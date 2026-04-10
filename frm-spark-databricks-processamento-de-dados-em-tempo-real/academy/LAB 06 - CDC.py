# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # Introdução
# MAGIC
# MAGIC Processamento de Change Data Capture
# MAGIC
# MAGIC <img src='https://raw.githubusercontent.com/douglas-engenheirodedados/streamingComApacheSpark-Databricks/main/cdc.png'>
# MAGIC
# MAGIC
# MAGIC ## Objetivos:
# MAGIC - Utilizar o [Databricks Labs Data Generator](https://databrickslabs.github.io/dbldatagen/public_docs/index.html) para gerar dados sintéticos para simular o processamento de Change Data Capture (CDC).
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC # Pré-Requisitos para o LAB:
# MAGIC
# MAGIC * Acesso a um **workspace** Databricks.
# MAGIC * Acesso a um **cluster**.
# MAGIC * Acesso a um **SQL Warehouse** (opcional).
# MAGIC * Acesso a um **catálogo** com as seguintes permissões:
# MAGIC     * `USE CATALOG`, `CREATE SCHEMA` e `CREATE TABLE` no catálogo

# COMMAND ----------

# MAGIC %md 
# MAGIC ## Change Data Capture

# COMMAND ----------

# MAGIC %pip install dbldatagen
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gerando uma base sintética

# COMMAND ----------

import dbldatagen as dg
import pyspark.sql.functions as F

spark.catalog.clearCache()
shuffle_partitions_requested = 8
partitions_requested = 32
data_rows = 10 * 1000 

spark.conf.set("spark.sql.shuffle.partitions", shuffle_partitions_requested)
spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
spark.conf.set("spark.sql.execution.arrow.maxRecordsPerBatch", 20000)

uniqueCustomers = 10 * 1000

dataspec = (
    dg.DataGenerator(spark, rows=data_rows, partitions=partitions_requested)
      .withColumn("customer_id","long", uniqueValues=uniqueCustomers)
      .withColumn("name", percentNulls=0.01, template=r'\\w \\w|\\w a. \\w')
      .withColumn("alias", percentNulls=0.01, template=r'\\w \\w|\\w a. \\w')
      .withColumn("payment_instrument_type", values=['paypal', 'Visa', 'Mastercard',
                  'American Express', 'discover', 'branded visa', 'branded mastercard'],
                  random=True, distribution="normal")
      .withColumn("int_payment_instrument", "int",  minValue=0000, maxValue=9999,
                  baseColumn="customer_id", baseColumnType="hash", omit=True)
      .withColumn("payment_instrument",
                  expr="format_number(int_payment_instrument, '**** ****** *####')",
                  baseColumn="int_payment_instrument")
      .withColumn("email", template=r'\\w.\\w@\\w.com|\\w-\\w@\\w')
      .withColumn("email2", template=r'\\w.\\w@\\w.com')
      .withColumn("ip_address", template=r'\\n.\\n.\\n.\\n')
      .withColumn("md5_payment_instrument",
                  expr="md5(concat(payment_instrument_type, ':', payment_instrument))",
                  base_column=['payment_instrument_type', 'payment_instrument'])
      .withColumn("customer_notes", text=dg.ILText(words=(1,8)))
      .withColumn("created_ts", "timestamp", expr="now()")
      .withColumn("modified_ts", "timestamp", expr="now()")
      .withColumn("memo", expr="'original data'")
      )
df1 = dataspec.build()

# write table

df1.write.format("delta").mode("overwrite").saveAsTable("bronze.cdc.customers1")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Executando o INSERT do primeiro DF

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from bronze.cdc.customers1
# MAGIC limit 5

# COMMAND ----------

# MAGIC %sql
# MAGIC select memo, count(*)
# MAGIC from bronze.cdc.customers1
# MAGIC group by memo

# COMMAND ----------

df_stream = spark.readStream.table("bronze.cdc.customers1")

# COMMAND ----------

df_stream.display()

# COMMAND ----------

sql_merge_query = """
MERGE INTO silver.cdc.lab_merge t
USING stream_update s
ON s.customer_id=t.customer_id
WHEN MATCHED THEN 
    UPDATE SET t.alias = s.alias, t.memo = 'updated on merge', t.modified_ts = now()
WHEN NOT MATCHED THEN 
    INSERT *
"""

# COMMAND ----------

class Upsert:
    def __init__(self, sql_merge_query, update_temp="stream_update"):
        self.sql_merge_query = sql_merge_query
        self.update_temp = update_temp 
        
    def upsert_to_delta(self, microBatchDF, batch):
        microBatchDF.createOrReplaceTempView(self.update_temp)
        microBatchDF._jdf.sparkSession().sql(self.sql_merge_query)

# COMMAND ----------

streaming_merge = Upsert(sql_merge_query)

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS silver.cdc.lab_merge
# MAGIC (customer_id LONG, name STRING, alias STRING, payment_instrument_type STRING, payment_instrument STRING, email STRING, email2 STRING, ip_address STRING, md5_payment_instrument STRING, customer_notes STRING, created_ts TIMESTAMP, modified_ts TIMESTAMP, memo STRING)

# COMMAND ----------

query = (df_stream.writeStream
                   .foreachBatch(streaming_merge.upsert_to_delta)
                   .outputMode("update")
                   .option("checkpointLocation", "/Volumes/silver/cdc/_checkpoints/lab_merge")
                   .trigger(availableNow=True)
                   .start())

query.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC select memo, count(*)
# MAGIC from silver.cdc.lab_merge
# MAGIC group by memo

# COMMAND ----------

# MAGIC %md
# MAGIC ## Criando alterações

# COMMAND ----------

start_of_new_ids = df1.select(F.max('customer_id')+1).collect()[0][0]

print(start_of_new_ids)

df1_inserts = (dataspec.clone()
        .option("startingId", start_of_new_ids)
        .withRowCount(10 * 1000)
        .build()
        .withColumn("memo", F.lit("insert"))
        .withColumn("customer_id", F.expr(f"customer_id + {start_of_new_ids}"))
              )

# read the written data - if we simply recompute, timestamps of original will be lost
df_original = spark.read.format("delta").table("bronze.cdc.customers1")

df1_updates = (df_original.sample(False, 0.1)
        .limit(50 * 1000)
        .withColumn("alias", F.lit('modified alias'))
        .withColumn("modified_ts",F.expr('now()'))
        .withColumn("memo", F.lit("update")))

df_changes = df1_inserts.union(df1_updates)

# randomize ordering
df_changes = (df_changes.withColumn("order_rand", F.expr("rand()"))
              .orderBy("order_rand")
              .drop("order_rand")
              )


display(df_changes)
df_changes.write.format("delta").mode("append").saveAsTable("bronze.cdc.customers1")

# COMMAND ----------

# MAGIC %sql
# MAGIC select memo, count(*)
# MAGIC from bronze.cdc.customers1
# MAGIC group by memo

# COMMAND ----------

# MAGIC %md
# MAGIC ## Executando o `MERGE`

# COMMAND ----------

df_stream_changes = spark.readStream.table("bronze.cdc.customers1")

# COMMAND ----------

query = (df_stream_changes.writeStream
                   .foreachBatch(streaming_merge.upsert_to_delta)
                   .outputMode("update")
                   .option("checkpointLocation", "/Volumes/silver/cdc/_checkpoints/lab_merge")
                   .trigger(availableNow=True)
                   .start())

query.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from silver.cdc.lab_merge

# COMMAND ----------

# MAGIC %sql
# MAGIC select memo, count(*)
# MAGIC from silver.cdc.lab_merge
# MAGIC group by memo

# COMMAND ----------

# MAGIC %md
# MAGIC ### Limpando o ambiente

# COMMAND ----------

spark.sql("DROP TABLE IF EXISTS bronze.cdc.customers1")
spark.sql("DROP TABLE IF EXISTS silver.cdc.lab_merge")

# Deleting all volumes used
dbutils.fs.rm("/Volumes/silver/cdc/_checkpoints/lab_merge", recurse=True)
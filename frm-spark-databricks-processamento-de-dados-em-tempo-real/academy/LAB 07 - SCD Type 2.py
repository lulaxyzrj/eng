# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # Introdução
# MAGIC
# MAGIC Processamento de SCD Type 2
# MAGIC
# MAGIC
# MAGIC
# MAGIC ## Objetivos:
# MAGIC - Utilizar o [Databricks Labs Data Generator](https://databrickslabs.github.io/dbldatagen/public_docs/index.html) para gerar dados sintéticos para simular o processamento de SCD Type 2.
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
# MAGIC ## Gerando uma base sintética

# COMMAND ----------

# MAGIC %pip install dbldatagen
# MAGIC %restart_python

# COMMAND ----------

import dbldatagen as dg
import pyspark.sql.functions as F

partitions_requested = 32
data_rows = 10 * 1000 

uniqueCustomers = 10 * 1000

# COMMAND ----------

dataspec = (
    dg.DataGenerator(spark, rows=data_rows, partitions=partitions_requested)
      .withColumn("customer_id","long", uniqueValues=uniqueCustomers)
      .withColumn("name", percentNulls=0.01, template=r'\\w \\w|\\w a. \\w')
      .withColumn("alias", percentNulls=0.01, template=r'\\w \\w|\\w a. \\w')
      .withColumn("payment_instrument_type", values=['paypal', 'Visa', 'Mastercard', 'American Express', 'discover', 'branded visa', 'branded mastercard'],               random=True, distribution="normal")
      .withColumn("int_payment_instrument", "int",  minValue=0000, maxValue=9999, baseColumn="customer_id", baseColumnType="hash", omit=True)
      .withColumn("payment_instrument", expr="format_number(int_payment_instrument, '**** ****** *####')", baseColumn="int_payment_instrument")
      .withColumn("email", template=r'\\w.\\w@\\w.com|\\w-\\w@\\w')
      .withColumn("email2", template=r'\\w.\\w@\\w.com')
      .withColumn("ip_address", template=r'\\n.\\n.\\n.\\n')
      .withColumn("md5_payment_instrument", expr="md5(concat(payment_instrument_type, ':', payment_instrument))", base_column=['payment_instrument_type', 'payment_instrument'])
      .withColumn("customer_notes", text=dg.ILText(words=(1,8)))
      .withColumn("created_ts", "timestamp", expr="now()")
      .withColumn("modified_ts", "timestamp", expr="now()")
      .withColumn("memo", expr="'original data'")
      )
df1 = dataspec.build()

# write table
df1.write.format("delta").mode("overwrite").saveAsTable("bronze.scd.customers1")

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from bronze.scd.customers1

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from bronze.scd.customers1
# MAGIC limit 10

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gravando o dataset na silver

# COMMAND ----------

sql_merge_query = """
MERGE INTO silver.scd.lab_scd AS t
USING (
  WITH stream_deduplicated AS (
    SELECT
      *,
      ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY modified_ts DESC) AS row_num
    FROM stream_update
  )
  SELECT * 
  FROM stream_deduplicated 
  WHERE row_num = 1
) AS s
ON t.customer_id = s.customer_id
   AND t.flag_ativo = 1

-- 1) Expira registro quando há alguma alteração null‑safe
WHEN MATCHED 
  AND (
    NOT (s.name                      <=> t.name) OR
    NOT (s.alias                     <=> t.alias) OR
    NOT (s.payment_instrument_type   <=> t.payment_instrument_type) OR
    NOT (s.payment_instrument        <=> t.payment_instrument) OR
    NOT (s.email                     <=> t.email) OR
    NOT (s.email2                    <=> t.email2) OR
    NOT (s.ip_address                <=> t.ip_address) OR
    NOT (s.md5_payment_instrument    <=> t.md5_payment_instrument) OR
    NOT (s.customer_notes            <=> t.customer_notes)
  )
THEN UPDATE SET
  data_fim     = current_timestamp(),
  flag_ativo   = 0,
  memo         = 'Registro expirado devido a atualização',
  modified_ts  = current_timestamp()

-- 2) Insere linha nova sempre que NÃO existir um registro ativo equivalente
WHEN NOT MATCHED BY TARGET
THEN INSERT (
    customer_id,
    name,
    alias,
    payment_instrument_type,
    payment_instrument,
    email,
    email2,
    ip_address,
    md5_payment_instrument,
    customer_notes,
    created_ts,
    modified_ts,
    memo,
    data_inicio,
    data_fim,
    flag_ativo
  )
  VALUES (
    s.customer_id,
    s.name,
    s.alias,
    s.payment_instrument_type,
    s.payment_instrument,
    s.email,
    s.email2,
    s.ip_address,
    s.md5_payment_instrument,
    s.customer_notes,
    s.created_ts,           -- data original de criação
    current_timestamp(),    -- marca inserção no DWH
    'Novo registro inserido',
    current_timestamp(),    -- data de início da nova versão
    NULL,                   -- sem data de fim
    1                       -- ativo
  );

"""

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### Explicação das mudanças
# MAGIC ✅ Manutenção de histórico: O registro antigo é marcado como inativo (flag_ativo = 0 e data_fim = current_timestamp()).
# MAGIC
# MAGIC ✅ Verificação de mudanças: A atualização ocorre apenas se houver diferenças entre os valores antigos e novos.
# MAGIC
# MAGIC ✅ Novo registro com os dados completos: Quando há uma alteração, uma nova linha com todas as colunas é adicionada.
# MAGIC
# MAGIC ✅ Campos de controle:
# MAGIC
# MAGIC - data_inicio: Define quando o registro começou a valer.
# MAGIC - data_fim: Define até quando ele foi válido (caso tenha sido atualizado).
# MAGIC - flag_ativo: Define se o registro está ativo (1) ou expirado (0).
# MAGIC - memo: Adiciona informações sobre a atualização.

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
# MAGIC CREATE TABLE IF NOT EXISTS silver.scd.lab_scd (
# MAGIC     customer_id LONG, 
# MAGIC     name STRING, 
# MAGIC     alias STRING, 
# MAGIC     payment_instrument_type STRING, 
# MAGIC     payment_instrument STRING, 
# MAGIC     email STRING, 
# MAGIC     email2 STRING, 
# MAGIC     ip_address STRING, 
# MAGIC     md5_payment_instrument STRING, 
# MAGIC     customer_notes STRING, 
# MAGIC     created_ts TIMESTAMP, 
# MAGIC     modified_ts TIMESTAMP, 
# MAGIC     memo STRING,
# MAGIC     data_inicio TIMESTAMP,  -- Data de início da validade do registro
# MAGIC     data_fim TIMESTAMP,     -- Data de fim da validade do registro (NULL significa ativo)
# MAGIC     flag_ativo INT          -- 1 para ativo, 0 para expirado
# MAGIC )

# COMMAND ----------

df_stream = spark.readStream.table("bronze.scd.customers1")

# COMMAND ----------

query = (df_stream.writeStream
                   .foreachBatch(streaming_merge.upsert_to_delta)
                   .outputMode("update")
                   .option("checkpointLocation", "/Volumes/silver/scd/_checkpoints/lab_scd")
                   .trigger(availableNow=True)
                   .start())

query.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC select memo, count(*)
# MAGIC from silver.scd.lab_scd
# MAGIC group by memo

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from silver.scd.lab_scd
# MAGIC limit 10

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
df_changes.write.format("delta").mode("append").saveAsTable("bronze.scd.customers1")

# COMMAND ----------

# MAGIC %sql
# MAGIC select memo, count(*)
# MAGIC from bronze.cdc.customers1
# MAGIC group by memo

# COMMAND ----------

# MAGIC %md
# MAGIC ## Executando o `MERGE`

# COMMAND ----------

df_stream_changes = spark.readStream.table("bronze.scd.customers1")

# COMMAND ----------

query = (df_stream_changes.writeStream
                   .foreachBatch(streaming_merge.upsert_to_delta)
                   .outputMode("update")
                   .option("checkpointLocation", "/Volumes/silver/scd/_checkpoints/lab_scd/")
                   .trigger(availableNow=True)
                   .start())

query.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from silver.scd.lab_scd
# MAGIC limit 10

# COMMAND ----------

# MAGIC %sql
# MAGIC select memo, count(*)
# MAGIC from silver.scd.lab_scd
# MAGIC group by memo

# COMMAND ----------

# MAGIC %md
# MAGIC ### Limpando o ambiente

# COMMAND ----------

# Drop the bronze table
spark.sql("DROP TABLE IF EXISTS bronze.scd.customers1")

# Drop the silver table
spark.sql("DROP TABLE IF EXISTS silver.scd.lab_scd")

# Remove the checkpoint directory
dbutils.fs.rm("/Volumes/silver/scd/_checkpoints/lab_scd/", recurse=True)
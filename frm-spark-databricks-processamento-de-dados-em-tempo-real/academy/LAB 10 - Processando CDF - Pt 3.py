# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # Processando Registros do Change Data Feed (CDF) do Delta Lake
# MAGIC
# MAGIC Neste notebook, vamos demonstrar um fluxo de como você pode facilmente propagar mudanças por um Lakehouse usando o Change Data Feed (CDF) do Delta Lake.
# MAGIC
# MAGIC ## Objetivos de Aprendizagem  
# MAGIC Ao final desta lição, você será capaz de:  
# MAGIC 1. Habilitar o Change Data Feed em um cluster ou em uma tabela específica  
# MAGIC 2. Descrever como as mudanças são registradas  
# MAGIC 3. Ler a saída do CDF com Spark SQL ou PySpark  usando API Streaming

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, IntegerType, StringType,TimestampType

# COMMAND ----------

# Habilita o CDF para todas as tabelas novas na Spark Session
# spark.sql("set spark.databricks.delta.properties.defaults.enableChangeDataFeed = true;")

# COMMAND ----------

# Criar schema
schema = StructType([
    StructField("id_cliente", IntegerType(), False),
    StructField("nome_cliente", StringType(), True),
    StructField("estado_cliente", StringType(), True)
])

# Criar DataFrame vazio
df_vazio = spark.createDataFrame([], schema)

df_vazio.write.format("delta") \
    .mode("append") \
    .option("delta.enableChangeDataFeed", "true") \
    .saveAsTable("sandbox.demo.cdf_stream")

# COMMAND ----------

# Ver versões disponíveis da tabela
spark.sql(f"DESCRIBE HISTORY sandbox.demo.cdf_stream").display()

# COMMAND ----------

df = (spark.readStream.format("delta") 
    .option("readChangeData", "true") 
    .table("sandbox.demo.cdf_stream") 
)
df.display()

# COMMAND ----------

dados_iniciais = [
    (1, "Ana", "SP"),
    (2, "Bruno", "RJ"),
    (3, "Carla", "MG")
]

df_iniciais = spark.createDataFrame(dados_iniciais, schema)

df_iniciais.write.format("delta") \
    .mode("append") \
    .saveAsTable("sandbox.demo.cdf_stream")

# COMMAND ----------

# Ver versões disponíveis da tabela
spark.sql(f"DESCRIBE HISTORY sandbox.demo.cdf_stream").display()

# COMMAND ----------

novos_dados = [
    (4, "Daniel", "BA"),
    (5, "Eduarda", "RS"),
    (6, "Felipe", "PR")
]

df_novos = spark.createDataFrame(novos_dados, schema)

df_novos.write.format("delta") \
    .mode("append") \
    .saveAsTable("sandbox.demo.cdf_stream")

# COMMAND ----------

spark.sql("""
    UPDATE sandbox.demo.cdf_stream
    SET nome_cliente = CONCAT('UPD_', nome_cliente)
    WHERE id_cliente IN (2, 5)
""")

# COMMAND ----------

spark.sql("""
         DELETE FROM sandbox.demo.cdf_stream
         WHERE id_cliente = 3
""")

# COMMAND ----------

# Ver versões disponíveis da tabela
spark.sql(f"DESCRIBE HISTORY sandbox.demo.cdf_stream").display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## batch

# COMMAND ----------

df = (spark.read.format("delta") 
    .option("readChangeData", "true") 
    .option("startingVersion",4)
    .table("sandbox.demo.cdf_stream")
)
df.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## streaming

# COMMAND ----------

df = (spark.readStream.format("delta") 
    .option("readChangeData", "true") 
    .option("startingVersion",0)
    .table("sandbox.demo.cdf_stream")
)
df.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## streaming sem startVersion ou startTimestamp

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from sandbox.demo.cdf_stream

# COMMAND ----------

df = (spark.readStream.format("delta") 
    .option("readChangeData", "true") 
    .table("sandbox.demo.cdf_stream")
)
df.display()

# COMMAND ----------

novos_dados = [
    (7, "Davi", "BA"),
    (8, "Eduardo", "RS"),
    (9, "Fernanda", "PR")
]

df_novos = spark.createDataFrame(novos_dados, schema)

df_novos.write.format("delta") \
    .mode("append") \
    .saveAsTable("sandbox.demo.cdf_stream")

# COMMAND ----------

spark.sql("""
         DELETE FROM sandbox.demo.cdf_stream
         WHERE id_cliente = 8
""")

# COMMAND ----------

spark.sql("""
    UPDATE sandbox.demo.cdf_stream
    SET nome_cliente = CONCAT('UPD_', nome_cliente)
    WHERE id_cliente IN (7, 9)
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Persistindo e controlando com o checkpoint

# COMMAND ----------

df = (spark.readStream.format("delta")
    .option("readChangeData", "true")
    .table("sandbox.demo.cdf_stream")
    .writeStream
    .format("delta")
    .option("checkpointLocation", "/Volumes/sandbox/demo/cdf/checkpoint/cdf_processed")
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .table("sandbox.demo.cdf_processed")
)
df.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from sandbox.demo.cdf_processed
# MAGIC order by _commit_timestamp

# COMMAND ----------

spark.sql("""
         DELETE FROM sandbox.demo.cdf_stream
         WHERE id_cliente = 1
""")

# COMMAND ----------

spark.sql("""
    UPDATE sandbox.demo.cdf_stream
    SET nome_cliente = CONCAT('UPD_', nome_cliente)
    WHERE id_cliente IN (4)
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## alter table

# COMMAND ----------

# MAGIC %sql
# MAGIC desc detail sandbox.demo.cdf_processed 

# COMMAND ----------

# MAGIC %sql
# MAGIC alter table sandbox.demo.cdf_processed SET TBLPROPERTIES (delta.enableChangeDataFeed = true)

# COMMAND ----------

# MAGIC %sql
# MAGIC drop table sandbox.demo.cdf_processed;

# COMMAND ----------

dbutils.fs.rm("/Volumes/sandbox/demo/cdf/checkpoint/", recurse=True)

# COMMAND ----------

df = (spark.readStream.format("delta")
    .option("readChangeData", "true")
    .table("sandbox.demo.cdf_stream").selectExpr("id_cliente", "nome_cliente", "estado_cliente", "_change_type as operation")
    .writeStream
    .format("delta")
    .option("checkpointLocation", "/Volumes/sandbox/demo/cdf/checkpoint/cdf_processed")
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .table("sandbox.demo.cdf_processed")
)
df.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC desc history sandbox.demo.cdf_processed 

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM table_changes('sandbox.demo.cdf_processed', 2)
# MAGIC -- where operation = "update_postimage"

# COMMAND ----------

# MAGIC %sql
# MAGIC desc detail sandbox.demo.cdf_processed 

# COMMAND ----------

novos_dados = [
    (10, "Daniela", "BA"),
    (11, "Antonio", "RS"),
    (12, "Fernando", "PR")
]

df_novos = spark.createDataFrame(novos_dados, schema)

df_novos.write.format("delta") \
    .mode("append") \
    .saveAsTable("sandbox.demo.cdf_stream")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM sandbox.demo.cdf_processed

# COMMAND ----------

# MAGIC %md
# MAGIC ## Limpando o Ambiente

# COMMAND ----------

# MAGIC %sql
# MAGIC drop table sandbox.demo.cdf_stream;
# MAGIC drop table sandbox.demo.cdf_processed;

# COMMAND ----------

dbutils.fs.rm("/Volumes/sandbox/demo/cdf/checkpoint/", recurse=True)
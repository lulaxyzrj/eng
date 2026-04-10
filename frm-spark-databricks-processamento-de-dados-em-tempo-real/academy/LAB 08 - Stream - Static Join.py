# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # Introdução
# MAGIC
# MAGIC Stream - Static Join
# MAGIC
# MAGIC <img src='https://raw.githubusercontent.com/douglas-engenheirodedados/streamingComApacheSpark-Databricks/main/streamStaticJoin.png'>
# MAGIC
# MAGIC
# MAGIC ## Objetivos:
# MAGIC - Utilizar o [Databricks Labs Data Generator](https://databrickslabs.github.io/dbldatagen/public_docs/index.html) para gerar dados sintéticos para simular Join entre tabelas Stream e estáticas.
# MAGIC - Realizer o join entre um entre uma tabelas estática e uma tabela stream

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
from pyspark.sql.types import IntegerType, StringType, LongType, FloatType, TimestampType
from datetime import datetime, timedelta
from pyspark.sql.functions import expr

# COMMAND ----------

# MAGIC %md
# MAGIC Geração do dataset estático de clientes: Este dataset conterá informações dos clientes e será utilizado para enriquecer os eventos de compras.

# COMMAND ----------

# Especificação dos dados dos clientes
client_data_spec = (
    dg.DataGenerator(spark, name="client_data", rows=1000, partitions=1)
    .withColumn("client_id", IntegerType(), minValue=1, maxValue=1000)
    .withColumn("client_name", StringType(), values=['Alice', 'Bob', 'Charlie', 'David', 'Eva'], random=True)
    .withColumn("client_email", StringType(), prefix="client", suffix="@example.com", random=True)
)

# Geração do DataFrame de clientes
client_df = client_data_spec.build()

# Escrita do DataFrame em uma tabela Delta
client_df.write.format("delta").mode("overwrite").saveAsTable("silver.demo.clientes")


# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from silver.demo.clientes
# MAGIC limit 10

# COMMAND ----------

# MAGIC %md
# MAGIC Geração do dataset de eventos de compras em streaming: Este dataset simulará um fluxo contínuo de eventos de compras.

# COMMAND ----------

# Especificação dos dados de compras
purchase_data_spec = (
    dg.DataGenerator(spark, name="purchase_data", rows=100000, partitions=1)
    .withColumn("purchase_id", LongType(), minValue=1, maxValue=1000000)
    .withColumn("client_id", IntegerType(), minValue=1, maxValue=1000)
    .withColumn("amount", FloatType(), minValue=10.0, maxValue=1000.0, random=True)
    .withColumn("purchase_time", TimestampType(), begin=datetime(2025, 1, 1), end=datetime(2025, 4, 21), interval=timedelta(minutes=1), random=True)
)

# Geração do DataFrame de compras em streaming
purchase_stream_df = purchase_data_spec.build(withStreaming=True, options={'rowsPerSecond': 10})

# Escrita do DataFrame de compras em uma tabela Delta em modo de streaming
purchase_query = (
    purchase_stream_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/Volumes/silver/demo/_checkpoints/compras")
    .table("silver.demo.compras")
)

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from silver.demo.compras

# COMMAND ----------

# Leitura do fluxo de compras
compras_df = spark.readStream.table("silver.demo.compras")

# Leitura da tabela estática de clientes
clientes_df = spark.read.table("silver.demo.clientes")

# Realização do join
enriched_purchases_df = compras_df.join(clientes_df, "client_id")

# Escrita do resultado do join em uma tabela Delta
enriched_query = (
    enriched_purchases_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/Volumes/gold/demo/_checkpoints/compras_enriquecidas")
    .table("gold.demo.compras_enriquecidas")
)


# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from gold.demo.compras_enriquecidas

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from gold.demo.compras_enriquecidas
# MAGIC limit 5

# COMMAND ----------

# MAGIC %md
# MAGIC ### Limpando o ambiente

# COMMAND ----------

# Dropando as tabelas utilizadas
spark.sql("DROP TABLE IF EXISTS silver.demo.clientes")
spark.sql("DROP TABLE IF EXISTS silver.demo.compras")
spark.sql("DROP TABLE IF EXISTS gold.demo.compras_enriquecidas")

# Dropando o checkpoint
dbutils.fs.rm("/Volumes/silver/demo/_checkpoints/compras", recurse=True)
dbutils.fs.rm("/Volumes/gold/demo/_checkpoints/compras_enriquecidas", recurse=True)
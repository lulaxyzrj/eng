# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # Introdução
# MAGIC
# MAGIC Este notebook é destinado ao estudo do Auto Loader.
# MAGIC
# MAGIC
# MAGIC <img src='https://raw.githubusercontent.com/douglas-engenheirodedados/streamingComApacheSpark-Databricks/main/Screenshot from 2025-01-21 19-17-40.png'>
# MAGIC
# MAGIC ## Neste notebook iremos:
# MAGIC
# MAGIC 1. Ler uma origem usando o Auto Loader

# COMMAND ----------

# MAGIC %md
# MAGIC # Pré-Requisitos para o LAB 3:
# MAGIC
# MAGIC * Acesso a um **workspace** Databricks.
# MAGIC * Acesso a um **SQL Warehouse** (Opcional).
# MAGIC * Acesso a um **cluster**.
# MAGIC * Acesso a um **catálogo** com as seguintes permissões:
# MAGIC     * `USE CATALOG`, `CREATE SCHEMA` e `CREATE TABLE` no catálogo

# COMMAND ----------

# MAGIC %md 
# MAGIC ## Auto Loader

# COMMAND ----------

"""
Variáveis de configuração para leitura de dados do Kafka:

- topic_pattern: Padrão de tópicos Kafka a serem assinados.
"""
topic_pattern = "gcn.classic.text.*"

# COMMAND ----------

catalog = "bronze"
schema = "gcn"
table = "multiplex_autoloader"
volume_checkpoint = "_checkpoints"
volume_schema = "_schema"
full_table_name = f"{catalog}.{schema}.{table}"
print("Nome completo da tabela :",full_table_name)

checkpoint_path = f"/Volumes/{catalog}/{schema}/{volume_checkpoint}/{table}"
schema_path = f"/Volumes/{catalog}/{schema}/{volume_schema}/{table}"
print("Caminho do checkpoint: ", checkpoint_path)
print("Caminho do schema:     ", schema_path)

# COMMAND ----------

import pyspark.sql.functions as F

def autoloader_to_bronze_multiplex():

    query = (spark
            # Configurando a origem do stream
             .readStream
                .format("cloudfiles")
                .option("cloudFiles.format", "json") 
                .option("subscribePattern", topic_pattern)  
                .option("cloudFiles.schemaLocation", schema_path)  # Specify schema location
                .load("/Volumes/landing/gcn/gcn/arquivos/") # Specify source directory
                .withColumn("ingestion_timestamp", F.current_timestamp())
                .withColumn("sistema_origem", F.lit("gcn.classic.text_autoloader"))
            # Gravando no destino
            .writeStream
                .format("delta")
                .option("checkpointLocation", checkpoint_path)
                .option("mergeSchema", True)
                .trigger(availableNow=True) # Executa o processo em batch
                .table(full_table_name)
    )
    query.awaitTermination()

# COMMAND ----------

autoloader_to_bronze_multiplex()

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from bronze.gcn.multiplex_autoloader
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
# MAGIC 1. Entender o funcionamento do Schema Inference, Evolution e Enforcement
# MAGIC 2. Ver na prática o funcionamento de cada uma das features.

# COMMAND ----------

# MAGIC %md
# MAGIC # Pré-Requisitos para o LAB 4:
# MAGIC
# MAGIC * Acesso a um **workspace** Databricks.
# MAGIC * Acesso a um **SQL Warehouse** (Opcional).
# MAGIC * Acesso a um **cluster**.
# MAGIC * Acesso a um **catálogo** com as seguintes permissões:
# MAGIC     * `USE CATALOG`, `CREATE SCHEMA` e `CREATE TABLE` no catálogo

# COMMAND ----------

# MAGIC %md 
# MAGIC ## Schema Inference & evolution

# COMMAND ----------

"""
Variáveis de configuração para leitura de dados do Kafka:

- topic_pattern: Padrão de tópicos Kafka a serem assinados.
"""
topic_pattern = "gcn.classic.text.*"

# COMMAND ----------

catalog = "bronze"
schema = "gcn"
table = "multiplex_autoloader_schema"
volume_checkpoint = "_checkpoints"
volume_schema = "_schema"
full_table_name = f"{catalog}.{schema}.{table}"
print("Nome completo da tabela :",full_table_name)

checkpoint_path = f"/Volumes/{catalog}/{schema}/{volume_checkpoint}/{table}"
schema_path = f"/Volumes/{catalog}/{schema}/{volume_schema}/{table}"
print("Caminho do checkpoint: ", checkpoint_path)
print("Caminho do schema: ", schema_path)

# COMMAND ----------

import pyspark.sql.functions as F

def autoloader_schema_inference_anf_evolution():

    query = (spark
            # Configurando a origem do stream
             .readStream
                .format("cloudfiles")
                .option("cloudFiles.format", "json") 
                .option("subscribePattern", topic_pattern)  
                .option("cloudFiles.schemaLocation", schema_path)  # Specify schema location
                # .option("cloudFiles.schemaEvolutionMode", "rescue") # Enable schema evolution
                # .option("rescuedDataColumn", "_rescued_data") # Specify rescued data column
                .load("/Volumes/landing/gcn/gcn/arquivos")
                .withColumn("ingestion_timestamp", F.current_timestamp())
                .withColumn("sistema_origem", F.lit("gcn.classic.text"))
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

autoloader_schema_inference_anf_evolution()

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from bronze.gcn.multiplex_autoloader_schema

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from bronze.gcn.multiplex_autoloader_schema
# MAGIC where `_rescued_data` is not null

# COMMAND ----------

# MAGIC %md
# MAGIC ## Schema Enforcement

# COMMAND ----------

import pyspark.sql.functions as F

def autoloader_schema_enforcement():

    schema = "offset STRING, timestamp STRING, topic STRING, value STRING, ingestion_timestamp TIMESTAMP, sistema_origem STRING,ingestion_blob_time TIMESTAMP"

    query = (spark
            # Configurando a origem do stream
             .readStream
                .format("cloudfiles")
                .option("cloudFiles.format", "json") 
                .option("subscribePattern", topic_pattern)  
                .schema(schema)  # Define o schema
                .load("/Volumes/landing/gcn/gcn/arquivos")
                .withColumn("ingestion_timestamp", F.current_timestamp())
                .withColumn("sistema_origem", F.lit("gcn.classic.text"))
            # Gravando no destino
            .writeStream
                .format("delta")
                .option("checkpointLocation", f"{checkpoint_path}_enforcement")
                .option("mergeSchema", True)
                .trigger(availableNow=True) # Executa o processo em batch
                .table("bronze.gcn.multiplex_autoloader_schema_enforcement")
    )
    query.awaitTermination()

# COMMAND ----------

autoloader_schema_enforcement()

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from bronze.gcn.multiplex_autoloader_schema_enforcement

# COMMAND ----------

# MAGIC %sql
# MAGIC select date_format(ingestion_blob_time, 'yyyy-MM-dd') as ingestion_date, count(1)
# MAGIC from bronze.gcn.multiplex_autoloader_schema_enforcement
# MAGIC group by date_format(ingestion_blob_time, 'yyyy-MM-dd')
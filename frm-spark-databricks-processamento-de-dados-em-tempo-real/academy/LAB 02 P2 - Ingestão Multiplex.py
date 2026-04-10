# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # Introdução
# MAGIC
# MAGIC Este notebook é destinado ao estudo dos padrões de ingestão singleplex e multiplex no contexto do Apache Spark Structured Streaming.
# MAGIC
# MAGIC
# MAGIC <img src='https://raw.githubusercontent.com/douglas-engenheirodedados/streamingComApacheSpark-Databricks/main/ingestaoSingleplexMultiplex.png'>
# MAGIC
# MAGIC ## Neste notebook iremos:
# MAGIC
# MAGIC 1. Ler uma origem Kafka e gravar n:1
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC # Pré-Requisitos para o LAB 2:
# MAGIC
# MAGIC * Acesso a um **workspace** Databricks.
# MAGIC * Acesso a um **SQL Warehouse** (Opcional).
# MAGIC * Acesso a um **cluster**.
# MAGIC * Acesso a um **catálogo** com as seguintes permissões:
# MAGIC     * `USE CATALOG`, `CREATE SCHEMA` e `CREATE TABLE` no catálogo

# COMMAND ----------

# MAGIC %md 
# MAGIC ## Multiplex

# COMMAND ----------

"""
Variáveis de configuração para leitura de dados do Kafka:

- topic_pattern: Padrão de tópicos Kafka a serem assinados.
"""
topic_pattern = "gcn.classic.text.*"

# COMMAND ----------

# Esse é um ambiente de estudos, utilize secrets de forma segura.
# TODO: Preencher com os valores obtidos no site do GCN
client_id = ""
client_secret = ""
bootstrap_servers = 'kafka.gcn.nasa.gov:9092'
token_endpoint_url = 'https://auth.gcn.nasa.gov/oauth2/token'

jaas_config = f'kafkashaded.org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required \
                clientId="{client_id}" \
                clientSecret="{client_secret}" ;'

kafka_config = {
    'kafka.bootstrap.servers': bootstrap_servers,
    'kafka.security.protocol': 'SASL_SSL',
    'kafka.sasl.mechanism': 'OAUTHBEARER',
    'kafka.sasl.oauthbearer.token.endpoint.url': token_endpoint_url,
    'kafka.sasl.jaas.config': jaas_config,
    'kafka.sasl.login.callback.handler.class': 'kafkashaded.org.apache.kafka.common.security.oauthbearer.secured.OAuthBearerLoginCallbackHandler',
    'startingOffsets': 'earliest' # Se quiser receber os dados retidos.
}

# COMMAND ----------

catalog = "bronze"
schema = "gcn"
table = "multiplex"
volume = "_checkpoints"
full_table_name = f"{catalog}.{schema}.{table}"
print("Nome completo da tabela :",full_table_name)

checkpoint_path = f"/Volumes/{catalog}/{schema}/{volume}/{table}"
print("Caminho do checkpoint: ", checkpoint_path)

# COMMAND ----------

import pyspark.sql.functions as F

def kafka_to_bronze_multiplex():
    """
    Função para ler dados de um tópico Kafka e gravar em uma tabela Delta.

    - Lê dados do stream Kafka configurado.
    - Adiciona colunas de timestamp de ingestão e sistema de origem.
    - Grava os dados em uma tabela Delta no modo append em batch.
    - Utiliza um checkpoint para garantir a tolerância a falhas.
    """
    query = (spark
            # Configurando a origem do stream
             .readStream
                .format("kafka") 
                .options(**kafka_config) 
                .option("subscribePattern", topic_pattern)  
                .load()
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

kafka_to_bronze_multiplex()

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from bronze.gcn.multiplex

# COMMAND ----------

# MAGIC %sql
# MAGIC select min(timestamp), max(timestamp)
# MAGIC from bronze.gcn.multiplex

# COMMAND ----------

# MAGIC %sql
# MAGIC select distinct topic
# MAGIC from bronze.gcn.multiplex

# COMMAND ----------

# MAGIC %sql
# MAGIC select cast(value as string), *
# MAGIC from bronze.gcn.multiplex
# MAGIC order by timestamp desc
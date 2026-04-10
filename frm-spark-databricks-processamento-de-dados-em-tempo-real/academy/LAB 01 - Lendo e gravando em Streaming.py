# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC <img src ='https://raw.githubusercontent.com/douglas-engenheirodedados/streamingComApacheSpark-Databricks/main/queryngKafka.png'>
# MAGIC
# MAGIC Conceitos centrais:
# MAGIC - Origem de entrada
# MAGIC - Transformações
# MAGIC - Trigger
# MAGIC - Destinos
# MAGIC
# MAGIC ## Nesta aula iremos:
# MAGIC 1. Comparar API Batch X Streaming
# MAGIC 1. Construir um DataFrame streaming
# MAGIC 2. Mostrar na tela o resultado de uma consulta streaming
# MAGIC 3. Gravar o resultado da consulta 
# MAGIC
# MAGIC
# MAGIC **Aviso:** 
# MAGIC Notebook com caracter apenas de estudos.

# COMMAND ----------

# MAGIC %md
# MAGIC # Pré-Requisitos para o LAB 1:
# MAGIC
# MAGIC * Acesso a um **workspace** Databricks.
# MAGIC * Acesso a um **SQL Warehouse**.
# MAGIC * Acesso a um **cluster**.
# MAGIC * Acesso a um **catálogo** com as seguintes permissões:
# MAGIC     * `USE CATALOG`, `CREATE SCHEMA` e `CREATE TABLE` no catálogo
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configurando nossa origem
# MAGIC
# MAGIC https://gcn.nasa.gov/

# COMMAND ----------

# ATENÇÃO: Os valores de client_id e client_secret estão hardcoded apenas para fins de estudo.
# Em um ambiente de produção, é altamente recomendável utilizar um gerenciador de secrets seguro,
# como o Azure Key Vault, AWS Secrets Manager ou Databricks Secrets, para proteger informações sensíveis.

# TODO: Preencher com os valores obtidos no site do GCN
client_id = ""
client_secret = ""

jaas_config =   f'kafkashaded.org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required \
                clientId="{client_id}" \
                clientSecret="{client_secret}" ;'

kafka_config = {
    'kafka.bootstrap.servers': 'kafka.gcn.nasa.gov:9092',
    'kafka.security.protocol': 'SASL_SSL',
    'kafka.sasl.mechanism': 'OAUTHBEARER',
    'kafka.sasl.oauthbearer.token.endpoint.url': 'https://auth.gcn.nasa.gov/oauth2/token',
    'kafka.sasl.jaas.config': jaas_config,
    'kafka.sasl.login.callback.handler.class': 'kafkashaded.org.apache.kafka.common.security.oauthbearer.secured.OAuthBearerLoginCallbackHandler',
    # 'startingOffsets': 'earliest' # Se quiser receber os dados retidos.
}

topic = "gcn.heartbeat"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Batch

# COMMAND ----------

# Lendo dados do Kafka
# ATENÇÃO: A leitura do Kafka usando a API de batch é apenas para fins didáticos e ilustrativos.
# Em um ambiente de produção, recomenda-se utilizar a API de streaming para processar dados em tempo real.

df = (
    spark 
    .read
    .format("kafka") 
    .options(**kafka_config) 
    .option("subscribe", topic) 
    .load() 
)

# Validando se o DataFrame é streaming
print("DataFrame Streaming: ", df.isStreaming)

# COMMAND ----------

df.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stream

# COMMAND ----------

# Criação de um DataFrame de streaming conectado ao Kafka
df_stream = (                           # Inicia a definição do DataFrame de streaming
    spark                               # Referência à sessão Spark ativa
    #TODO: Preencher com a chamada do método de leitura de streaming
    .                         # Método que indica leitura em streaming (contínua)
    .format("kafka")                    # Define o Apache Kafka como fonte de dados
    .options(**kafka_config)            # Aplica configurações de conexão ao Kafka (ex: servidor, credenciais)
    .option("subscribe", topic)         # Define qual tópico Kafka será consumido
    .load()                             # Executa a operação de leitura e cria o DataFrame
)

# Validação do DataFrame
print("DataFrame Streaming: ", df_stream.isStreaming)  # Verifica se é realmente um DataFrame de streaming
                                                      # Retorna True se for streaming, False caso contrário

# COMMAND ----------

df_stream.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gravando no destino

# COMMAND ----------

catalog = "sandbox"
schema = "ft_ss"
volume = "checkpoints"
table_name = "gcn_heartbeat"
full_table_name = f"{catalog}.{schema}.{table_name}"
#TODO : Preencher com o URL
url_external_location = ""
print(f"Nome completa do tabela: {full_table_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC #### Criando o catalogo

# COMMAND ----------

spark.sql(f"create catalog if not exists {catalog} managed location '{url_external_location}'")

# COMMAND ----------

# MAGIC %md
# MAGIC #### Criando schema e volume

# COMMAND ----------

spark.sql(f"create schema if not exists {catalog}.{schema}")
spark.sql(f"create volume if not exists {catalog}.{schema}.{volume}")

# COMMAND ----------

checkpoint_path = f"/Volumes/sandbox/ft_ss/checkpoints/{topic}"
print(f"Checkpoint path: {checkpoint_path}")
# Checkpoint é um mecanismo no Structured Streaming que permite a tolerância a falhas.
# Ele armazena informações de progresso e metadados do stream para que, em caso de falha,
# o processamento possa ser retomado do ponto de interrupção, garantindo a consistência dos dados.

# COMMAND ----------

import pyspark.sql.functions as F

def process_kafka():
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
                .option("subscribe", topic) 
                .load()
                .withColumn("ingestion_timestamp", F.current_timestamp())
                .withColumn("sistema_origem", F.lit("gcn"))
            # Gravando no destino
            #TODO: Preencher com a chamada do método de gravação do destino
            .
                .format("delta")
                .option("checkpointLocation", checkpoint_path)
                .outputMode("append") # APPEND (DEFAULT), UPDATE, COMPLETE
                .trigger(availableNow=True) # Executa o processo em batch
                .table(f"{full_table_name}")
    )
    query.awaitTermination()

# COMMAND ----------

process_kafka()
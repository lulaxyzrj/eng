# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # Introdução
# MAGIC
# MAGIC Stream - Stream Join
# MAGIC
# MAGIC <img src='https://raw.githubusercontent.com/douglas-engenheirodedados/streamingComApacheSpark-Databricks/main/streamStreamJoin.png'>
# MAGIC
# MAGIC
# MAGIC ## Objetivos:
# MAGIC - Utilizar o [Databricks Labs Data Generator](https://databrickslabs.github.io/dbldatagen/public_docs/index.html) para gerar dados sintéticos para simular Join entre tabelas Stream e Stream.
# MAGIC - Realizer o join entre tabelas Streaming

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

# DBTITLE 1,Importação das bibliotecas
from pyspark.sql.types import IntegerType, StringType, TimestampType
import dbldatagen as dg
from datetime import datetime, timedelta
from pyspark.sql.functions import expr

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC Passo 1: Gerar dados de impressões e cliques
# MAGIC
# MAGIC Utilizando a dbldatagen, podemos criar dois DataFrames de streaming: um para impressões de anúncios e outro para cliques em anúncios.

# COMMAND ----------

# Definir o intervalo de geração de timestamps sintéticos
current_time = datetime.now()
start_time = current_time - timedelta(hours=2)  # últimos 2h apenas

# Configuração do dataset de Impressões
impressions_spec = (
        dg.DataGenerator(spark, name="impressions", rows=100000, partitions=4)
        .withIdOutput()
        .withColumn("impressionAdId", IntegerType(), minValue=1, maxValue=100)
        .withColumn("impressionTime", TimestampType(),
                    begin=start_time, end=current_time,
                    interval=timedelta(seconds=30), random=True)
        .withColumn("userId", IntegerType(), minValue=1, maxValue=1000)
    )

# Configuração do dataset de Cliques
clicks_spec = (
        dg.DataGenerator(spark, name="clicks", rows=50000, partitions=4)
        .withIdOutput()
        .withColumn("clickAdId", IntegerType(), minValue=1, maxValue=100)
        .withColumn("clickTime", TimestampType(),
                    begin=start_time, end=current_time,
                    interval=timedelta(seconds=30), random=True)
        .withColumn("userId", IntegerType(), minValue=1, maxValue=1000)
    )

# Gerar dados como streaming (modo simulado)
impressions_stream = impressions_spec.build(withStreaming=True, options={'rowsPerSecond': 10})
clicks_stream = clicks_spec.build(withStreaming=True, options={'rowsPerSecond': 10})

# COMMAND ----------

# Visualizar schemas para fins didáticos
print("Schema de Impressões:")
impressions_stream.printSchema()

# COMMAND ----------

print("Schema de Cliques:")
clicks_stream.printSchema()

# COMMAND ----------

impressions_stream.display()

# COMMAND ----------

clicks_stream.display()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC Passo 2: Aplicar watermarks nas colunas de tempo do evento
# MAGIC
# MAGIC Para gerenciar o estado e a latência no processamento de streams, aplicamos marcas d'água (watermarks) nas colunas de tempo dos eventos. Isso permite descartar estados antigos que não serão mais necessários, otimizando o uso de recursos.

# COMMAND ----------

impressions_with_watermark = impressions_stream.withWatermark("impressionTime", "1 hour")
clicks_with_watermark = clicks_stream.withWatermark("clickTime", "1 hour")

# COMMAND ----------

# MAGIC %md
# MAGIC Passo 3: Realizar o join entre os streams com restrição de tempo de evento
# MAGIC
# MAGIC Para correlacionar as impressões que levaram a cliques, realizamos um join entre os dois streams com base no adId e no userId, garantindo que o clique ocorreu dentro de uma hora após a impressão.

# COMMAND ----------

# Join entre os dois streams com condição de tempo
joined_stream = impressions_with_watermark.alias("impressions").join(
    clicks_with_watermark.alias("clicks"),
    expr("""
        impressions.impressionAdId = clicks.clickAdId AND
        impressions.userId = clicks.userId AND
        clicks.clickTime >= impressions.impressionTime AND
        clicks.clickTime <= impressions.impressionTime + interval 1 hour
    """)
)

# COMMAND ----------

joined_stream.display()

# COMMAND ----------

# MAGIC %md
# MAGIC Passo 4: Processar e exibir os resultados
# MAGIC
# MAGIC Por fim, escrevemos o resultado do join para a memória ou para outro sink de sua preferência.

# COMMAND ----------

query = (
    joined_stream.writeStream
    .outputMode("append")
    .format("memory")
    .queryName("my_query")
    .trigger(processingTime="10 seconds")
    .start()
)
query.awaitTermination()

# COMMAND ----------

# Posteriormente, é possível consultar os dados armazenados na tabela temporária
spark.sql("SELECT * FROM my_query").display()

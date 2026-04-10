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
# MAGIC 3. Ler a saída do CDF com Spark SQL ou PySpark  usando API Batch 
# MAGIC

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, IntegerType, StringType,TimestampType

# COMMAND ----------

# Habilita o CDF para todas as tabelas novas na Spark Session
# spark.sql("set spark.databricks.delta.properties.defaults.enableChangeDataFeed = true;")

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS sandbox.demo.cdf (id_cliente INT, nome_cliente STRING, estado_cliente STRING) -- TBLPROPERTIES (delta.enableChangeDataFeed = true)

# COMMAND ----------

# MAGIC %sql
# MAGIC desc extended sandbox.demo.cdf 

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE sandbox.demo.cdf SET TBLPROPERTIES (delta.enableChangeDataFeed = true)

# COMMAND ----------

# MAGIC %sql
# MAGIC desc detail sandbox.demo.cdf 

# COMMAND ----------

# Criar schema
schema = StructType([
    StructField("id_cliente", IntegerType(), False),
    StructField("nome_cliente", StringType(), True),
    StructField("estado_cliente", StringType(), True)
])

# Criar DataFrame vazio
df_vazio = spark.createDataFrame([], schema)

# Salvar como tabela Delta com CDF habilitado
df_vazio.write.format("delta") \
    .option("delta.enableChangeDataFeed", "true") \
    .mode("append") \
    .saveAsTable("sandbox.demo.cdf")

# COMMAND ----------

# MAGIC %sql
# MAGIC desc detail sandbox.demo.cdf

# COMMAND ----------

# Ver versões disponíveis da tabela
spark.sql(f"DESCRIBE HISTORY sandbox.demo.cdf").display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## PySpark

# COMMAND ----------

dados_iniciais = [
    (1, "Ana", "SP"),
    (2, "Bruno", "RJ"),
    (3, "Carla", "MG")
]

df_iniciais = spark.createDataFrame(dados_iniciais, schema)

df_iniciais.write.format("delta") \
    .mode("append") \
    .option("delta.enableChangeDataFeed", "true") \
    .saveAsTable("sandbox.demo.cdf")

# COMMAND ----------

# Ver versões disponíveis da tabela
spark.sql(f"DESCRIBE HISTORY sandbox.demo.cdf").display()

# COMMAND ----------

novos_dados = [
    (4, "Daniel", "BA"),
    (5, "Eduarda", "RS"),
    (6, "Felipe", "PR")
]

df_novos = spark.createDataFrame(novos_dados, schema)

df_novos.write.format("delta") \
    .mode("append") \
    .saveAsTable("sandbox.demo.cdf")

# COMMAND ----------

# Ver versões disponíveis da tabela
spark.sql(f"DESCRIBE HISTORY sandbox.demo.cdf").display()

# COMMAND ----------

spark.sql("""
    UPDATE sandbox.demo.cdf
    SET nome_cliente = CONCAT('UPD_', nome_cliente)
    WHERE id_cliente IN (2, 5)
""")

# COMMAND ----------

# Ver versões disponíveis da tabela
spark.sql(f"DESCRIBE HISTORY sandbox.demo.cdf").display()

# COMMAND ----------

spark.sql("""
         DELETE FROM sandbox.demo.cdf
         WHERE id_cliente = 3
""")

# COMMAND ----------

# Ver versões disponíveis da tabela
spark.sql(f"DESCRIBE HISTORY sandbox.demo.cdf").display()

# COMMAND ----------

# Exemplo: mudanças entre as versões 0 e 4 (ajuste conforme a saída do comando acima)
df_cdf = (spark.read.format("delta") 
    .option("readChangeData", "true") 
    .option("startingVersion", 1) 
    # .option("endingVersion", 3)
    .table("sandbox.demo.cdf")
)
df_cdf.display()

# COMMAND ----------

ts_update = "2025-05-25T19:00:00.000+00:00"

# COMMAND ----------

# Exemplo: mudanças entre as versões 0 e 4 (ajuste conforme a saída do comando acima)
df_cdf = (spark.read.format("delta") 
    .option("readChangeData", "true")
    #TODO: ajustar conforme o _commit_timestamp 
    .option("startingTimestamp", "2025-05-25T18:59:00.000+00:00") 
    # .option("endingTimestamp", "2025-05-25T19:00:22.000+00:00")
    .table("sandbox.demo.cdf")
)
df_cdf = df_cdf.orderBy("_commit_timestamp", ascending=False)
display(df_cdf)

# COMMAND ----------

# MAGIC %md
# MAGIC ## SQL

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM table_changes("sandbox.demo.cdf", 1)
# MAGIC order by _commit_version desc

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM table_changes("sandbox.demo.cdf", "2025-05-25T19:00:29.000+00:00")
# MAGIC order by _commit_timestamp desc

# COMMAND ----------

# MAGIC %md
# MAGIC ## Limpando o Ambiente

# COMMAND ----------

# MAGIC %sql
# MAGIC drop table sandbox.demo.cdf
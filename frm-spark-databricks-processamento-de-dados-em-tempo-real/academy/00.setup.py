# Databricks notebook source
# MAGIC %md
# MAGIC # Bem-vindo ao Notebook de Setup do Curso
# MAGIC
# MAGIC Este notebook foi criado para ajudá-lo a configurar todo o ambiente necessário para a execução do curso. 
# MAGIC
# MAGIC Aqui, você encontrará todas as instruções e comandos necessários para garantir que seu ambiente esteja pronto para as atividades práticas.
# MAGIC
# MAGIC
# MAGIC ## Objetivo
# MAGIC
# MAGIC O objetivo é garantir que você tenha um ambiente de desenvolvimento robusto e pronto para que você possa focar no aprendizado e na prática dos conceitos do curso sem se preocupar com problemas técnicos.
# MAGIC
# MAGIC Vamos começar!

# COMMAND ----------

#TODO : Preencher com o URL do Storage
storage_root = ""

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sandbox

# COMMAND ----------

catalogo_sandbox = "sandbox"
schema_demo = "demo"
volume_demo = "cdf"

# COMMAND ----------

spark.sql(f"create catalog if not exists {catalogo_sandbox} managed location '{storage_root}'")
spark.sql(f"create schema if not exists {catalogo_sandbox}.{schema_demo}")
spark.sql(f"create volume if not exists {catalogo_sandbox}.{schema_demo}.{volume_demo}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Landing

# COMMAND ----------

catalog_landing = "landing"
schema_gcn = "gcn"
volume_gcn = "gcn"

# COMMAND ----------

spark.sql(f"create catalog if not exists {catalog_landing} managed location '{storage_root}'")
spark.sql(f"create schema if not exists {catalog_landing}.{schema_gcn}")
spark.sql(f"create volume if not exists {catalog_landing}.{schema_gcn}.{volume_gcn}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze

# COMMAND ----------

# DBTITLE 1,Tabela heartbeat
catalog_bronze = "bronze"
schema_gcn = "gcn"
schema_cdc = "cdc"
schema_scd = "scd"
volume_checkpoints = "_checkpoints"
volume_schema = "_schema"

# COMMAND ----------

spark.sql(f"create catalog if not exists {catalog_bronze} managed location '{storage_root}'")
spark.sql(f"create schema if not exists {catalog_bronze}.{schema_gcn}")
spark.sql(f"create schema if not exists {catalog_bronze}.{schema_cdc}")
spark.sql(f"create schema if not exists {catalog_bronze}.{schema_scd}")
spark.sql(f"create volume if not exists {catalog_bronze}.{schema_scd}.{volume_checkpoints}")
spark.sql(f"create volume if not exists {catalog_bronze}.{schema_gcn}.{volume_checkpoints}")
spark.sql(f"create volume if not exists {catalog_bronze}.{schema_gcn}.{volume_schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver

# COMMAND ----------

catalog_silver = "silver"
schema_demo = "demo"

# COMMAND ----------

spark.sql(f"create catalog if not exists {catalog_silver} managed location '{storage_root}'")
spark.sql(f"create schema if not exists {catalog_silver}.{schema_gcn}")
spark.sql(f"create schema if not exists {catalog_silver}.{schema_cdc}")
spark.sql(f"create schema if not exists {catalog_silver}.{schema_scd}")
spark.sql(f"create schema if not exists {catalog_silver}.{schema_demo}")
spark.sql(f"create volume if not exists {catalog_silver}.{schema_gcn}.{volume_checkpoints}")
spark.sql(f"create volume if not exists {catalog_silver}.{schema_cdc}.{volume_checkpoints}")
spark.sql(f"create volume if not exists {catalog_silver}.{schema_scd}.{volume_checkpoints}")
spark.sql(f"create volume if not exists {catalog_silver}.{schema_gcn}.{volume_schema}")
spark.sql(f"create volume if not exists {catalog_silver}.{schema_demo}.{volume_checkpoints}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Gold

# COMMAND ----------

catalog_gold = "gold"

# COMMAND ----------

spark.sql(f"create catalog if not exists {catalog_gold} managed location '{storage_root}'")
spark.sql(f"create schema if not exists {catalog_gold}.{schema_demo}")
spark.sql(f"create schema if not exists {catalog_gold}.{schema_gcn}")
spark.sql(f"create volume if not exists {catalog_gold}.{schema_demo}.{volume_checkpoints}")
spark.sql(f"create volume if not exists {catalog_gold}.{schema_gcn}.{volume_checkpoints}")
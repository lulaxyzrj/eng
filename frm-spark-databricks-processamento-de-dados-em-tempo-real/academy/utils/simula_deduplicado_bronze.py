# Databricks notebook source
# MAGIC %md
# MAGIC #Notebook para gerar uma camada bronze duplicada
# MAGIC
# MAGIC Esse notebook tem o objetivo de criar uma tabela bronze simulando duplicação de dados.

# COMMAND ----------

print("Carregando batch 1")
df = spark.read.format("json").load("/Volumes/landing/gcn/gcn/arquivos/")
df.write.format("delta").mode("overwrite").saveAsTable("bronze.gcn.lab_deduplication")
print("Fim do batch 1")

# COMMAND ----------

print("Carregando batch 2")
df = spark.read.format("json").load("/Volumes/landing/gcn/gcn/arquivos/")
df.write.format("delta").mode("append").saveAsTable("bronze.gcn.lab_deduplication")
print("Fim do batch 2")
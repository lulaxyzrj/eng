# Databricks notebook source



# COMMAND ----------
import pyspark.sql.functions as F

  

df = spark.read.format("json").load(

"abfss://landing@adlsubereatsdevsji8.dfs.core.windows.net/mongodb/items/*.jsonl"

).select(

"*",

F.col("_metadata.file_path").alias("source_file"),

F.col("_metadata.file_modification_time").alias("ingestion_time")

)
display(df)
# COMMAND ----------

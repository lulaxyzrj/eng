# Databricks notebook source

try:
    spark
except NameError:
    from utils.spark_session_config import get_spark_will_fall_back
    spark = get_spark_will_fall_back()

# COMMAND ----------
import pyspark.sql.functions as F

  

df = spark.read.format("json").load(

"abfss://landing@adlsubereatsdevsji8.dfs.core.windows.net/mongodb/items/*.jsonl"

).select(

"*",

F.col("_metadata.file_path").alias("source_file"),

F.col("_metadata.file_modification_time").alias("ingestion_time")

)
df.show(truncate=False)
# COMMAND ----------

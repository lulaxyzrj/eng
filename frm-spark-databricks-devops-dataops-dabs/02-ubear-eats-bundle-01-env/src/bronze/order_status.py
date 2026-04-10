# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer - Order Status
# MAGIC 
# MAGIC Raw ingestion from landing zone using Auto Loader.
# MAGIC Append-only with file metadata for lineage.
# MAGIC 
# MAGIC **Sources:**
# MAGIC - `kafka/orders/*.jsonl`
# MAGIC - `kafka/status/*.jsonl`
# MAGIC - `kafka/payments/*.jsonl`

# COMMAND ----------

import dlt
from pyspark.sql import functions as F

# COMMAND ----------

# Pipeline parameters (set in resources/pipelines/order_status.yml)
LANDING_PATH = spark.conf.get("pipeline.landing_path")
BRONZE_SCHEMA = spark.conf.get("pipeline.bronze_schema")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Orders

# COMMAND ----------

@dlt.table(
    name=f"{BRONZE_SCHEMA}.kafka_orders",
    comment="Raw orders from landing zone.",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "order_id"
    }
)
def kafka_orders():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", f"{LANDING_PATH}/_schemas/kafka/orders")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(f"{LANDING_PATH}/kafka/orders/*.jsonl")
        .select(
            "*",
            F.col("_metadata.file_path").alias("_source_file"),
            F.col("_metadata.file_modification_time").alias("_ingestion_time"),
            F.current_timestamp().alias("_processed_time")
        )
    )

# COMMAND ----------
# MAGIC %md
# MAGIC ## Order Status

# COMMAND ----------

@dlt.table(
    name=f"{BRONZE_SCHEMA}.kafka_order_status",
    comment="Raw order status transitions (state machine).",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "order_identifier"
    }
)
def kafka_order_status():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", f"{LANDING_PATH}/_schemas/kafka/status")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(f"{LANDING_PATH}/kafka/status/*.jsonl")
        .select(
            "*",
            F.col("_metadata.file_path").alias("_source_file"),
            F.col("_metadata.file_modification_time").alias("_ingestion_time"),
            F.current_timestamp().alias("_processed_time")
        )
    )

# COMMAND ----------
# MAGIC %md
# MAGIC ## Payments

# COMMAND ----------

@dlt.table(
    name=f"{BRONZE_SCHEMA}.kafka_payments",
    comment="Raw payments from landing zone.",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "payment_id"
    }
)
def kafka_payments():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", f"{LANDING_PATH}/_schemas/kafka/payments")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(f"{LANDING_PATH}/kafka/payments/*.jsonl")
        .select(
            "*",
            F.col("_metadata.file_path").alias("_source_file"),
            F.col("_metadata.file_modification_time").alias("_ingestion_time"),
            F.current_timestamp().alias("_processed_time")
        )
    )
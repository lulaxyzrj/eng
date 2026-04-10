# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer - Order Status
# MAGIC 
# MAGIC Cleaned, typed, and validated data.
# MAGIC Quality expectations applied.

# COMMAND ----------

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, IntegerType, DoubleType, TimestampType

# COMMAND ----------

# Pipeline parameters (set in resources/pipelines/order_status.yml)
BRONZE_SCHEMA = spark.conf.get("pipeline.bronze_schema")
SILVER_SCHEMA = spark.conf.get("pipeline.silver_schema")

# COMMAND ----------

# Status sequence for funnel ordering
STATUS_SEQUENCE = {
    "Order Placed": 1,
    "In Analysis": 2,
    "Accepted": 3,
    "Preparing": 4,
    "Ready for Pickup": 5,
    "Picked Up": 6,
    "Out for Delivery": 7,
    "Delivered": 8,
    "Completed": 9
}

# COMMAND ----------
# MAGIC %md
# MAGIC ## Orders

# COMMAND ----------

@dlt.table(
    name=f"{SILVER_SCHEMA}.orders",
    comment="Cleaned orders with proper data types.",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "order_id"
    }
)
@dlt.expect_or_drop("valid_order_id", "order_id IS NOT NULL")
@dlt.expect_or_drop("valid_total_amount", "total_amount > 0")
@dlt.expect("has_user_key", "user_key IS NOT NULL")
def silver_orders():
    return (
        dlt.read_stream(f"{BRONZE_SCHEMA}.kafka_orders")
        .select(
            F.col("order_id").cast(StringType()).alias("order_id"),
            F.col("user_key").cast(StringType()).alias("user_key"),
            F.col("restaurant_key").cast(StringType()).alias("restaurant_key"),
            F.col("driver_key").cast(StringType()).alias("driver_key"),
            F.col("rating_key").cast(StringType()).alias("rating_key"),
            F.col("payment_key").cast(StringType()).alias("payment_key"),
            F.to_timestamp("order_date", "yyyy-MM-dd HH:mm:ss.SSSSSS").alias("order_timestamp"),
            F.col("total_amount").cast(DoubleType()).alias("total_amount"),
            F.to_timestamp("dt_current_timestamp", "yyyy-MM-dd HH:mm:ss.SSS").alias("event_timestamp"),
            F.date_format(
                F.to_timestamp("order_date", "yyyy-MM-dd HH:mm:ss.SSSSSS"), 
                "yyyy-MM-dd"
            ).alias("order_date_key"),
            F.hour(F.to_timestamp("order_date", "yyyy-MM-dd HH:mm:ss.SSSSSS")).alias("order_hour"),
            F.col("_source_file"),
            F.col("_ingestion_time"),
            F.col("_processed_time")
        )
    )

# COMMAND ----------
# MAGIC %md
# MAGIC ## Order Status

# COMMAND ----------

@dlt.table(
    name=f"{SILVER_SCHEMA}.order_status",
    comment="Cleaned order status with flattened state machine.",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "order_identifier,status_sequence"
    }
)
@dlt.expect_or_drop("valid_status_id", "status_id IS NOT NULL")
@dlt.expect_or_drop("valid_order_identifier", "order_identifier IS NOT NULL")
@dlt.expect_or_drop("valid_status_name", "status_name IS NOT NULL")
def silver_order_status():
    status_map = F.create_map([F.lit(x) for item in STATUS_SEQUENCE.items() for x in item])
    
    return (
        dlt.read_stream(f"{BRONZE_SCHEMA}.kafka_order_status")
        .select(
            F.col("status_id").cast(IntegerType()).alias("status_id"),
            F.col("order_identifier").cast(StringType()).alias("order_identifier"),
            F.col("status.status_name").cast(StringType()).alias("status_name"),
            (F.col("status.timestamp") / 1000).cast(TimestampType()).alias("status_timestamp"),
            F.to_timestamp("dt_current_timestamp", "yyyy-MM-dd HH:mm:ss.SSS").alias("event_timestamp"),
            F.col("_source_file"),
            F.col("_ingestion_time"),
            F.col("_processed_time")
        )
        .withColumn("status_sequence", status_map[F.col("status_name")])
        .withColumn("status_date_key", F.date_format("status_timestamp", "yyyy-MM-dd"))
        .withColumn("status_hour", F.hour("status_timestamp"))
    )

# COMMAND ----------
# MAGIC %md
# MAGIC ## Payments

# COMMAND ----------

@dlt.table(
    name=f"{SILVER_SCHEMA}.payments",
    comment="Cleaned payments with proper data types.",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "payment_id"
    }
)
@dlt.expect_or_drop("valid_payment_id", "payment_id IS NOT NULL")
@dlt.expect_or_drop("valid_amount", "amount > 0")
@dlt.expect("valid_status", "status IS NOT NULL")
def silver_payments():
    return (
        dlt.read_stream(f"{BRONZE_SCHEMA}.kafka_payments")
        .select(
            F.col("payment_id").cast(StringType()).alias("payment_id"),
            F.col("order_key").cast(StringType()).alias("order_key"),
            F.col("amount").cast(DoubleType()).alias("amount"),
            F.col("currency").cast(StringType()).alias("currency"),
            F.col("method").cast(StringType()).alias("method"),
            F.col("provider").cast(StringType()).alias("provider"),
            F.col("card_brand").cast(StringType()).alias("card_brand"),
            F.col("status").cast(StringType()).alias("status"),
            F.col("failure_reason").cast(StringType()).alias("failure_reason"),
            F.col("refunded").cast("boolean").alias("refunded"),
            F.col("platform_fee").cast(DoubleType()).alias("platform_fee"),
            F.col("provider_fee").cast(DoubleType()).alias("provider_fee"),
            F.col("net_amount").cast(DoubleType()).alias("net_amount"),
            F.to_timestamp("timestamp", "yyyy-MM-dd HH:mm:ss.SSS").alias("payment_timestamp"),
            F.to_timestamp("dt_current_timestamp", "yyyy-MM-dd HH:mm:ss.SSS").alias("event_timestamp"),
            F.col("_source_file"),
            F.col("_ingestion_time"),
            F.col("_processed_time")
        )
        .withColumn("payment_date_key", F.date_format("payment_timestamp", "yyyy-MM-dd"))
        .withColumn("payment_hour", F.hour("payment_timestamp"))
    )


# COMMAND ----------
# MAGIC %md
# MAGIC ## Orders Enriched (with latest status)

# COMMAND ----------

@dlt.table(
    name=f"{SILVER_SCHEMA}.orders_enriched",
    comment="Orders joined with latest status for revenue analysis.",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "order_id"
    }
)
def silver_orders_enriched():
    """Orders with current status for revenue metrics."""
    from pyspark.sql.window import Window
    
    orders_df = dlt.read(f"{SILVER_SCHEMA}.orders")
    status_df = dlt.read(f"{SILVER_SCHEMA}.order_status")
    
    # Get latest status per order
    window_latest = Window.partitionBy("order_identifier").orderBy(
        F.desc("status_sequence"),
        F.desc("status_timestamp")
    )
    
    latest_status = (
        status_df
        .withColumn("row_num", F.row_number().over(window_latest))
        .filter(F.col("row_num") == 1)
        .select(
            F.col("order_identifier"),
            F.col("status_name").alias("current_status"),
            F.col("status_sequence").alias("current_status_sequence"),
            F.col("status_timestamp").alias("last_status_timestamp")
        )
    )
    
    return (
        orders_df
        .join(
            latest_status,
            orders_df.order_id == latest_status.order_identifier,
            "left"
        )
        .select(
            orders_df["*"],
            "current_status",
            "current_status_sequence",
            "last_status_timestamp"
        )
    )
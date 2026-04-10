# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer - Order Funnel & Payment Health
# MAGIC 
# MAGIC Aggregated metrics for Streamlit dashboard.

# COMMAND ----------

import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------

# Pipeline parameters (set in resources/pipelines/order_status.yml)
SILVER_SCHEMA = spark.conf.get("pipeline.silver_schema")
GOLD_SCHEMA = spark.conf.get("pipeline.gold_schema")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Order Funnel Metrics
# MAGIC Source: `silver.order_status`

# COMMAND ----------

@dlt.table(
    name=f"{GOLD_SCHEMA}.order_funnel_live",
    comment="Real-time order counts by status.",
    table_properties={"quality": "gold"}
)
def gold_order_funnel_live():
    """Current order distribution across funnel stages."""
    status_df = dlt.read(f"{SILVER_SCHEMA}.order_status")
    window_latest = Window.partitionBy("order_identifier").orderBy(
        F.desc("status_sequence"), 
        F.desc("status_timestamp")
    )
    
    return (
        status_df
        .withColumn("row_num", F.row_number().over(window_latest))
        .filter(F.col("row_num") == 1)
        .groupBy("status_name", "status_sequence")
        .agg(F.count("order_identifier").alias("order_count"))
        .withColumn("last_updated", F.current_timestamp())
        .orderBy("status_sequence")
    )

# COMMAND ----------

@dlt.table(
    name=f"{GOLD_SCHEMA}.order_transitions",
    comment="Avg latency between status transitions.",
    table_properties={"quality": "gold"}
)
def gold_order_transitions():
    """Time between consecutive status changes."""
    status_df = dlt.read(f"{SILVER_SCHEMA}.order_status")
    window_prev = Window.partitionBy("order_identifier").orderBy("status_timestamp")
    
    return (
        status_df
        .withColumn("prev_status_name", F.lag("status_name").over(window_prev))
        .withColumn("prev_timestamp", F.lag("status_timestamp").over(window_prev))
        .filter(F.col("prev_timestamp").isNotNull())
        .withColumn(
            "transition_seconds",
            F.col("status_timestamp").cast("long") - F.col("prev_timestamp").cast("long")
        )
        .withColumn(
            "transition_name",
            F.concat(F.col("prev_status_name"), F.lit(" → "), F.col("status_name"))
        )
        .groupBy("transition_name", "prev_status_name", "status_name")
        .agg(
            F.count("*").alias("transition_count"),
            F.avg("transition_seconds").alias("avg_seconds"),
            F.percentile_approx("transition_seconds", 0.5).alias("median_seconds")
        )
        .withColumn("avg_minutes", F.round(F.col("avg_seconds") / 60, 2))
        .withColumn("last_updated", F.current_timestamp())
    )

# COMMAND ----------

@dlt.table(
    name=f"{GOLD_SCHEMA}.order_funnel_hourly",
    comment="Hourly order counts by status.",
    table_properties={"quality": "gold"}
)
def gold_order_funnel_hourly():
    """Time-series data for trends."""
    return (
        dlt.read(f"{SILVER_SCHEMA}.order_status")
        .groupBy("status_date_key", "status_hour", "status_name", "status_sequence")
        .agg(
            F.count("*").alias("event_count"),
            F.countDistinct("order_identifier").alias("unique_orders")
        )
        .withColumn(
            "hour_timestamp",
            F.to_timestamp(
                F.concat(
                    F.col("status_date_key"), 
                    F.lit(" "), 
                    F.lpad(F.col("status_hour").cast("string"), 2, "0"), 
                    F.lit(":00:00")
                ),
                "yyyy-MM-dd HH:mm:ss"
            )
        )
        .withColumn("last_updated", F.current_timestamp())
    )

# COMMAND ----------

@dlt.table(
    name=f"{GOLD_SCHEMA}.order_completion_daily",
    comment="Daily completion rates.",
    table_properties={"quality": "gold"}
)
def gold_order_completion_daily():
    """Daily KPIs for order completion."""
    status_df = dlt.read(f"{SILVER_SCHEMA}.order_status")
    
    order_summary = (
        status_df
        .groupBy("order_identifier")
        .agg(
            F.min("status_timestamp").alias("first_timestamp"),
            F.max("status_timestamp").alias("last_timestamp"),
            F.max(F.when(F.col("status_name") == "Completed", 1).otherwise(0)).alias("is_completed"),
            F.max(F.when(F.col("status_name") == "Delivered", 1).otherwise(0)).alias("is_delivered")
        )
        .withColumn(
            "completion_seconds",
            F.when(
                F.col("is_completed") == 1,
                F.unix_timestamp("last_timestamp") - F.unix_timestamp("first_timestamp")
            )
        )
        .withColumn("order_date", F.date_format("first_timestamp", "yyyy-MM-dd"))
    )
    
    return (
        order_summary
        .groupBy("order_date")
        .agg(
            F.count("*").alias("total_orders"),
            F.sum("is_completed").alias("completed_orders"),
            F.sum("is_delivered").alias("delivered_orders"),
            F.avg("completion_seconds").alias("avg_completion_seconds")
        )
        .withColumn("completion_rate_pct", F.round(F.col("completed_orders") / F.col("total_orders") * 100, 2))
        .withColumn("avg_completion_minutes", F.round(F.col("avg_completion_seconds") / 60, 2))
        .withColumn("last_updated", F.current_timestamp())
        .orderBy("order_date")
    )

# COMMAND ----------
# MAGIC %md
# MAGIC ## Revenue Metrics
# MAGIC Source: `silver.orders_enriched`

# COMMAND ----------

@dlt.table(
    name=f"{GOLD_SCHEMA}.order_revenue_by_status",
    comment="Total revenue by current order status.",
    table_properties={"quality": "gold"}
)
def gold_order_revenue_by_status():
    """Revenue distribution across funnel stages."""
    orders_df = dlt.read(f"{SILVER_SCHEMA}.orders_enriched")
    
    return (
        orders_df
        .filter(F.col("current_status").isNotNull())
        .groupBy("current_status", "current_status_sequence")
        .agg(
            F.count("order_id").alias("order_count"),
            F.sum("total_amount").alias("total_revenue"),
            F.avg("total_amount").alias("avg_ticket")
        )
        .withColumn("total_revenue", F.round("total_revenue", 2))
        .withColumn("avg_ticket", F.round("avg_ticket", 2))
        .withColumn("last_updated", F.current_timestamp())
        .orderBy("current_status_sequence")
    )

# COMMAND ----------
# MAGIC %md
# MAGIC ## Payment Health Metrics
# MAGIC Source: `silver.payments`

# COMMAND ----------

@dlt.table(
    name=f"{GOLD_SCHEMA}.payment_health",
    comment="Payment success rates by method.",
    table_properties={"quality": "gold"}
)
def gold_payment_health():
    """Payment health metrics - success rate by payment method."""
    payments_df = dlt.read(f"{SILVER_SCHEMA}.payments")
    
    return (
        payments_df
        .groupBy("method")
        .agg(
            F.count("*").alias("total_payments"),
            F.sum(F.when(F.col("status") == "succeeded", 1).otherwise(0)).alias("succeeded"),
            F.sum(F.when(F.col("status") == "failed", 1).otherwise(0)).alias("failed"),
            F.sum(F.when(F.col("status") == "pending", 1).otherwise(0)).alias("pending"),
            F.sum(F.when(F.col("status") == "refunded", 1).otherwise(0)).alias("refunded"),
            F.sum("amount").alias("total_amount"),
            F.sum("net_amount").alias("total_net_amount")
        )
        .withColumn("success_rate_pct", F.round(F.col("succeeded") / F.col("total_payments") * 100, 2))
        .withColumn("failure_rate_pct", F.round(F.col("failed") / F.col("total_payments") * 100, 2))
        .withColumn("last_updated", F.current_timestamp())
        .orderBy(F.desc("total_payments"))
    )

# COMMAND ----------

@dlt.table(
    name=f"{GOLD_SCHEMA}.payment_failures",
    comment="Payment failure reasons breakdown.",
    table_properties={"quality": "gold"}
)
def gold_payment_failures():
    """Failure reason analysis."""
    payments_df = dlt.read(f"{SILVER_SCHEMA}.payments")
    
    failed_payments = (
        payments_df
        .filter(F.col("status") == "failed")
        .filter(F.col("failure_reason").isNotNull())
        .filter(F.col("failure_reason") != "")
    )
    
    total_failed = failed_payments.count()
    
    return (
        failed_payments
        .groupBy("failure_reason")
        .agg(
            F.count("*").alias("failure_count"),
            F.sum("amount").alias("failed_amount")
        )
        .withColumn("failure_pct", F.round(F.col("failure_count") / F.lit(total_failed) * 100, 2))
        .withColumn("last_updated", F.current_timestamp())
        .orderBy(F.desc("failure_count"))
    )

# COMMAND ----------

@dlt.table(
    name=f"{GOLD_SCHEMA}.payment_by_provider",
    comment="Payment volume by provider.",
    table_properties={"quality": "gold"}
)
def gold_payment_by_provider():
    """Payment breakdown by provider (Stripe, PayPal, Adyen)."""
    payments_df = dlt.read(f"{SILVER_SCHEMA}.payments")
    
    return (
        payments_df
        .groupBy("provider")
        .agg(
            F.count("*").alias("total_payments"),
            F.sum(F.when(F.col("status") == "succeeded", 1).otherwise(0)).alias("succeeded"),
            F.sum("amount").alias("total_amount"),
            F.avg("platform_fee").alias("avg_platform_fee"),
            F.avg("provider_fee").alias("avg_provider_fee")
        )
        .withColumn("success_rate_pct", F.round(F.col("succeeded") / F.col("total_payments") * 100, 2))
        .withColumn("last_updated", F.current_timestamp())
        .orderBy(F.desc("total_payments"))
    )

# COMMAND ----------

@dlt.table(
    name=f"{GOLD_SCHEMA}.payment_daily",
    comment="Daily payment metrics.",
    table_properties={"quality": "gold"}
)
def gold_payment_daily():
    """Daily payment KPIs for trend analysis."""
    payments_df = dlt.read(f"{SILVER_SCHEMA}.payments")
    
    return (
        payments_df
        .groupBy("payment_date_key")
        .agg(
            F.count("*").alias("total_payments"),
            F.sum(F.when(F.col("status") == "succeeded", 1).otherwise(0)).alias("succeeded"),
            F.sum(F.when(F.col("status") == "failed", 1).otherwise(0)).alias("failed"),
            F.sum("amount").alias("total_amount"),
            F.sum("net_amount").alias("total_net_amount"),
            F.sum("platform_fee").alias("total_platform_fees")
        )
        .withColumn("success_rate_pct", F.round(F.col("succeeded") / F.col("total_payments") * 100, 2))
        .withColumn("last_updated", F.current_timestamp())
        .orderBy("payment_date_key")
    )
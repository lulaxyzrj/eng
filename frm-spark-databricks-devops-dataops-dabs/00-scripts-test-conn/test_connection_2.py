# Databricks notebook source



# COMMAND ----------
import pyspark.sql.functions as F


df1 = spark.table("ubereats_dev.bronze.bronze_order_status")


#display(df1)


# COMMAND ----------
df = spark.table("ubereats_dev.bronze.bronze_orders")


display(df)
# COMMAND ----------
df1.printSchema()
# COMMAND ----------

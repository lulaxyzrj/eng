# Databricks notebook source
from pyspark.sql import functions as F
from pyspark.sql.types import StringType
import os
import base64

# -----------------------------
# Parâmetros
# -----------------------------
ROWS = 10_000_000          # ajuste conforme tempo
PAYLOAD_SIZE = 2048       # 1 KB real por linha (~2 GB total)
OUTPUT_TABLE = "sandbox.default.spill_demo_raw"
spark.sql(f"CREATE TABLE IF NOT EXISTS {OUTPUT_TABLE} USING DELTA")
# -----------------------------
# UDF de alta entropia REAL
# -----------------------------
def random_string():
    return base64.b64encode(os.urandom(PAYLOAD_SIZE)).decode("utf-8")

random_udf = F.udf(random_string, StringType())

# -----------------------------
# Gerar dataset
# -----------------------------
df = (
    spark.range(0, ROWS)
    .withColumn("group_key", (F.rand() * 10).cast("int"))  # skew proposital
    .withColumn("payload", random_udf())
)

# -----------------------------
# Gravar fisicamente (Delta)
# -----------------------------
(
    df.write
      .mode("overwrite")
      .format("delta")
      .option('mergeSchema', 'true').saveAsTable(OUTPUT_TABLE)
)

# COMMAND ----------

# MAGIC %sql
# MAGIC describe detail sandbox.default.spill_demo_raw

# COMMAND ----------

df = spark.table("sandbox.default.spill_demo_raw")

(
    df.repartition(1)
      .orderBy("payload")
      .write
      .mode("overwrite")
      .format("delta")
      .saveAsTable("sandbox.default.spill_demo_sorted")
)

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from sandbox.default.spill_demo_sorted
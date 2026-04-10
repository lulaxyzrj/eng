import sys
import hashlib
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, rand, lit, when, monotonically_increasing_id
from pyspark.sql.types import StringType, DoubleType
import time

# === PARÂMETROS ===
if len(sys.argv) < 5:
    raise ValueError("Esperado: <stage> <orders_subdir> <products_subdir> <items_subdir> <output_path>")

stage = sys.argv[1].lower()
orders_subdir = sys.argv[2]
products_subdir = sys.argv[3]
items_subdir = sys.argv[4]
output_path = sys.argv[5]

# === SESSÃO ===
def get_spark():
    spark = SparkSession.builder \
        .appName(f"UberEats ETL - {stage}") \
        .config("spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "com.amazonaws:aws-java-sdk-bundle:1.11.900") \
        .getOrCreate()
    return spark

spark = get_spark()
spark.sparkContext.setLogLevel("INFO")

# === UDFs PESADAS COM PROTEÇÃO ===
@udf(returnType=StringType())
def ultra_hash(value):
    val = value or "0"
    for _ in range(1000):
        val = hashlib.sha256(val.encode()).hexdigest()
    return val

@udf(returnType=DoubleType())
def cpu_noise(n):
    n = n if n is not None else 0.0
    total = 0.0
    for i in range(5000):
        total += (i ** 0.5) / (i + 1)
    return total + n

# === BRONZE ===
if stage in ["bronze", "todos"]:
    orders_df = spark.read.json(f"s3a://{orders_subdir}/*").withColumn("stage", lit("bronze"))
    products_df = spark.read.json(f"s3a://{products_subdir}/*").withColumn("stage", lit("bronze"))
    items_df = spark.read.json(f"s3a://{items_subdir}/*").withColumn("stage", lit("bronze"))

    orders_df.write.mode("overwrite").parquet(f"{output_path}/bronze/orders")
    products_df.write.mode("overwrite").parquet(f"{output_path}/bronze/products")
    items_df.write.mode("overwrite").parquet(f"{output_path}/bronze/items")

# === SILVER ===
if stage in ["silver", "todos"]:
    orders_df = spark.read.parquet(f"{output_path}/bronze/orders")
    products_df = spark.read.parquet(f"{output_path}/bronze/products")
    items_df = spark.read.parquet(f"{output_path}/bronze/items")

    # Preenchimento de nulos antes de UDFs
    orders_df = orders_df.na.fill({"user_key": "null"})
    products_df = products_df.na.fill({"name": "null"})
    items_df = items_df.na.fill({"quantity": 0})

    enriched_orders = orders_df \
        .withColumn("id", monotonically_increasing_id()) \
        .withColumn("rand_col", rand()) \
        .withColumn("noise", cpu_noise(col("rand_col"))) \
        .withColumn("hash_user", ultra_hash(col("user_key"))) \
        .repartition(20)

    enriched_products = products_df \
        .withColumn("hash_name", ultra_hash(col("name"))) \
        .withColumn("rand_col", rand()) \
        .repartition(20)

    enriched_items = items_df \
        .withColumn("rand_col", rand()) \
        .withColumn("noise", cpu_noise(col("rand_col"))) \
        .repartition(20)

    enriched_orders.write.mode("overwrite").parquet(f"{output_path}/silver/orders")
    enriched_products.write.mode("overwrite").parquet(f"{output_path}/silver/products")
    enriched_items.write.mode("overwrite").parquet(f"{output_path}/silver/items")

# === GOLD ===
if stage in ["gold", "todos"]:
    orders_df = spark.read.parquet(f"{output_path}/silver/orders")
    products_df = spark.read.parquet(f"{output_path}/silver/products")
    items_df = spark.read.parquet(f"{output_path}/silver/items")

    joined = items_df.join(products_df, on="product_id", how="left") \
                     .withColumn("item_total", (col("price") * col("quantity")).cast(DoubleType())) \
                     .withColumn("score", cpu_noise(col("item_total"))) \
                     .repartition(30)

    agg = joined.groupBy("order_id").agg({"item_total": "sum", "score": "avg"}) \
                .withColumnRenamed("sum(item_total)", "total_sum") \
                .withColumnRenamed("avg(score)", "score_avg")

    result = orders_df.join(agg, on="order_id", how="left") \
                      .withColumn("final_score", cpu_noise(col("score_avg"))) \
                      .withColumn("val_hashed", ultra_hash(col("order_id"))) \
                      .repartition(10)

    for i in range(3):
        print(f"[GOLD] Escrita iterativa {i+1}")
        result.withColumn("batch", lit(i)).write.mode("overwrite").parquet(f"{output_path}/gold/batch_{i}")

spark.stop()
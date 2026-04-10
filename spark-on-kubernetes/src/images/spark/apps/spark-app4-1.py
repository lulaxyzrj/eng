import sys
import time
import hashlib
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, isnan, when, udf, lit, rand
from pyspark.sql.types import StringType, FloatType

# === PARÂMETROS ===

if len(sys.argv) < 5:
    raise ValueError("Esperado: <stage> <orders_subdir> <products_subdir> <items_subdir> <output_path>")

stage = sys.argv[1].lower()         # 'bronze', 'silver', 'gold', 'todos'
orders_subdir = sys.argv[2]
products_subdir = sys.argv[3]
items_subdir = sys.argv[4]
output_path = sys.argv[5]

# === SESSÃO SPARK ===
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

# === UDF PESADA (emula CPU-bound) ===
@udf(returnType=StringType())
def heavy_hash(value):
    result = value if value else ""
    for _ in range(500):
        result = hashlib.sha256(result.encode()).hexdigest()
    return result

# === BRONZE ===
if stage in ["bronze", "todos"]:
    orders_df = spark.read.json(f"s3a://{orders_subdir}/*")
    products_df = spark.read.json(f"s3a://{products_subdir}/*")
    items_df = spark.read.json(f"s3a://{items_subdir}/*")

    orders_df.write.mode("overwrite").parquet(f"{output_path}/bronze/orders")
    products_df.write.mode("overwrite").parquet(f"{output_path}/bronze/products")
    items_df.write.mode("overwrite").parquet(f"{output_path}/bronze/items")

# === SILVER ===
if stage in ["silver", "todos"]:
    orders_df = spark.read.parquet(f"{output_path}/bronze/orders")
    products_df = spark.read.parquet(f"{output_path}/bronze/products")
    items_df = spark.read.parquet(f"{output_path}/bronze/items")

    orders_clean = orders_df.dropna().dropDuplicates(["order_id"])
    products_clean = products_df.dropna().dropDuplicates(["product_id"])
    items_clean = items_df.dropna().dropDuplicates(["order_id", "product_id"])

    # Enriquecimento com UDF artificial
    orders_enriched = orders_clean.withColumn("hashed_user", heavy_hash(col("user_key")))
    products_enriched = products_clean.withColumn("name_hashed", heavy_hash(col("name")))
    items_enriched = items_clean.withColumn("rand_col", rand())

    orders_enriched.write.mode("overwrite").parquet(f"{output_path}/silver/orders")
    products_enriched.write.mode("overwrite").parquet(f"{output_path}/silver/products")
    items_enriched.write.mode("overwrite").parquet(f"{output_path}/silver/items")

# === GOLD ===
if stage in ["gold", "todos"]:
    orders_df = spark.read.parquet(f"{output_path}/silver/orders")
    products_df = spark.read.parquet(f"{output_path}/silver/products")
    items_df = spark.read.parquet(f"{output_path}/silver/items")

    # Join + agregações artificiais
    items_joined = items_df.join(products_df, on="product_id", how="left")
    items_joined = items_joined.withColumn("item_total", col("price") * col("quantity"))

    orders_validated = orders_df.join(items_joined.groupBy("order_id")
                                       .agg({"item_total": "sum"}).withColumnRenamed("sum(item_total)", "total_calc"),
                                       on="order_id", how="left")

    orders_validated = orders_validated.withColumn("diff", col("total_calc") - lit(0.01))

    # Repetição artificial: múltiplas escritas em loop para carga extra
    for i in range(5):
        print(f"Iteração {i+1} de gravação gold...")
        orders_validated.withColumn("loop", lit(i)).write.mode("overwrite").parquet(f"{output_path}/gold/loop_{i}")

spark.stop()

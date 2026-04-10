import sys
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import col, count, isnan, when

# === 0. PARÂMETROS VIA ARGUMENTOS ===

if len(sys.argv) < 4:
    raise ValueError("Parâmetros esperados: <subdiretório-dados> <caminho-base> <caminho-output>")

subdir = sys.argv[1]  # ex: "orders"
base_path = sys.argv[2]  # ex: "s3a://owshq-shadow-traffic-uber-eats"
output_path = sys.argv[3]  # ex: "s3a://owshq-shadow-traffic-uber-eats/parquet"

input_orders_path = f"{base_path}/kafka/{subdir}/*"
input_products_path = f"{base_path}/mysql/products/*"
input_items_path = f"{base_path}/mongodb/items/*"

# === 1. SESSÃO SPARK ===

def get_spark():
    spark = SparkSession.builder \
        .appName(f"UberEats ETL - {subdir}") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://datalake-hl.deepstore:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "minio") \
        .config("spark.hadoop.fs.s3a.secret.key", "minio123") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "com.amazonaws:aws-java-sdk-bundle:1.11.900") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("INFO")
    return spark

spark = get_spark()

# === 2. LEITURA DOS DADOS ===

orders_schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("user_key", StringType(), True),
    StructField("restaurant_key", StringType(), True),
    StructField("driver_key", StringType(), True),
    StructField("order_date", TimestampType(), True),
    StructField("total_amount", FloatType(), True),
    StructField("payment_id", StringType(), True)
])
orders_df = spark.read.schema(orders_schema).json(input_orders_path)

products_schema = StructType([
    StructField("product_id", StringType(), True),
    StructField("name", StringType(), True),
    StructField("price", FloatType(), True),
    StructField("restaurant_id", StringType(), True)
])
products_df = spark.read.schema(products_schema).json(input_products_path)

items_schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("quantity", IntegerType(), True)
])
items_df = spark.read.schema(items_schema).json(input_items_path)

# === 3. QUALIDADE DE DADOS ===

def check_nulls(df, name):
    print(f"\n[Verificação] Valores nulos no dataset '{name}':")
    exprs = []
    for c, dtype in df.dtypes:
        if dtype in ['double', 'float']:
            exprs.append(count(when(col(c).isNull() | isnan(c), c)).alias(c))
        else:
            exprs.append(count(when(col(c).isNull(), c)).alias(c))
    df.select(exprs).show()

def check_duplicates(df, id_col, name):
    print(f"\n[Verificação] Duplicatas em '{id_col}' no dataset '{name}':")
    df.groupBy(id_col).count().filter("count > 1").show()

check_nulls(orders_df, "orders")
check_nulls(products_df, "products")
check_nulls(items_df, "items")

check_duplicates(orders_df, "order_id", "orders")
check_duplicates(products_df, "product_id", "products")
check_duplicates(items_df, "order_id", "items")

# === 4. TRANSFORMAÇÕES ===

items_enriched = items_df.join(products_df, on="product_id", how="left")
items_enriched = items_enriched.withColumn("item_total", col("price") * col("quantity"))

order_totals = items_enriched.groupBy("order_id") \
    .agg({"item_total": "sum"}) \
    .withColumnRenamed("sum(item_total)", "calculated_total")

orders_validated = orders_df.join(order_totals, on="order_id", how="left")
orders_validated = orders_validated.withColumn("diff_total", col("total_amount") - col("calculated_total"))

print("\n[Verificação] Pedidos com diferença entre total registrado e calculado:")
orders_validated.filter(col("diff_total") != 0).show()

# === 5. SALVAR ===

orders_validated.write.mode("overwrite").parquet(f"{output_path}/orders_validated")
items_enriched.write.mode("overwrite").parquet(f"{output_path}/items_enriched")

spark.stop()

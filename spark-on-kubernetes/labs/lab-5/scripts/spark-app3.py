import sys
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import col, count, isnan, when

# === 0. PARÂMETROS ===

if len(sys.argv) < 5:
    raise ValueError("Esperado: <process_type> <orders_subdir> <products_subdir> <items_subdir> <output_path>")

process_type = sys.argv[1].lower()         # 'orders', 'products', 'items', 'todos'
orders_subdir = sys.argv[2]
products_subdir = sys.argv[3]
items_subdir = sys.argv[4]
output_path = sys.argv[5]

# === 1. SESSÃO SPARK ===

def get_spark():
    spark = SparkSession.builder \
        .appName(f"UberEats ETL - {process_type}") \
        .config("spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "com.amazonaws:aws-java-sdk-bundle:1.11.900") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("INFO")
    return spark

spark = get_spark()

# === 2. FUNÇÕES AUXILIARES ===

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

# === 3. PROCESSAMENTO CONDICIONAL ===

orders_df = products_df = items_df = None

if process_type in ["orders", "todos"]:
    orders_schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("user_key", StringType(), True),
        StructField("restaurant_key", StringType(), True),
        StructField("driver_key", StringType(), True),
        StructField("order_date", TimestampType(), True),
        StructField("total_amount", FloatType(), True),
        StructField("payment_id", StringType(), True)
    ])
    orders_df = spark.read.schema(orders_schema).json(f"s3a://{orders_subdir}/*")
    check_nulls(orders_df, "orders")
    check_duplicates(orders_df, "order_id", "orders")

if process_type in ["products", "todos"]:
    products_schema = StructType([
        StructField("product_id", StringType(), True),
        StructField("name", StringType(), True),
        StructField("price", FloatType(), True),
        StructField("restaurant_id", StringType(), True)
    ])
    products_df = spark.read.schema(products_schema).json(f"s3a://{products_subdir}/*")
    check_nulls(products_df, "products")
    check_duplicates(products_df, "product_id", "products")

if process_type in ["items", "todos"]:
    items_schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("product_id", StringType(), True),
        StructField("quantity", IntegerType(), True)
    ])
    items_df = spark.read.schema(items_schema).json(f"s3a://{items_subdir}/*")
    check_nulls(items_df, "items")
    check_duplicates(items_df, "order_id", "items")

# === 4. TRANSFORMAÇÕES (se todos disponíveis) ===

if process_type == "todos" and all([orders_df, products_df, items_df]):
    items_enriched = items_df.join(products_df, on="product_id", how="left")
    items_enriched = items_enriched.withColumn("item_total", col("price") * col("quantity"))

    order_totals = items_enriched.groupBy("order_id") \
        .agg({"item_total": "sum"}) \
        .withColumnRenamed("sum(item_total)", "calculated_total")

    orders_validated = orders_df.join(order_totals, on="order_id", how="left")
    orders_validated = orders_validated.withColumn("diff_total", col("total_amount") - col("calculated_total"))

    print("\n[Verificação] Pedidos com diferença entre total registrado e calculado:")
    orders_validated.filter(col("diff_total") != 0).show()

    orders_validated.write.mode("overwrite").parquet(f"{output_path}/orders_validated")
    items_enriched.write.mode("overwrite").parquet(f"{output_path}/items_enriched")

elif process_type == "orders":
    orders_df.write.mode("overwrite").parquet(f"{output_path}/orders_raw")

elif process_type == "products":
    products_df.write.mode("overwrite").parquet(f"{output_path}/products_raw")

elif process_type == "items":
    items_df.write.mode("overwrite").parquet(f"{output_path}/items_raw")

else:
    print(f"Tipo de processamento '{process_type}' não reconhecido.")

spark.stop()

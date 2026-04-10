from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import col, count, isnan, when

# === 0. CRIAÇÃO DA SESSÃO SPARK ===

def get_spark():
    spark = SparkSession.builder \
        .appName('UberEats ETL') \
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

# === 1. LEITURA DOS DADOS ===

# Orders (Kafka)
orders_schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("user_key", StringType(), True),
    StructField("restaurant_key", StringType(), True),
    StructField("driver_key", StringType(), True),
    StructField("order_date", TimestampType(), True),
    StructField("total_amount", FloatType(), True),
    StructField("payment_id", StringType(), True)
])
orders_df = spark.read.schema(orders_schema).json("s3a://owshq-shadow-traffic-uber-eats/kafka/orders/*")

# Products (MySQL)
products_schema = StructType([
    StructField("product_id", StringType(), True),
    StructField("name", StringType(), True),
    StructField("price", FloatType(), True),
    StructField("restaurant_id", StringType(), True)
])
products_df = spark.read.schema(products_schema).json("s3a://owshq-shadow-traffic-uber-eats/mysql/products/*")

# Itens (MongoDB)
items_schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("quantity", IntegerType(), True)
])
items_df = spark.read.schema(items_schema).json("s3a://owshq-shadow-traffic-uber-eats/mongodb/items/*")


# === 2. VERIFICAÇÕES DE QUALIDADE DE DADOS ===

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


# === 3. TRANSFORMAÇÕES E JOINs ===

# Join entre items e products para obter valor unitário
items_enriched = items_df.join(products_df, on="product_id", how="left")

# Calcular subtotal do item
items_enriched = items_enriched.withColumn("item_total", col("price") * col("quantity"))

# Agregar subtotal por pedido
order_totals = items_enriched.groupBy("order_id") \
    .agg({"item_total": "sum"}) \
    .withColumnRenamed("sum(item_total)", "calculated_total")

# Join com orders para comparar valores
orders_validated = orders_df.join(order_totals, on="order_id", how="left")

# Calcular diferença entre total registrado e calculado
orders_validated = orders_validated.withColumn("diff_total", col("total_amount") - col("calculated_total"))

# Mostrar registros onde há divergência nos valores
print("\n[Verificação] Pedidos com diferença entre total registrado e calculado:")
orders_validated.filter(col("diff_total") != 0).show()


# === 4. SALVAR RESULTADOS NO DATALAKE ===

orders_validated.write.mode("overwrite").parquet("s3a://owshq-shadow-traffic-uber-eats/parquet/orders_validated")
items_enriched.write.mode("overwrite").parquet("s3a://owshq-shadow-traffic-uber-eats/parquet/items_enriched")


# === 5. FINALIZAÇÃO ===
spark.stop()

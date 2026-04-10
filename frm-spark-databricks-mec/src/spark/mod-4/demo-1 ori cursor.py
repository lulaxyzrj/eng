"""
Demo 1: Delta Lake Foundation & Setup
==================================

MinIO ports (typical):
  - 9090 = Web Console only (browser) — do NOT use for Spark S3A.
  - 9000 = S3 API — use this for fs.s3a.endpoint (kubectl port-forward svc/... 9000:9000).

Environment (optional):
  S3A_ENDPOINT            default http://localhost:9000 (host + port-forward).
                            Docker Spark: http://host.docker.internal:9000
                            In-cluster: http://datalake-hl.deepstore:9000
  S3A_ACCESS_KEY / S3A_SECRET_KEY  or AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
                            default minio / minio123
  DEMO1_SHADOW_BUCKET     default owshq-shadow-traffic-uber-eats
  DEMO1_LAKEHOUSE_BUCKET  default owshq-uber-eats-lakehouse (create empty in MinIO)

Reads use directory prefixes (trailing /) so any JSONL under that path works.

Run (Docker Compose Spark + MinIO forwarded on host:9000):
  docker exec -e S3A_ENDPOINT=http://host.docker.internal:9000 -it spark-master \\
    /opt/bitnami/spark/bin/spark-submit --master spark://spark-master:7077 \\
    /opt/bitnami/spark/jobs/spark/mod-4/demo-1.py
"""

import os

from pyspark.sql import SparkSession
from delta.tables import DeltaTable
from pyspark.sql.functions import col


def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def buckets() -> tuple[str, str]:
    shadow = _env("DEMO1_SHADOW_BUCKET", "owshq-shadow-traffic-uber-eats")
    lake = _env("DEMO1_LAKEHOUSE_BUCKET", "owshq-uber-eats-lakehouse")
    return shadow, lake


def paths() -> dict[str, str]:
    shadow, lake = buckets()
    return {
        "restaurants_read": f"s3a://{shadow}/mysql/restaurants/",
        "bronze_restaurants": f"s3a://{lake}/bronze/restaurants",
        "drivers_read": f"s3a://{shadow}/postgres/drivers/",
        "bronze_drivers": f"s3a://{lake}/bronze/drivers",
        "orders_read": f"s3a://{shadow}/kafka/orders/",
        "bronze_orders": f"s3a://{lake}/bronze/orders",
        "users_read": f"s3a://{shadow}/mongodb/users/",
        "parquet_users": f"s3a://{lake}/parquet/users",
        "bronze_users": f"s3a://{lake}/bronze/users",
    }


def spark_session() -> SparkSession:
    """Spark + Delta + S3A (MinIO API on port 9000, not console 9090)."""

    endpoint = _env("S3A_ENDPOINT", "http://localhost:9000")
    access_key = _env("S3A_ACCESS_KEY") or _env("AWS_ACCESS_KEY_ID", "minio")
    secret_key = _env("S3A_SECRET_KEY") or _env("AWS_SECRET_ACCESS_KEY", "minio123")

    ssl_default = "true" if endpoint.lower().startswith("https://") else "false"
    ssl_raw = _env("S3A_SSL_ENABLED", ssl_default)
    ssl_enabled = ssl_raw.lower() in ("1", "true", "yes")

    builder = (
        SparkSession.builder.appName("Demo-1-DeltaLake-Foundation")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.endpoint", endpoint)
        .config("spark.hadoop.fs.s3a.access.key", access_key)
        .config("spark.hadoop.fs.s3a.secret.key", secret_key)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(ssl_enabled).lower())
        .config("spark.hadoop.fs.s3a.connection.maximum", "100")
        .config("spark.hadoop.fs.s3a.threads.max", "20")
        .config("spark.hadoop.fs.s3a.connection.timeout", "300000")
        .config("spark.hadoop.fs.s3a.connection.establish.timeout", "5000")
        .config("spark.hadoop.fs.s3a.readahead.range", "256K")
        .config("spark.hadoop.fs.s3a.fast.upload", "true")
        .config("spark.hadoop.fs.s3a.fast.upload.buffer", "disk")
        .config("spark.hadoop.fs.s3a.multipart.size", "64M")
        .config("spark.hadoop.fs.s3a.multipart.threshold", "64M")
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2")
        .config("spark.hadoop.fs.s3a.committer.name", "directory")
        .config("spark.sql.parquet.filterPushdown", "true")
        .config("spark.sql.parquet.mergeSchema", "false")
        .config("spark.sql.parquet.columnarReaderBatchSize", "4096")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    )

    jars = _env("SPARK_JARS_PACKAGES")
    if jars:
        builder = builder.config("spark.jars.packages", jars)

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def table_creation_api(spark):
    """Demo: Creating Delta Lake tables using DataFrame API"""

    p = paths()
    restaurants_df = spark.read.json(p["restaurants_read"])

    print(f"✅ Loaded {restaurants_df.count()} restaurants from {p['restaurants_read']}")
    restaurants_df.show(3, truncate=False)

    lk_restaurants_path = p["bronze_restaurants"]
    restaurants_df.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(lk_restaurants_path)

    lk_restaurants_df = spark.read.format("delta").load(lk_restaurants_path)
    print(f"✅ Delta table created with {lk_restaurants_df.count()} records at {lk_restaurants_path}")
    lk_restaurants_df.select("name", "cuisine_type", "city", "average_rating").show(5)

    return lk_restaurants_df


def table_creation_sql(spark):
    """Demo: Creating Delta Lake tables using Spark SQL"""

    p = paths()
    drivers_df = spark.read.json(p["drivers_read"])

    drivers_df.createOrReplaceTempView("vw_drivers")

    lk_drivers_path = p["bronze_drivers"]

    spark.sql(f"""
        CREATE OR REPLACE TABLE drivers
        USING DELTA
        LOCATION '{lk_drivers_path}'
        AS SELECT 
            driver_id,
            first_name,
            last_name,
            license_number,
            vehicle_type,
            vehicle_make,
            vehicle_model,
            vehicle_year,
            city,
            country,
            date_birth,
            phone_number,
            uuid,
            dt_current_timestamp
        FROM vw_drivers
    """)

    result = spark.sql("""
        SELECT 
            vehicle_type,
            COUNT(*) as driver_count,
            AVG(vehicle_year) as avg_vehicle_year
        FROM drivers 
        GROUP BY vehicle_type 
        ORDER BY driver_count DESC
    """)

    print("🔍 Drivers by vehicle type:")
    result.show()

    return spark.read.format("delta").load(lk_drivers_path)


def read_write_operations(spark):
    """Demo: Delta Lake read and write operations"""

    p = paths()
    orders_df = spark.read.json(p["orders_read"])

    lk_orders_path = p["bronze_orders"]

    print("💾 Writing orders with OVERWRITE mode...")
    orders_df.write \
        .format("delta") \
        .mode("overwrite") \
        .save(lk_orders_path)

    initial_count = spark.read.format("delta").load(lk_orders_path).count()
    print(f"✅ Initial record count: {initial_count}")

    print("➕ Appending new orders...")
    new_orders_df = orders_df.limit(10).withColumn("total_amount", col("total_amount") + 100)

    new_orders_df.write \
        .format("delta") \
        .mode("append") \
        .save(lk_orders_path)

    final_count = spark.read.format("delta").load(lk_orders_path).count()
    print(f"✅ Final record count after append: {final_count}")

    filtered_df = spark.read.format("delta").load(lk_orders_path).filter(col("total_amount") > 100)

    print(f"📈 Orders with amount > 100: {filtered_df.count()}")

    return spark.read.format("delta").load(lk_orders_path)


def parquet_to_delta_conversion(spark):
    """Demo: Converting Parquet to Delta Lake format using CONVERT TO DELTA"""

    p = paths()
    users_df = spark.read.json(p["users_read"])

    parquet_users_path = p["parquet_users"]
    print("📁 Creating Parquet table...")
    users_df.write \
        .format("parquet") \
        .mode("overwrite") \
        .save(parquet_users_path)

    lk_users_path = p["bronze_users"]
    print("🔄 Converting Parquet to Delta Lake using CONVERT TO DELTA...")

    spark.sql(f"""
        CONVERT TO DELTA parquet.`{parquet_users_path}`
    """)

    print("🔄 Alternative: Converting with new location...")
    spark.sql(f"""
        CREATE OR REPLACE TABLE users
        USING DELTA
        LOCATION '{lk_users_path}'
        AS SELECT * FROM parquet.`{parquet_users_path}`
    """)

    lk_users_df = spark.read.format("delta").load(lk_users_path)
    print(f"✅ Converted {lk_users_df.count()} users to Delta format")
    lk_users_df.select("user_id", "email", "city", "country").show(5)

    print("\n📊 Comparison:")
    print(f"Original Parquet files: {parquet_users_path}")
    print(f"Converted Delta table: {lk_users_path}")

    return lk_users_df


def table_metadata_exploration(spark):
    """Demo: Exploring Delta Lake table metadata"""

    lk_restaurants_path = paths()["bronze_restaurants"]
    delta_table = DeltaTable.forPath(spark, lk_restaurants_path)

    print("📜 Delta table history:")
    delta_table.history().select("version", "timestamp", "operation", "operationMetrics").show(truncate=False)

    print("📋 Delta table details:")
    spark.sql(f"DESCRIBE DETAIL delta.`{lk_restaurants_path}`").show(truncate=False)

    return delta_table


def main():
    """Main execution function"""

    spark = spark_session()

    table_creation_api(spark)
    table_metadata_exploration(spark)

    # table_creation_sql(spark)
    # read_write_operations(spark)
    # parquet_to_delta_conversion(spark)

    spark.stop()


if __name__ == "__main__":
    main()

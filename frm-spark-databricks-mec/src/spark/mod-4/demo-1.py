"""
Demo 1: Delta Lake Foundation & Setup
==================================

MinIO ports (typical):
  - 9090 = Web Console only (browser) — do NOT use for Spark S3A.
  - 9000 = S3 API — use this for fs.s3a.endpoint (kubectl port-forward svc/... 9000:9000).

Environment (optional):
  S3A_ENDPOINT            If unset: inside Docker -> http://host.docker.internal:9000
                            (MinIO API port-forwarded on the host). Otherwise localhost:9000.
                            Override for in-cluster Spark: http://datalake-hl.deepstore:9000
                            Linux Docker without host.docker.internal: http://172.17.0.1:9000
  S3A_ACCESS_KEY / S3A_SECRET_KEY  or AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
                            default minio / minio123
  DEMO1_SHADOW_BUCKET     default owshq-shadow-traffic-uber-eats
  DEMO1_LAKEHOUSE_BUCKET  default owshq-uber-eats-lakehouse (create empty in MinIO)

Reads use directory prefixes (trailing /) so any JSONL under that path works.

Run (Docker Compose Spark + kubectl port-forward ... 9000:9000 on the host):
  docker exec -it spark-master /opt/bitnami/spark/bin/spark-submit \\
    --master spark://spark-master:7077 \\
    /opt/bitnami/spark/jobs/spark/mod-4/demo-1.py
"""

import os

from pyspark.sql import SparkSession


def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def _default_s3a_endpoint() -> str:
    """MinIO S3 API URL. localhost inside a container is wrong for host port-forwards."""
    explicit = _env("S3A_ENDPOINT")
    if explicit:
        return explicit
    if os.path.exists("/.dockerenv"):
        return "http://host.docker.internal:9000"
    return "http://localhost:9000"


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

    endpoint = _default_s3a_endpoint()
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



def main():
    """Main execution function"""

    spark = spark_session()
    try:
        table_creation_api(spark)
    finally:
        spark.stop()

if __name__ == "__main__":
    main()

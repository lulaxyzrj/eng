"""
Demo 1: Delta Lake Foundation & Setup
==================================

This demo covers:
- Delta Lake + Spark Setup
- Spark Session Configuration
- Table Creation (DataFrame API & Spark SQL)
- Read & Write Operations
- Converting Parquet to Delta Lake Tables

Run command:
docker exec -it spark-master /opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  /opt/bitnami/spark/jobs/spark/mod-4/d1.py
"""

import base64
from pdb import main
from pyspark.sql import SparkSession
from delta.tables import DeltaTable
from pyspark.sql.functions import col, current_timestamp


def spark_session():
    """Create Spark Session with Delta Lake and MinIO S3 configurations"""

    encoded_access_key = "bWluaW9sYWtl"
    encoded_secret_key = "TGFrRTE0MjUzNkBA"
    access_key = base64.b64decode(encoded_access_key).decode('utf-8')
    secret_key = base64.b64decode(encoded_secret_key).decode('utf-8')

    spark = SparkSession.builder \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://24.144.65.249:80") \
        .config("spark.hadoop.fs.s3a.access.key", access_key) \
        .config("spark.hadoop.fs.s3a.secret.key", secret_key) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.connection.maximum", "100") \
        .config("spark.hadoop.fs.s3a.threads.max", "20") \
        .config("spark.hadoop.fs.s3a.connection.timeout", "300000") \
        .config("spark.hadoop.fs.s3a.connection.establish.timeout", "5000") \
        .config("spark.hadoop.fs.s3a.readahead.range", "256K") \
        .config("spark.hadoop.fs.s3a.fast.upload", "true") \
        .config("spark.hadoop.fs.s3a.fast.upload.buffer", "disk") \
        .config("spark.hadoop.fs.s3a.multipart.size", "64M") \
        .config("spark.hadoop.fs.s3a.multipart.threshold", "64M") \
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2") \
        .config("spark.hadoop.fs.s3a.committer.name", "directory") \
        .config("spark.sql.parquet.filterPushdown", "true") \
        .config("spark.sql.parquet.mergeSchema", "false") \
        .config("spark.sql.parquet.columnarReaderBatchSize", "4096") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    return spark


def table_creation_api(spark):
    """Demo: Creating Delta Lake tables using DataFrame API"""

    restaurants_path = "s3a://owshq-shadow-traffic-uber-eats/mysql/restaurants/01JTKHGDFWAZPJ8BDQRHCGVPD3.jsonl"
    restaurants_df = spark.read.json(restaurants_path)

    print(f"✅ Loaded {restaurants_df.count()} restaurants")
    restaurants_df.show(3, truncate=False)

    lk_restaurants_path = "s3a://owshq-uber-eats-lakehouse/bronze/restaurants"
    restaurants_df.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(lk_restaurants_path)

    lk_restaurants_df = spark.read.format("delta").load(lk_restaurants_path)
    print(f"✅ Delta table created with {lk_restaurants_df.count()} records")
    lk_restaurants_df.select("name", "cuisine_type", "city", "average_rating").show(5)

    return lk_restaurants_df


    def main():
    spark = spark_session()
    part_1_table_creation_api = table_creation_api(spark)

    spark.stop()

if __name__ == "__main__":
    main()
    
    



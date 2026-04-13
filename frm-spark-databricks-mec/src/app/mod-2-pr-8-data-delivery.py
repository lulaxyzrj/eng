"""
docker exec -it spark-master /opt/bitnami/spark/bin/spark-submit --master 'local[*]' --deploy-mode client /opt/bitnami/spark/jobs/app/mod-2-pr-8-data-delivery.py

Use --master 'local[*]' (not spark://spark-master:7077) when writing to
file:/opt/bitnami/spark/storage. In standalone cluster mode, executors run on
workers and all try to mkdir/commit under the same file: path; bind mounts
often still fail with Mkdirs/IOException even if the host dir is 777. Local
mode runs the job in the spark-master process only, so writes go to the
mounted storage from a single JVM.

Paths use /opt/bitnami/spark/storage (build/docker-compose.yml: APP_STORAGE_PATH).
"""

import shutil
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import Column
from pyspark.sql.functions import col, regexp_replace, round, sqrt, to_timestamp, year, month


def path_safe_partition_key(c: Column) -> Column:
    """Hive partition folder names must be encodable as JVM paths; strip non-ASCII and path chars."""
    s = regexp_replace(c, "/", "_")
    return regexp_replace(s, r"[^\p{ASCII}]", "_")

STORAGE_ROOT = "/opt/bitnami/spark/storage"
OUTPUT_ROOT = f"{STORAGE_ROOT}/output"

spark = SparkSession.builder \
    .getOrCreate()

restaurants_df = spark.read.json(f"{STORAGE_ROOT}/mysql/restaurants/01JS4W5A7YWTYRQKDA7F7N95VY.jsonl")
drivers_df = spark.read.json(f"{STORAGE_ROOT}/postgres/drivers/01JS4W5A74BK7P4BPTJV1D3MHA.jsonl")
orders_df = spark.read.json(f"{STORAGE_ROOT}/kafka/orders/01JS4W5A7XY65S9Z69BY51BEJ4.jsonl")

restaurant_analytics = restaurants_df.select(
    "name", "cuisine_type", "city", "country", "average_rating", "num_reviews"
).withColumn(
    "popularity_score",
    round(col("average_rating") * sqrt(col("num_reviews") / 1000), 2)
)

print("Restaurant Analytics:")
restaurant_analytics.show(5)

# TODO 1. write file formats
restaurant_analytics.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(f"{OUTPUT_ROOT}/csv")

restaurant_analytics.write \
    .mode("overwrite") \
    .json(f"{OUTPUT_ROOT}/json")

restaurant_analytics.write \
    .mode("overwrite") \
    .parquet(f"{OUTPUT_ROOT}/parquet")

restaurant_analytics.write \
    .mode("overwrite") \
    .orc(f"{OUTPUT_ROOT}/orc")

# TODO 2. write modes (errorIfExists fails if the output dir exists — remove it so re-runs work)
_errorifexists_out = Path(f"{OUTPUT_ROOT}/errorifexists")
if _errorifexists_out.exists():
    shutil.rmtree(_errorifexists_out)

restaurant_analytics.write.mode("errorifexists").parquet(f"{OUTPUT_ROOT}/errorifexists")
restaurant_analytics.write.mode("overwrite").parquet(f"{OUTPUT_ROOT}/overwrite")
restaurant_analytics.write.mode("append").parquet(f"{OUTPUT_ROOT}/append")

# TODO = file-system-level, not data-content-level
restaurant_analytics.write.mode("ignore").parquet(f"{OUTPUT_ROOT}/ignore")

# TODO 3. compression options
restaurant_analytics.write.mode("overwrite").option("compression", "gzip").parquet(f"{OUTPUT_ROOT}/gzip")
restaurant_analytics.write.mode("overwrite").option("compression", "snappy").parquet(f"{OUTPUT_ROOT}/snappy")
restaurant_analytics.write.mode("overwrite").option("compression", "zstd").parquet(f"{OUTPUT_ROOT}/zstd")
restaurant_analytics.write.mode("overwrite").option("compression", "none").parquet(f"{OUTPUT_ROOT}/none")

# TODO 4. partitioning data (use ASCII-safe keys — accented city names break Java Paths in partition dirs)
by_cuisine = restaurant_analytics.withColumn(
    "cuisine_part", path_safe_partition_key(col("cuisine_type"))
)
by_cuisine.write.mode("overwrite").partitionBy("cuisine_part").parquet(f"{OUTPUT_ROOT}/by_cuisine")

by_location = restaurant_analytics.withColumn(
    "country_part", path_safe_partition_key(col("country"))
).withColumn(
    "city_part", path_safe_partition_key(col("city"))
)
by_location.write.mode("overwrite").partitionBy("country_part", "city_part").parquet(f"{OUTPUT_ROOT}/by_location")

# TODO 5. controlling file sizes
restaurant_analytics.write.mode("overwrite").parquet(f"{OUTPUT_ROOT}/default")
restaurant_analytics.repartition(2).write.mode("overwrite").parquet(f"{OUTPUT_ROOT}/repartitioned")
restaurant_analytics.coalesce(1).write.mode("overwrite").parquet(f"{OUTPUT_ROOT}/coalesced")
restaurant_analytics.repartition(1).write.mode("overwrite").option("maxRecordsPerFile", 100).parquet(f"{OUTPUT_ROOT}/records")

# TODO 6. time-based partitioning
orders_with_time = orders_df.withColumn(
    "order_timestamp",
    to_timestamp("order_date")
).withColumn(
    "year", year("order_timestamp")
).withColumn(
    "month", month("order_timestamp")
)

orders_with_time.write \
    .mode("overwrite") \
    .partitionBy("year", "month") \
    .parquet(f"{OUTPUT_ROOT}/orders_by_time")

spark.stop()

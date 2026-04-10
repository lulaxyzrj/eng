"""
docker exec -it spark-master /opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  /opt/bitnami/spark/jobs/app/mod-2-p18.py
"""

from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.sql.warehouse.dir", "file:/tmp/warehouse") \
    .config("spark.local.dir", "/tmp/spark-temp") \
    .getOrCreate()

print("spark.sql.warehouse.dir is set to:", spark.conf.get("spark.sql.warehouse.dir"))
# TODO set config
spark.sparkContext.setLogLevel("ERROR")
spark.sql("SET spark.sql.echo=true")
spark.conf.set("spark.sql.legacy.allowNonEmptyLocationInCTAS", "true")

spark.sql("""
CREATE OR REPLACE TEMPORARY VIEW restaurants_temp
USING json
OPTIONS (path "./storage/mysql/restaurants/01JS4W5A7YWTYRQKDA7F7N95VY.jsonl")
""")

spark.sql("""
CREATE OR REPLACE TEMPORARY VIEW drivers_temp
USING json
OPTIONS (path "./storage/postgres/drivers/01JS4W5A74BK7P4BPTJV1D3MHA.jsonl")
""")

spark.sql("""
CREATE OR REPLACE TEMPORARY VIEW orders_temp
USING json
OPTIONS (path "./storage/kafka/orders/01JS4W5A7XY65S9Z69BY51BEJ4.jsonl")
""")


# TODO 1. creating permanent tables

spark.sql("CREATE DATABASE IF NOT EXISTS analytics")  
spark.sql("USE analytics")  


#spark.sql("""
#CREATE TABLE  IF NOT EXISTS restaurants
##USING PARQUET
#AS SELECT * FROM restaurants_temp
#""")

#spark.sql("""
##CREATE TABLE IF NOT EXISTS restaurant_summary
#USING PARQUET
#AS
#SELECT
#    restaurant_id,
#    name,
#    cuisine_type,
##    city,
#    average_rating,
#    num_reviews,
#    average_rating * LOG(10, GREATEST(num_reviews, 10)) AS popularity_score
#FROM restaurants_temp
#""")

spark.sql("SHOW TABLES IN analytics").show()
#spark.sql("DESCRIBE FORMATTED analytics.restaurants").show(10, truncate=False)

#todo 2  managed vs external tables

spark.sql("""
CREATE TABLE IF NOT EXISTS managed_orders
USING PARQUET
AS SELECT * FROM orders_temp
""")

orders_path = "/tmp/warehouse/external_orders"

spark.sql("SELECT * FROM orders_temp").write \
     .format("parquet") \
    .mode("overwrite") \
    .save(orders_path)

spark.sql("""
CREATE EXTERNAL TABLE IF NOT EXISTS external_orders
USING PARQUET
LOCATION '{orders_path}'
""")

spark.stop()

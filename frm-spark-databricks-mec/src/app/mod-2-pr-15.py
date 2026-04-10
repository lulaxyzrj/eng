"""
docker exec -it spark-master /opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  /opt/bitnami/spark/jobs/app/mod-2-pr-14.py
"""

from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.sql.warehouse.dir", "/opt/bitnami/spark/jobs/app/warehouse") \
    .getOrCreate()

# TODO set config
spark.sparkContext.setLogLevel("ERROR")
spark.sql("SET spark.sql.echo=true")

# TODO 1. read data using SQL
spark.sql("""
CREATE OR REPLACE TEMPORARY VIEW restaurants
USING json
OPTIONS (path "./storage/mysql/restaurants/01JS4W5A7YWTYRQKDA7F7N95VY.jsonl")
""")

spark.sql("""
CREATE OR REPLACE TEMPORARY VIEW drivers
USING json
OPTIONS (path "./storage/postgres/drivers/01JS4W5A74BK7P4BPTJV1D3MHA.jsonl")
""")

spark.sql("""
CREATE OR REPLACE TEMPORARY VIEW orders
USING json
OPTIONS (path "./storage/kafka/orders/01JS4W5A7XY65S9Z69BY51BEJ4.jsonl")
""")

restaurants_count = spark.sql("SELECT COUNT(*) as restaurant_count FROM restaurants")
drivers_count = spark.sql("SELECT COUNT(*) as driver_count FROM drivers")
orders_count = spark.sql("SELECT COUNT(*) as order_count FROM orders")

restaurants_count.show()
drivers_count.show()
orders_count.show()

spark.sql("DESCRIBE restaurants").show(10, truncate=False)
spark.sql("SELECT * FROM restaurants LIMIT 5").show(truncate=False)


#TODO 2 querying data using SQL

spark.sql("""
SELECT name,cuisine_type,city, average_rating
FROM restaurants
WHERE average_rating > 4.0
ORDER BY average_rating DESC
LIMIT 5
""").show()

spark.sql("""
SELECT cuisine_type,COUNT(*) as restaurant_count
FROM restaurants
GROUP BY cuisine_type
ORDER BY restaurant_count DESC
LIMIT 5
""").show()

spark.sql("""
SELECT city,COUNT(*) as restaurant_count
FROM restaurants
GROUP BY city
ORDER BY restaurant_count DESC
LIMIT 5
""").show()

#TODO 3: creating temporary and permanent objects 

spark.sql("""
CREATE OR REPLACE GLOBAL TEMPORARY VIEW global_restaurants 
AS
SELECT * FROM restaurants
""")



spark.sql(""" CREATE DATABASE IF NOT EXISTS ubereats""")

spark.sql(""" DROP TABLE IF EXISTS ubereats.restaurants""")
spark.sql(""" DROP TABLE IF EXISTS ubereats.drivers""")
spark.sql(""" DROP TABLE IF EXISTS ubereats.orders""")

#TODO 4: creating managed and external tables

spark.conf.set("spark.sql.legacy.allowNonEmptyLocationInCTAS", "true")
print(spark.conf.get("spark.sql.legacy.allowNonEmptyLocationInCTAS"))

spark.sql("""
CREATE EXTERNAL TABLE ubereats.restaurants
USING  parquet
LOCATION "/tmp/1/restaurants"
AS
SELECT * FROM restaurants 
""")

spark.sql("""
CREATE EXTERNAL TABLE ubereats.drivers
USING  parquet
LOCATION "/tmp/1/drivers"
AS
SELECT * FROM drivers 
""")

spark.sql("""
CREATE EXTERNAL TABLE ubereats.orders
USING  parquet
LOCATION "/tmp/1/orders"
AS
SELECT * FROM orders 
""")

spark.sql("""
SELECT name,cuisine_type,city, average_rating
FROM ubereats.restaurants
WHERE num_reviews < 3000 
ORDER BY num_reviews DESC
LIMIT 5
""").show()

#tooo 4 
spark.sql("DESCRIBE restaurants").show(10)

spark.sql("""
CREATE OR REPLACE TEMPORARY VIEW rest_sch_type AS
SELECT
    CAST(restaurant_id AS INT) AS restaurant_id,
    name,
    cuisine_type,
    city,
    country,
    CAST(average_rating AS DOUBLE) AS average_rating,
    CAST(num_reviews AS INT) AS num_reviews,
    cnpj,
    address,
    opening_time,
    closing_time,
    phone_number,
    uuid,
    dt_current_timestamp
FROM restaurants
""")

spark.sql("DESCRIBE rest_sch_type").show(10)

spark.sql("DROP TABLE IF EXISTS ubereats.rest_sch_type")

spark.sql("""
CREATE EXTERNAL TABLE ubereats.rest_sch_type
USING parquet
LOCATION '/tmp/rest_sch_type'
AS SELECT * FROM rest_sch_type
""")

# TODO 5. exploring catalog with sql
spark.sql("SHOW DATABASES").show()

spark.sql("SHOW TABLES IN ubereats").show()

spark.sql("SHOW TBLPROPERTIES ubereats.restaurants").show(truncate=False)

spark.sql("SHOW COLUMNS IN ubereats.restaurants").show()

spark.sql("SHOW CREATE TABLE ubereats.restaurants").show(truncate=False)

spark.stop()


spark.stop()

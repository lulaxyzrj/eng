"""
docker exec -it spark-master /opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  /opt/bitnami/spark/jobs/app/mod-2-pr-16.py
"""

from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .getOrCreate()

# TODO set config
spark.sparkContext.setLogLevel("ERROR")
spark.sql("SET spark.sql.echo=true")

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

# TODO 1. advanced join operations
print("Inner Join:")
spark.sql("""
SELECT 
    o.order_id,
    r.name AS restaurant_name,
    r.cuisine_type,
    o.total_amount
FROM orders o
INNER JOIN restaurants r ON o.restaurant_key = r.cnpj
LIMIT 5
""").show()
print("Left Join:")
spark.sql("""
SELECT 
    r.name,
    r.cuisine_type,
    COUNT(o.order_id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS total_revenue
FROM restaurants r
LEFT JOIN orders o ON r.cnpj = o.restaurant_key
GROUP BY r.name, r.cuisine_type
ORDER BY order_count DESC
LIMIT 5
""").show()
print("Right Join:")
spark.sql("""
SELECT 
    o.order_id,
    o.total_amount,
    r.name AS restaurant_name
FROM restaurants r
RIGHT JOIN orders o ON r.cnpj = o.restaurant_key
LIMIT 5
""").show()
print("Full Outer Join:")
spark.sql("""
SELECT 
    r.name,
    o.order_id,
    o.total_amount
FROM restaurants r
FULL OUTER JOIN orders o ON r.cnpj = o.restaurant_key
LIMIT 5
""").show()
print("Cross Join:")
spark.sql("""
SELECT 
    o.order_id,
    r.name AS restaurant_name,
    r.cuisine_type,
    CONCAT(d.first_name, ' ', d.last_name) AS driver_name,
    d.vehicle_type,
    o.total_amount
FROM orders o
JOIN restaurants r ON o.restaurant_key = r.cnpj
JOIN drivers d ON o.driver_key = d.license_number
LIMIT 5
""").show()

# TODO 2. subqueries for complex logic

spark.sql("""
SELECT 
    o.order_id,
    r.name AS restaurant_name,
    r.cuisine_type,
    CONCAT(d.first_name, ' ', d.last_name) AS driver_name,
    d.vehicle_type,
    o.total_amount
FROM orders o
JOIN restaurants r ON o.restaurant_key = r.cnpj
JOIN drivers d ON o.driver_key = d.license_number
LIMIT 5
""").show()

spark.sql("""
SELECT 
    name,
    cuisine_type,
    city,
    average_rating
FROM restaurants r
WHERE (cuisine_type, average_rating) IN (
    SELECT 
        cuisine_type, 
        MAX(average_rating) AS max_rating
    FROM restaurants
    GROUP BY cuisine_type
)
ORDER BY average_rating DESC
LIMIT 5
""").show()

spark.sql("""
SELECT
    cs.cuisine_type,
    cs.restaurant_count,
    cs.avg_rating,
    COUNT(o.order_id) AS order_count,
    ROUND(SUM(o.total_amount), 2) AS total_revenue
FROM (
    SELECT
        cuisine_type,
        COUNT(*) AS restaurant_count,
        ROUND(AVG(average_rating), 2) AS avg_rating
    FROM restaurants
    GROUP BY cuisine_type
) cs
LEFT JOIN restaurants r ON r.cuisine_type = cs.cuisine_type
LEFT JOIN orders o ON o.restaurant_key = r.cnpj
GROUP BY cs.cuisine_type, cs.restaurant_count, cs.avg_rating
ORDER BY total_revenue DESC
LIMIT 5
""").show()

# TODO 3. window functions
print("Top 10 restaurants by average rating per cuisine type: Ordena decrescente pelo average_rating dentro de cuuisine_type" )
spark.sql("""
SELECT * FROM (
    SELECT
        name,
        cuisine_type,
        city,
        average_rating,
        DENSE_RANK() OVER (PARTITION BY cuisine_type ORDER BY average_rating DESC) AS rank
    FROM restaurants
) ranked
WHERE rank <= 3
ORDER BY cuisine_type, rank
LIMIT 10
""").show()
print("Top 10 restaurants with average rating and rank within cuisine type and city:")
spark.sql("""
SELECT
    name,
    cuisine_type,
    city,
    average_rating,
    num_reviews,
    ROUND(average_rating, 2) AS rating,
    ROUND(AVG(average_rating) OVER (PARTITION BY cuisine_type), 2) AS cuisine_avg_rating,
    ROUND(average_rating - AVG(average_rating) OVER (PARTITION BY cuisine_type), 2) AS diff_from_cuisine_avg,
    RANK() OVER (PARTITION BY cuisine_type ORDER BY average_rating DESC) AS cuisine_rank,
    RANK() OVER (PARTITION BY city ORDER BY average_rating DESC) AS city_rank
FROM restaurants
ORDER BY cuisine_type, cuisine_rank
LIMIT 10
""").show()
print("Top 5 cities with most restaurants and cumulative percentage:")
spark.sql("""
SELECT
    city,
    COUNT(*) AS restaurant_count,
    SUM(COUNT(*)) OVER (ORDER BY COUNT(*) DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total,
    ROUND(SUM(COUNT(*)) OVER (ORDER BY COUNT(*) DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / 
          SUM(COUNT(*)) OVER () * 100, 2) AS cumulative_percentage
FROM restaurants
GROUP BY city
ORDER BY restaurant_count DESC
LIMIT 5
""").show()
print("Calculating rating difference with LAG function:")
spark.sql("""
SELECT
    cuisine_type,
    name,
    average_rating,
    LAG(average_rating, 1) OVER (PARTITION BY cuisine_type ORDER BY average_rating DESC) AS prev_rating,
    average_rating - LAG(average_rating, 1) OVER (PARTITION BY cuisine_type ORDER BY average_rating DESC) AS rating_diff
FROM restaurants
ORDER BY cuisine_type, average_rating DESC
LIMIT 10
""").show()

spark.stop()
"""
docker exec -it spark-master /opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  /opt/bitnami/spark/jobs/app/mod-2-pr-20-postgres-integration.py

-------------------
-------------------
JDBC & Partitioning
column = "total_deliveries"
lowerBound = 0
upperBound = 1000
numPartitions = 4

SELECT * FROM drivers WHERE total_deliveries >= 0 AND total_deliveries < 250
SELECT * FROM drivers WHERE total_deliveries >= 250 AND total_deliveries < 500
SELECT * FROM drivers WHERE total_deliveries >= 500 AND total_deliveries < 750
SELECT * FROM drivers WHERE total_deliveries >= 750 AND total_deliveries <= 1000
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, DateType
from pyspark.sql.functions import col, round
from pyspark.sql import Row

spark = SparkSession.builder \
    .getOrCreate()

# TODO configs
spark.sparkContext.setLogLevel("ERROR")

# TODO configure PostgreSQL connection
pg_host = "159.203.159.29"
pg_port = "5432"
pg_database = "postgres"
pg_user = "postgres"
pg_password = "6e8e5979-25c5-44e2-ad76-7a4e8ee68c6f"

jdbc_url = f"jdbc:postgresql://{pg_host}:{pg_port}/{pg_database}"

connection_properties = {
    "user": pg_user,
    "password": pg_password,
    "driver": "org.postgresql.Driver"
}

# TODO test PostgreSQL connection
try:
    test_df = spark.read.jdbc(
        url=jdbc_url,
        table="(SELECT 1 as test) AS test",
        properties=connection_properties
    )
    test_df.show()
    print("PostgreSQL connection successfully established!")
except Exception as e:
    print(f"Error connecting to PostgreSQL: {str(e)}")


# TODO set schema
drivers_schema = StructType([
    StructField("license_plate", StringType(), True),
    StructField("phone_number", StringType(), True),
    StructField("last_login", DateType(), True),
    StructField("email", StringType(), True),
    StructField("average_rating", FloatType(), True),
    StructField("name", StringType(), True),
    StructField("total_earnings", FloatType(), True),
    StructField("status", StringType(), True),
    StructField("registration_date", DateType(), True),
    StructField("driver_id", StringType(), False),
    StructField("total_deliveries", IntegerType(), True),
    StructField("vehicle_type", StringType(), True)
])

print("Schema of the 'drivers' table:")
for field in drivers_schema:
    print(f"  - {field.name}: {field.dataType}")


spark.stop()

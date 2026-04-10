# Databricks notebook source
import dlt
from pyspark.sql.functions import *

# Simulando uma fonte de dados de alta cardinalidade para gerar carga
@dlt.table(
  name="raw_traffic_data",
  comment="Dados brutos de tráfego simulados para teste de scaling"
)
def raw_traffic_data():
    return (
        spark.readStream
        .format("rate")
        .option("rowsPerSecond", 5000) # Carga inicial alta
        .load()
    )

@dlt.table(
  name="refined_traffic",
  comment="Limpeza e processamento pesado para forçar uso de slots"
)
def refined_traffic():
    return (
        dlt.read_stream("raw_traffic_data")
        .withColumn("processing_time", current_timestamp())
        .withColumn("complex_hash", sha2(col("value").cast("string"), 256))
    )
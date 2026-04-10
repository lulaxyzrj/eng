# Databricks notebook source
# MAGIC %md
# MAGIC # Disk Cache: ML Training Demo
# MAGIC
# MAGIC **Objetivo:** Demonstrar disk cache em ML training (múltiplas épocas).
# MAGIC
# MAGIC **Conceito:** SSD local armazena dados do cloud storage. Leituras repetidas vêm do SSD (0 latência).
# MAGIC
# MAGIC **Lab:**
# MAGIC * Dataset: `sandbox.default.spill_demo_raw` (7.7 GB)
# MAGIC * Modelo: LogisticRegression (3 épocas)
# MAGIC * Ganho esperado: 20-40% nas épocas 2-3
# MAGIC
# MAGIC **Requisito:** Cluster com SSD local + SINGLE_USER mode (MLlib).

# COMMAND ----------

from pyspark.ml.classification import LogisticRegression
from pyspark.ml.feature import VectorAssembler
import time

# COMMAND ----------

spark.conf.set("spark.databricks.io.cache.enabled", True)

# COMMAND ----------

# 1. Configuração e Preparação (Caminho da sua tabela de 7.7GB)
table_path = "sandbox.default.spill_demo_raw"
df = spark.read.table(table_path)

# Preparando features básicas para o modelo
assembler = VectorAssembler(inputCols=["group_key", "id"], outputCol="features")
training_data = assembler.transform(df).select("features", df.group_key.alias("label"))

# 2. Definição do Modelo
lr = LogisticRegression(maxIter=1, regParam=0.01) # 1 iter por chamada para controlar o loop

# 3. Simulação de Épocas (Onde a mágica do Disk Cache acontece)
num_epochs = 3
results = []

for epoch in range(1, num_epochs + 1):
    print(f"Iniciando Época {epoch}...")
    start_time = time.time()
    
    # O comando .fit() força a leitura completa do dataset
    model = lr.fit(training_data)
    
    end_time = time.time()
    duration = end_time - start_time
    results.append(duration)
    print(f"Duração da Época {epoch}: {duration:.2f} segundos")

# 4. Resumo da Melhoria
print(f"\nGanho de Performance: Época 1 (Fria) vs Época 2+ (Morna)")
print(f"Época 1: {results[0]:.2f}s (Popula o SSD)")
print(f"Época 2: {results[1]:.2f}s (Lido do SSD Local)")
print(f"Época 3: {results[2]:.2f}s (Lido do SSD Local)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Resultados
# MAGIC
# MAGIC | Época | Duração | Fonte | Ganho |
# MAGIC |-------|----------|-------|-------|
# MAGIC | 1 (cold) | 105.7s | Cloud storage | Baseline |
# MAGIC | 2 (warm) | 74.4s | SSD local | **30%** |
# MAGIC | 3 (warm) | 73.8s | SSD local | **30%** |
# MAGIC
# MAGIC **Economia:** 31s por época.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Conclusão
# MAGIC
# MAGIC **Disk cache melhorou 30%:**
# MAGIC * Época 1: Popula SSD (105.7s)
# MAGIC * Épocas 2-3: Lê do SSD (74s)
# MAGIC
# MAGIC **Spark UI:** Verifique `cache hits` > 0 nas épocas 2-3.
# MAGIC
# MAGIC **Quando usar:**
# MAGIC * ML training (múltiplas épocas)
# MAGIC * Dashboards (queries repetitivas)
# MAGIC * EDA (explorar mesmo dataset)
# MAGIC
# MAGIC **Ganho típico:** 20-40% em workloads repetitivos.
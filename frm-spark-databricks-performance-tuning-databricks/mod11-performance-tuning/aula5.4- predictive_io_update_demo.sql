-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Photon MERGE Performance Demo
-- MAGIC
-- MAGIC **Objetivo:** Comparar MERGE sem Photon vs com Photon.
-- MAGIC
-- MAGIC **Photon:**
-- MAGIC * Engine C++ nativo (vs Spark JVM)
-- MAGIC * Processamento vetorizado
-- MAGIC * Otimização de deletion vectors
-- MAGIC
-- MAGIC **Lab:**
-- MAGIC * Target: `sandbox.default.spill_demo_raw` (5M registros, 7.7 GB)
-- MAGIC * Source: 2M registros (1M updates + 1M inserts)
-- MAGIC * Ganho esperado: 40-60%

-- COMMAND ----------

SET spark.databricks.photon.enabled

-- COMMAND ----------

-- Desabilitar Photon para estabelecer baseline
SET spark.databricks.photon.enabled = False

-- COMMAND ----------

-- Verificar estado da tabela
DESCRIBE DETAIL sandbox.default.spill_demo_raw

-- COMMAND ----------

-- DBTITLE 1,Criar Tabela Source (Updates + Inserts)
-- Source: 2M registros (1M updates + 1M inserts)
CREATE OR REPLACE TEMP VIEW merge_source AS
-- 1M UPDATES (IDs existentes 0-999999)
SELECT 
  id,
  group_key,
  CONCAT('UPDATED_V3_', payload) AS payload
FROM sandbox.default.spill_demo_raw
WHERE id < 1000000

UNION ALL

-- 1M INSERTS (IDs novos 5000000-5999999)
SELECT 
  id + 5000000 AS id,
  (id + 5000000) % 10 AS group_key,
  CONCAT('NEW_', REPEAT('X', 2700)) AS payload
FROM sandbox.default.spill_demo_raw
WHERE id < 1000000

-- COMMAND ----------

-- DBTITLE 1,Verify Table Creation
-- MERGE sem Photon (Baseline)
-- Photon já foi desabilitado na célula 6

MERGE INTO sandbox.default.spill_demo_raw AS target
USING merge_source AS source
ON target.id = source.id
WHEN MATCHED THEN 
  UPDATE SET 
    target.payload = source.payload,
    target.group_key = source.group_key
WHEN NOT MATCHED THEN 
  INSERT (id, group_key, payload) 
  VALUES (source.id, source.group_key, source.payload)

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Baseline: MERGE sem Photon
-- MAGIC
-- MAGIC **Output:** 1M updates + 1M inserts
-- MAGIC
-- MAGIC **Métricas (Scan parquet):**
-- MAGIC * `scan time`: **2.5s**
-- MAGIC * `cloud storage duration`: **10.8s**
-- MAGIC * `time spent reading deletion vectors total`: **3.6s**
-- MAGIC * `size read`: **2008 MiB**
-- MAGIC * `files read`: **50**
-- MAGIC
-- MAGIC **Gargalo:** 3.6s lendo deletion vectors (1M DV rows).

-- COMMAND ----------

-- DBTITLE 1,Habilitar Photon
-- Habilitar Photon para ativar Predictive I/O
SET spark.databricks.photon.enabled = True

-- COMMAND ----------

SET spark.databricks.photon.enabled

-- COMMAND ----------

-- Recriar source IDÊNTICA
CREATE OR REPLACE TEMP VIEW merge_source AS
SELECT 
  id,
  group_key,
  CONCAT('UPDATED_V3_', payload) AS payload
FROM sandbox.default.spill_demo_raw
WHERE id < 1000000

UNION ALL

SELECT 
  id + 6000000 AS id,
  (id + 6000000) % 10 AS group_key,
  CONCAT('NEW_', REPEAT('X', 2700)) AS payload
FROM sandbox.default.spill_demo_raw
WHERE id < 1000000

-- COMMAND ----------

-- MERGE com Photon (Predictive I/O ativo)
MERGE INTO sandbox.default.spill_demo_raw AS target
USING merge_source AS source
ON target.id = source.id
WHEN MATCHED THEN 
  UPDATE SET 
    target.payload = source.payload,
    target.group_key = source.group_key
WHEN NOT MATCHED THEN 
  INSERT (id, group_key, payload) 
  VALUES (source.id, source.group_key, source.payload)

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Comparação: Baseline vs Photon
-- MAGIC
-- MAGIC **Workload:** 1M updates + 1M inserts (~2 GiB scan)
-- MAGIC
-- MAGIC | Métrica | Baseline (Cél 6) | Photon (Cél 10) | Ganho |
-- MAGIC |---------|------------------|-----------------|-------|
-- MAGIC | **Scan type** | Scan parquet | PhotonScan | ✅ Photon ativo |
-- MAGIC | **Scan time / cumulative** | 2.5s | 1.5s | ✅ **40%** |
-- MAGIC | **Cloud storage duration** | 10.8s | 4.8s | ✅ **56%** |
-- MAGIC | **DV read time** | 3.6s | 1.3s | ✅ **64%** |
-- MAGIC | **Size read** | 2008 MiB | 2007 MiB | Igual |
-- MAGIC | **Files read** | 50 | 50 | Igual |
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ## Conclusão
-- MAGIC
-- MAGIC **Photon melhorou 40-64% via:**
-- MAGIC * Engine C++ vetorizado (vs Spark JVM)
-- MAGIC * Deletion vectors processados 64% mais rápido
-- MAGIC * Cloud storage 56% mais eficiente
-- MAGIC
-- MAGIC **Gargalo:** Deletion vectors (3.6s → 1.3s).
-- MAGIC
-- MAGIC **Boas práticas:**
-- MAGIC * Habilite Photon para MERGE/UPDATE/DELETE
-- MAGIC * Monitore `deletion vector read time` na Spark UI
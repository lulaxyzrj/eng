# Databricks notebook source
# MAGIC %md
# MAGIC # Simulação de Disk Spill no Spark
# MAGIC
# MAGIC Este notebook demonstra como forçar e observar o comportamento de **disk spill** no Apache Spark.
# MAGIC
# MAGIC ## O que é Disk Spill?
# MAGIC
# MAGIC Quando o Spark processa dados que não cabem na memória disponível (RAM), ele precisa escrever dados temporários em disco. Esse processo é chamado de **spill** e impacta significativamente a performance.
# MAGIC
# MAGIC ## Objetivo da Simulação
# MAGIC
# MAGIC * **Etapa 1**: Configurar Spark com otimizações habilitadas (baseline)
# MAGIC * **Etapa 2**: Gerar dataset grande (~4 GB) com alta entropia
# MAGIC * **Etapa 3**: Verificar características da tabela criada
# MAGIC * **Etapa 4**: Desabilitar otimizações e forçar gargalos de memória
# MAGIC * **Etapa 5**: Executar operação custosa (repartition + orderBy) para provocar spill
# MAGIC
# MAGIC ## Ambiente
# MAGIC
# MAGIC * **Cluster**: Single-node (0 workers) - toda execução no driver
# MAGIC * **Node Type**: Standard_D4s_v3 (4 cores, 16 GB RAM)
# MAGIC * **Dataset**: 2 milhões de linhas × 2 KB cada = ~4 GB de dados

# COMMAND ----------

# MAGIC %md
# MAGIC ## Etapa 1: Configuração Otimizada (Baseline)
# MAGIC
# MAGIC **Objetivo**: Estabelecer configurações que permitem ao Spark operar eficientemente.
# MAGIC
# MAGIC ### Configurações Aplicadas:
# MAGIC
# MAGIC * `spark.sql.shuffle.partitions = "auto"`: Permite ao Spark determinar automaticamente o número ideal de partições durante shuffles
# MAGIC * `spark.sql.adaptive.enabled = true`: Habilita Adaptive Query Execution (AQE), que otimiza o plano de execução dinamicamente
# MAGIC * `spark.sql.autoBroadcastJoinThreshold = 1`: Define threshold de 1 byte para broadcast joins (força broadcast de tabelas pequenas)
# MAGIC
# MAGIC **Resultado**: Spark pode usar todas as otimizações disponíveis para processar dados eficientemente.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Etapa 2: Geração de Dataset com Alta Entropia
# MAGIC
# MAGIC **Objetivo**: Criar uma tabela grande com dados que não comprimem bem, simulando cenários reais de alta cardinalidade.
# MAGIC
# MAGIC ### Parâmetros:
# MAGIC
# MAGIC * **ROWS**: 2.000.000 linhas
# MAGIC * **PAYLOAD_SIZE**: 2.048 bytes por linha (dados aleatórios em base64)
# MAGIC * **Volume Total**: ~4 GB de dados brutos
# MAGIC * **Tabela**: `sandbox.default.spill_demo_raw`
# MAGIC
# MAGIC ### Técnica de Geração:
# MAGIC
# MAGIC * **UDF customizada**: Gera strings aleatórias usando `os.urandom()` + `base64.encode()`
# MAGIC * **Alta entropia**: Dados aleatórios não comprimem eficientemente
# MAGIC * **Skew proposital**: `group_key` com distribuição desigual (rand() × 10) para simular data skew
# MAGIC
# MAGIC ### Colunas:
# MAGIC
# MAGIC * `id`: Identificador sequencial (0 a 1.999.999)
# MAGIC * `group_key`: Chave de agrupamento (0-9) com distribuição aleatória
# MAGIC * `payload`: String de ~2 KB com dados aleatórios
# MAGIC
# MAGIC **Resultado**: Tabela Delta com 4 arquivos Parquet totalizando ~4,1 GB.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Etapa 3: Verificação da Tabela Criada
# MAGIC
# MAGIC **Objetivo**: Inspecionar metadados e características físicas da tabela gerada.
# MAGIC
# MAGIC ### Informações Obtidas:
# MAGIC
# MAGIC * **Formato**: Delta Lake
# MAGIC * **Número de arquivos**: 4 arquivos Parquet
# MAGIC * **Tamanho total**: 4.122.566.969 bytes (~3,84 GB)
# MAGIC * **Compressão**: ZSTD (codec padrão do Delta)
# MAGIC * **Features habilitadas**: Deletion Vectors, Row Tracking, Domain Metadata
# MAGIC
# MAGIC ### Por que verificar?
# MAGIC
# MAGIC Confirmar que o dataset tem tamanho suficiente para exceder a memória disponível quando processado com configurações restritivas.
# MAGIC
# MAGIC **Observação**: Mesmo com compressão ZSTD, o tamanho permanece grande devido à alta entropia dos dados aleatórios.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Etapa 4: Operação Custosa para Forçar Spill
# MAGIC
# MAGIC **Objetivo**: Executar operações que consomem muita memória para provocar disk spill.
# MAGIC
# MAGIC ### Operações Aplicadas:
# MAGIC
# MAGIC 1. **`repartition(1)`**: Força todos os dados (~4 GB) em uma única partição
# MAGIC    * Requer shuffle completo do dataset
# MAGIC    * Concentra toda a carga em uma task
# MAGIC
# MAGIC 2. **`orderBy("payload")`**: Ordena por coluna de alta cardinalidade
# MAGIC    * Requer manter dados em memória para sorting
# MAGIC    * Strings de 2 KB cada aumentam pressão de memória
# MAGIC    * Com 2M linhas, precisa ordenar ~4 GB de dados
# MAGIC
# MAGIC 3. **`saveAsTable()`**: Persiste resultado em Delta
# MAGIC    * Força materialização completa
# MAGIC    * Escreve dados ordenados em disco
# MAGIC
# MAGIC ### Por que isso causa Spill?
# MAGIC
# MAGIC * **Memória necessária**: ~4 GB de dados + overhead de sorting
# MAGIC * **Memória disponível**: ~16 GB total, mas parte usada por JVM, buffers, etc.
# MAGIC * **Single partition**: Sem paralelismo para distribuir carga
# MAGIC * **Sorting**: Algoritmo de ordenação precisa manter estruturas auxiliares em memória
# MAGIC
# MAGIC ### Sinais de Spill:
# MAGIC
# MAGIC Durante a execução, observe na Spark UI:
# MAGIC * **Spill (Memory)**: Bytes que foram spilled da memória
# MAGIC * **Spill (Disk)**: Bytes escritos em disco temporário
# MAGIC * **Shuffle Write**: Volume de dados movimentados
# MAGIC * **Task Duration**: Tempo significativamente maior devido a I/O de disco
# MAGIC
# MAGIC **Status**: Célula em execução (streaming) - aguardando conclusão da operação custosa.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import StringType
import os
import base64

# -----------------------------
# Parâmetros
# -----------------------------
ROWS = 4_000_000          # ajuste conforme tempo
PAYLOAD_SIZE = 2048       # 1 KB real por linha (~2 GB total)
OUTPUT_TABLE = "sandbox.default.spill_demo_raw"
spark.sql(f"CREATE TABLE IF NOT EXISTS {OUTPUT_TABLE} USING DELTA")
# -----------------------------
# UDF de alta entropia REAL
# -----------------------------
def random_string():
    return base64.b64encode(os.urandom(PAYLOAD_SIZE)).decode("utf-8")

random_udf = F.udf(random_string, StringType())

# -----------------------------
# Gerar dataset
# -----------------------------
df = (
    spark.range(0, ROWS)
    .withColumn("group_key", (F.rand() * 10).cast("int"))  # skew proposital
    .withColumn("payload", random_udf())
)

# -----------------------------
# Gravar fisicamente (Delta)
# -----------------------------
(
    df.write
      .mode("overwrite")
      .format("delta")
      .option('mergeSchema', 'true').saveAsTable(OUTPUT_TABLE)
)

# COMMAND ----------

# MAGIC %sql
# MAGIC describe detail sandbox.default.spill_demo_raw

# COMMAND ----------

df = spark.table("sandbox.default.spill_demo_raw")

(
    df.repartition(1)
      .orderBy("payload")
      .write
      .mode("overwrite")
      .format("delta")
      .saveAsTable("sandbox.default.spill_demo_sorted")
)


# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from sandbox.default.spill_demo_sorted
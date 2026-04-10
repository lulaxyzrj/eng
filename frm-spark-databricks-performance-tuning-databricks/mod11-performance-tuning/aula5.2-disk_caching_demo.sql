-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Aula: Disk Caching no Databricks
-- MAGIC
-- MAGIC ## 🎯 Objetivo
-- MAGIC Demonstrar o **Disk Cache** (Delta Cache): cache automático em SSD local que acelera leituras repetitivas de tabelas Delta/Parquet.
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ## 💡 Conceito Chave
-- MAGIC
-- MAGIC **Disk Cache ≠ Premium Storage**
-- MAGIC
-- MAGIC | Tipo | Localização | Latência | Usado pelo Cache? |
-- MAGIC |------|-------------|----------|-------------------|
-- MAGIC | Premium Storage (Managed Disks) | Remoto (rede) | 5-10ms | ❌ Não |
-- MAGIC | Temporary Storage (NVMe Local) | Físico no worker | 0.1ms | ✅ Sim |
-- MAGIC
-- MAGIC **Por que `spark.databricks.io.cache.enabled = false` na E8_v3?**
-- MAGIC * E8_v3 tem apenas 100 GB de disco temporário (insuficiente)
-- MAGIC * Databricks só habilita automaticamente em instâncias Storage Optimized (série L: 678 GB - 1.8 TB)
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ## 🖥️ Instâncias Azure
-- MAGIC
-- MAGIC | Instância | Disco Local | Cache Automático | Uso |
-- MAGIC |------------|-------------|------------------|-----|
-- MAGIC | **D4s_v3** | ❌ Nenhum | `false` | ⚠️ Evitar |
-- MAGIC | **E8_v3** | ⚠️ 100 GB | `false` | Demo/teste |
-- MAGIC | **L4s/L8s_v2** | ✅ 678 GB - 1.8 TB | `true` | ✅ Produção |
-- MAGIC
-- MAGIC **Regra:** Forçar cache sem disco local **degrada** performance (fallback para storage remoto).
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ## 🧪 Lab
-- MAGIC
-- MAGIC **Tabela:** `sandbox.default.spill_demo_raw` (4M registros, ~10 GB)
-- MAGIC
-- MAGIC 1. Verificar status do cache (esperado: `false`)
-- MAGIC 2. Habilitar manualmente para demo
-- MAGIC 3. **Cold Read** (célula 10) → popula cache
-- MAGIC 4. **Warm Read** (célula 13) → usa cache
-- MAGIC 5. Comparar métricas na Spark UI

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 🔍 Parte 1: Verificação do Cache
-- MAGIC
-- MAGIC **Cluster:** Standard_E8_v3 (100 GB disco local)
-- MAGIC
-- MAGIC **Expectativa:** `false` (disco insuficiente para habilitação automática)
-- MAGIC
-- MAGIC **Comando:** Consulta a configuração atual do Disk Cache

-- COMMAND ----------

SET spark.databricks.io.cache.enabled

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 💡 Resultado: `false`
-- MAGIC
-- MAGIC **Por quê?** E8_v3 tem apenas 100 GB de disco temporário. Databricks exige ~500 GB para habilitação automática.
-- MAGIC
-- MAGIC **Comparação:**
-- MAGIC * **D4s_v3:** `false` (sem disco local)
-- MAGIC * **E8_v3:** `false` (disco pequeno)
-- MAGIC * **L4s:** `true` (678 GB NVMe)
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ### 🛠️ Habilitando Manualmente
-- MAGIC
-- MAGIC Para fins didáticos, vamos habilitar:

-- COMMAND ----------

SET spark.databricks.io.cache.enabled = True

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## ⚠️ Parte 2: Armadilha - Forçar Cache em Hardware Inadequado
-- MAGIC
-- MAGIC **Cenário:** Forçar cache em D4s_v3 (sem disco local)
-- MAGIC
-- MAGIC ```sql
-- MAGIC SET spark.databricks.io.cache.enabled = true
-- MAGIC ```
-- MAGIC
-- MAGIC **Resultado:**
-- MAGIC 1. Fallback para Premium Storage (remoto)
-- MAGIC 2. Latência de rede em cada leitura
-- MAGIC 3. Performance **pior** que ler direto do Delta Lake
-- MAGIC
-- MAGIC **Latências:**
-- MAGIC * Delta Lake (ADLS Gen2): 5-10ms
-- MAGIC * Cache NVMe Local: 0.1ms ✅
-- MAGIC * "Cache" Premium Storage: 3-8ms ❌
-- MAGIC
-- MAGIC **Quando forçar é válido:**
-- MAGIC * Instância com disco local (ex: D4**d**s_v3)
-- MAGIC * Série L com cache desabilitado por política
-- MAGIC
-- MAGIC **Regra:** Confie na detecção automática do Databricks.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 🔄 Disk Cache vs. Spark Cache
-- MAGIC
-- MAGIC **Confusão comum:** Disk Cache ≠ `CACHE TABLE`
-- MAGIC
-- MAGIC | Característica | Disk Cache | Spark Cache |
-- MAGIC |-----------------|------------|-------------|
-- MAGIC | **Armazenamento** | SSD NVMe local | Memória RAM |
-- MAGIC | **Trigger** | ✅ Automático (1ª leitura) | ❌ Manual (`CACHE TABLE`) |
-- MAGIC | **Persistência** | Entre queries | Apenas sessão |
-- MAGIC | **Spark UI** | Métricas "cache hits" no Scan | Aba "Storage" |
-- MAGIC | **Databricks recomenda** | ✅ Sim (padrão) | ⚠️ Casos específicos |
-- MAGIC
-- MAGIC **Quando usar cada um:**
-- MAGIC * **Disk Cache:** Tabelas Delta/Parquet, dashboards, EDA, ML iterativo
-- MAGIC * **Spark Cache:** Resultados intermediários, DataFrames não-Parquet
-- MAGIC
-- MAGIC **Nesta aula:** Demonstramos Disk Cache (automático). Não usaremos `CACHE TABLE`.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 🧪 Parte 3: Demonstração Prática
-- MAGIC
-- MAGIC **Tabela:** `sandbox.default.spill_demo_raw`
-- MAGIC * 4 milhões de registros
-- MAGIC * Colunas: `id`, `group_key`, `payload` (\~2.7 KB)
-- MAGIC * Tamanho real: 7.7 GiB
-- MAGIC
-- MAGIC **Fluxo:**
-- MAGIC 1. Célula 10: **Cold Read** (popula cache)
-- MAGIC 2. Célula 13: **Warm Read** (usa cache)

-- COMMAND ----------

desc detail sandbox.default.spill_demo_raw

-- COMMAND ----------

-- DBTITLE 1,Verify Table Creation
-- Cold Read: Primeira leitura da tabela (popula Disk Cache)
SELECT 
  group_key,
  COUNT(*) AS total_records,
  AVG(LENGTH(payload)) AS avg_payload_size,
  MIN(id) AS min_id,
  MAX(id) AS max_id
FROM sandbox.default.spill_demo_raw
GROUP BY group_key
ORDER BY group_key;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 📊 Parte 4: Análise Cold Read (Célula 10)
-- MAGIC
-- MAGIC **O que aconteceu:**
-- MAGIC 1. Spark leu 11.1 GiB de Parquet do ADLS Gen2
-- MAGIC 2. Disk Cache escreveu 11.1 GiB no SSD local
-- MAGIC 3. **7.2 minutos aguardando rede** + 5.1 min de scan total
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ### 🔍 Métricas Reais (Cold Read)
-- MAGIC
-- MAGIC **Acesso:** Spark UI → SQL/DataFrame tab → Scan parquet
-- MAGIC
-- MAGIC | Métrica | Valor | Significado |
-- MAGIC |---------|-------|-------------|
-- MAGIC | `cache hits size total` | **23.1 MiB** | Cache hit mínimo (footers/DVs) |
-- MAGIC | `cache misses size total` | **11.1 GiB** | Leitura remota (cold) |
-- MAGIC | `cache writes size total` | **11.1 GiB** | Populando cache |
-- MAGIC | `cloud storage response size` | **11.6 GiB** | Download ADLS Gen2 |
-- MAGIC | `cloud storage request duration` | **7.2 min** | Tempo aguardando rede |
-- MAGIC | `cloud storage request count` | **3038** | Chamadas HTTP |
-- MAGIC | `unified cache write bytes` | **11.1 GiB** | Escrito no SSD (ParquetColumnChunk) |
-- MAGIC | `unified cache hits count` | **602** | Hits em footers/DVs (já cached) |
-- MAGIC | `unified cache miss count` | **172** | Misses em column chunks (cold) |
-- MAGIC | `scan time` | **5.1 min** | Tempo total de scan |
-- MAGIC | `scan task time` | **7.6 min** | Tempo agregado de tasks |
-- MAGIC | `rows output` | **8,719,932** | Linhas lidas (4M + 1.7M DVs) |
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC **Próximo:** Célula 13 executa a mesma query. Esperamos **100% cache hit** e **redução drástica** no tempo.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 🚀 Parte 5: Warm Read - Usando o Disk Cache
-- MAGIC
-- MAGIC **O que já aconteceu (Célula 10 - Cold Read):**
-- MAGIC * Leu **11.1 GiB** do ADLS Gen2 (cache miss)
-- MAGIC * Escreveu **11.1 GiB** no SSD local (populando cache)
-- MAGIC * **7.2 minutos** de latência de rede
-- MAGIC * **3038 chamadas HTTP** para cloud storage
-- MAGIC * Scan time: **5.1 minutos**
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC **Agora (Célula 13 - Warm Read):**
-- MAGIC * Lê direto do SSD local (sem rede)
-- MAGIC * Esperado: **100% cache hit**
-- MAGIC * Ganho esperado: **4-10x mais rápido**
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ### 🎯 Expectativa de Métricas (Warm Read)
-- MAGIC
-- MAGIC | Métrica | Cold Read | Warm Read (Esperado) |
-- MAGIC |---------|-----------|----------------------|
-- MAGIC | `cache hits size` | 23.1 MiB | **≈ 11.1 GiB** ✅ |
-- MAGIC | `cache misses size` | 11.1 GiB | **0.0 B** ✅ |
-- MAGIC | `cloud storage response` | 11.6 GiB | **0.0 B** ✅ |
-- MAGIC | `cloud storage duration` | 7.2 min | **0 ms** ✅ |
-- MAGIC | `cloud storage requests` | 3038 | **0** ✅ |
-- MAGIC | `unified cache read bytes` | 23.1 MiB | **≈ 11.1 GiB** ✅ |
-- MAGIC | `scan time` | 5.1 min | **< 2 min** ✅ |
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC **Próximo:** Execute a célula 13 e compare as métricas reais na célula 14.

-- COMMAND ----------

-- DBTITLE 1,Warm Read Query - With Cache
-- Warm Read: Mesma query da célula 10 (com Disk Cache)
SELECT 
  group_key,
  COUNT(*) AS total_records,
  AVG(LENGTH(payload)) AS avg_payload_size,
  MIN(id) AS min_id,
  MAX(id) AS max_id
FROM sandbox.default.spill_demo_raw
GROUP BY group_key
ORDER BY group_key;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 📊 Parte 6: Comparação Cold vs Warm Read
-- MAGIC
-- MAGIC **Acesso:** Spark UI → SQL/DataFrame tab → Scan parquet → Metrics
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ### 🔥 Métricas Reais - Cold Read vs Warm Read
-- MAGIC
-- MAGIC | Métrica | Cold (Cél 10) | Warm (Cél 13) | Melhoria |
-- MAGIC |---------|--------------|--------------|----------|
-- MAGIC | **Cache Hits** |
-- MAGIC | `cache hits size total` | 23.1 MiB | **11.1 GiB** | ✅ **480x** |
-- MAGIC | `cache misses size total` | 11.1 GiB | **0.0 B** | ✅ **100%** |
-- MAGIC | **Cloud Storage (ADLS Gen2)** |
-- MAGIC | `cloud storage response size` | 11.6 GiB | **0.0 B** | ✅ **100%** |
-- MAGIC | `cloud storage request duration` | 7.2 min | **0 ms** | ✅ **100%** |
-- MAGIC | `cloud storage request count` | 3038 | **0** | ✅ **100%** |
-- MAGIC | **Unified Cache (SSD Local)** |
-- MAGIC | `unified cache hits count` | 602 | **774** | ✅ **100% hit** |
-- MAGIC | `unified cache miss count` | 172 | **0** | ✅ **100%** |
-- MAGIC | `unified cache read bytes` | 23.1 MiB | **11.1 GiB** | ✅ **SSD local** |
-- MAGIC | `unified cache write bytes` | 11.1 GiB | **0.0 B** | ✅ Já cached |
-- MAGIC | **Performance** |
-- MAGIC | `scan time` | **5.1 min** | **1.1 min** | ✅ **4.6x** |
-- MAGIC | `scan task time` | 7.6 min | **3.3 min** | ✅ **2.3x** |
-- MAGIC | `rows output` | 8,719,932 | 8,719,932 | ✅ Idêntico |
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ### ✅ Evidências de 100% Cache Hit
-- MAGIC
-- MAGIC **Cold Read (Célula 10):**
-- MAGIC * Leu **11.1 GiB** do ADLS Gen2 (cache miss)
-- MAGIC * Escreveu **11.1 GiB** no SSD local
-- MAGIC * **7.2 minutos** aguardando rede (3038 requests HTTP)
-- MAGIC * Scan time: **5.1 minutos**
-- MAGIC
-- MAGIC **Warm Read (Célula 13):**
-- MAGIC * Leu **11.1 GiB** do SSD local (100% cache hit)
-- MAGIC * **Zero bytes** baixados do ADLS Gen2
-- MAGIC * **Zero requests HTTP** para cloud storage
-- MAGIC * Scan time: **1.1 minuto** (78% redução)
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ### 💡 Por Que o Ganho Foi 4.6x (Não 10x)?
-- MAGIC
-- MAGIC **Fatores limitantes:**
-- MAGIC 1. **Single-node cluster:** 0 workers (apenas driver)
-- MAGIC 2. **CPU-bound após I/O:** Descompressão, agregação, ordenação
-- MAGIC 3. **E8_v3 (100 GB SSD):** Não otimizado para cache (série L seria melhor)
-- MAGIC
-- MAGIC **Ganho real:**
-- MAGIC * **Eliminação total** de latência de rede (7.2 min → 0 ms)
-- MAGIC * **4.6x mais rápido** mesmo em hardware não otimizado
-- MAGIC * Em produção (série L, multi-node): ganhos de **10-20x** são comuns
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ### ⚠️ Disk Cache vs Spark Cache
-- MAGIC
-- MAGIC | | Disk Cache | Spark Cache |
-- MAGIC |-|------------|-------------|
-- MAGIC | **Armazenamento** | SSD local | RAM |
-- MAGIC | **Spark UI** | "cache hits" no Scan | Aba "Storage" |
-- MAGIC | **Trigger** | Automático | `CACHE TABLE` |
-- MAGIC | **Persistência** | Entre queries | Apenas sessão |
-- MAGIC
-- MAGIC **Invalidação:** Modificações na tabela (UPDATE/DELETE), restart do cluster, disco cheio (LRU eviction).

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 🧹 Parte 6: Limpeza
-- MAGIC
-- MAGIC **Disk Cache:** Gerenciado automaticamente (LRU). Não precisa limpar.
-- MAGIC
-- MAGIC **Spark Cache:** Requer `UNCACHE TABLE` para liberar RAM.
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC **Boas práticas:**
-- MAGIC * Monitore uso de disco local
-- MAGIC * Use série L para produção
-- MAGIC * Não tente gerenciar Disk Cache manualmente

-- COMMAND ----------

-- DBTITLE 1,Drop Demo Table
-- Tabela sandbox.default.spill_demo_raw é mantida (usada em outros labs)
-- Não há necessidade de limpeza

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 🎯 Resumo
-- MAGIC
-- MAGIC ### 📌 Key Takeaways
-- MAGIC
-- MAGIC **1. Hardware é Fundamental**
-- MAGIC * Requer: NVMe local (temporary storage), ~500 GB mínimo
-- MAGIC * D4s_v3: ❌ Sem disco local → `false`
-- MAGIC * E8_v3: ⚠️ 100 GB → `false` (pequeno, mas funciona se habilitado)
-- MAGIC * L4s/L8s_v2: ✅ 678 GB - 1.8 TB → `true` (ideal)
-- MAGIC
-- MAGIC **2. Disk Cache vs Spark Cache**
-- MAGIC * **Disk Cache:** SSD local, automático, para Delta/Parquet
-- MAGIC * **Spark Cache:** RAM, manual (`CACHE TABLE`), para DataFrames
-- MAGIC
-- MAGIC
-- MAGIC **3. Quando Usar**
-- MAGIC * ✅ Queries repetitivas, dashboards, EDA, ML iterativo
-- MAGIC * ❌ Queries únicas, dados voláteis, sem disco local
-- MAGIC
-- MAGIC **4. Armadilhas Comuns**
-- MAGIC * ⚠️ Confundir Premium Storage com disco local
-- MAGIC * ⚠️ Achar que E8_v3 tem cache automático
-- MAGIC * ⚠️ Forçar cache em D4s_v3 (degrada performance)
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ### 📚 Próximos Passos
-- MAGIC
-- MAGIC 1. Teste com suas tabelas de produção
-- MAGIC 2. Compare E8_v3 vs L4s (ganhos ainda maiores)
-- MAGIC 3. Monitore métricas na Spark UI
-- MAGIC 4. Justifique uso de série L com ganhos documentados
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ### 🔗 Recursos
-- MAGIC
-- MAGIC * [Databricks Delta Cache](https://docs.databricks.com/delta/delta-cache.html)
-- MAGIC * [Azure Storage Optimized VMs](https://learn.microsoft.com/azure/virtual-machines/lsv2-series)
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ## ✅ Fim da Aula
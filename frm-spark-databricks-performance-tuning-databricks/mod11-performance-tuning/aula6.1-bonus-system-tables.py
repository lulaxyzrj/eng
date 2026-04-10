# Databricks notebook source
# MAGIC %md
# MAGIC # System Tables: Performance, Cost & Governance
# MAGIC
# MAGIC Este notebook demonstra o uso de **System Tables** do Databricks para monitoramento de:
# MAGIC
# MAGIC * **Performance**: Identificar queries lentas, gargalos de execução, spill to disk, eficiência de paralelização, cache hit rates
# MAGIC * **Custo**: Análise de consumo de DBUs por warehouse, usuário, tipo de workload e tendências temporais
# MAGIC * **Governança**: Rastreamento de tags de policies, auditoria de atividade de usuários, padrões de uso por aplicação
# MAGIC * **Capacity Planning**: Análise de concorrência, queue wait times, recomendações de sizing
# MAGIC
# MAGIC ## System Tables Utilizadas
# MAGIC
# MAGIC * `system.query.history` - Histórico de execução de queries SQL (performance, usuários, padrões)
# MAGIC * `system.billing.usage` - Consumo de DBUs, custos e tags de governance policies
# MAGIC
# MAGIC ## Estrutura do Notebook
# MAGIC
# MAGIC 1. **Performance Analysis** - Queries lentas, eficiência paralela, spill, cache
# MAGIC 2. **Cost Analysis** - DBUs por warehouse/usuário, tendências, breakdown por SKU
# MAGIC 3. **Tags & Governança** - Tags de policies, cost allocation, auditoria de usuários
# MAGIC 4. **Warehouse Usage Patterns** - Concorrência, wait times, capacity planning
# MAGIC
# MAGIC ---

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Performance Analysis
# MAGIC
# MAGIC ### Identificando Gargalos de Execução

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📊 Top Slow Queries
# MAGIC
# MAGIC **Objetivo:** Identifica as 10 queries mais lentas dos últimos 7 dias para priorizar otimizações.
# MAGIC
# MAGIC **Métricas-chave:**
# MAGIC * `parallel_efficiency_pct` - Eficiência de paralelização (ideal >80%)
# MAGIC * `wait_sec` - Tempo esperando por recursos (indica contenção)
# MAGIC * `read_mb` - Volume de dados lidos (candidatos para particionamento)
# MAGIC
# MAGIC **Quando usar:** Investigação inicial de problemas de performance ou revisão semanal de queries críticas.

# COMMAND ----------

# DBTITLE 1,Top Slow Queries
# MAGIC %sql
# MAGIC -- Top 10 queries mais lentas (últimos 7 dias)
# MAGIC -- Métricas defensivas: duration, task efficiency, I/O patterns
# MAGIC SELECT 
# MAGIC     statement_id,
# MAGIC     executed_by,
# MAGIC     compute.warehouse_id,
# MAGIC     start_time,
# MAGIC     total_duration_ms / 1000.0 AS duration_sec,
# MAGIC     execution_duration_ms / 1000.0 AS exec_sec,
# MAGIC     waiting_for_compute_duration_ms / 1000.0 AS wait_sec,
# MAGIC     read_bytes / 1024 / 1024 AS read_mb,
# MAGIC     produced_rows,
# MAGIC     CASE 
# MAGIC         WHEN total_duration_ms > 0 THEN (total_task_duration_ms / total_duration_ms) * 100 
# MAGIC         ELSE 0 
# MAGIC     END AS parallel_efficiency_pct,
# MAGIC     LEFT(statement_text, 100) AS query_preview
# MAGIC FROM system.query.history
# MAGIC WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
# MAGIC     AND execution_status = 'FINISHED'
# MAGIC     AND total_duration_ms > 0
# MAGIC ORDER BY total_duration_ms DESC
# MAGIC LIMIT 10

# COMMAND ----------

# MAGIC %md
# MAGIC ### ⚠️ Queries com Baixa Eficiência Paralela
# MAGIC
# MAGIC **Objetivo:** Detecta queries com eficiência de paralelização <50%, indicando data skew ou operações single-threaded.
# MAGIC
# MAGIC **Sinais de alerta:**
# MAGIC * Alto `shuffle_mb` com baixa eficiência → Skew em joins/aggregations
# MAGIC * Baixo `shuffle_mb` com baixa eficiência → Operações não paralelizáveis (UDFs, window functions sem particionamento)
# MAGIC
# MAGIC **Ação recomendada:** Revisar estratégia de join (broadcast vs. shuffle), adicionar salting em chaves skewed, ou reparticionar dados.

# COMMAND ----------

# DBTITLE 1,Low Parallel Efficiency
# MAGIC %sql
# MAGIC -- Queries com baixa eficiência de paralelização (<50%)
# MAGIC -- Indica possível skew ou operações single-threaded
# MAGIC SELECT 
# MAGIC     statement_id,
# MAGIC     executed_by,
# MAGIC     start_time,
# MAGIC     total_duration_ms / 1000.0 AS duration_sec,
# MAGIC     (total_task_duration_ms / NULLIF(total_duration_ms, 0)) * 100 AS parallel_efficiency_pct,
# MAGIC     read_bytes / 1024 / 1024 AS read_mb,
# MAGIC     shuffle_read_bytes / 1024 / 1024 AS shuffle_mb,
# MAGIC     LEFT(statement_text, 80) AS query_preview
# MAGIC FROM system.query.history
# MAGIC WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
# MAGIC     AND execution_status = 'FINISHED'
# MAGIC     AND total_duration_ms > 10000  -- Apenas queries >10s
# MAGIC     AND total_task_duration_ms > 0
# MAGIC     AND (total_task_duration_ms / total_duration_ms) < 0.5  -- <50% efficiency
# MAGIC ORDER BY total_duration_ms DESC
# MAGIC LIMIT 20

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💾 Spill to Disk Analysis (ANTI-OOM)
# MAGIC
# MAGIC **Objetivo:** Identifica queries que esgotaram memória e precisaram escrever dados temporários em disco.
# MAGIC
# MAGIC **Impacto:** Spill degrada performance drasticamente (10-100x mais lento que operações em memória).
# MAGIC
# MAGIC **Causas comuns:**
# MAGIC * Joins cartesianos ou sem broadcast hint
# MAGIC * Aggregations com alta cardinalidade sem pré-agregação
# MAGIC * Window functions sobre partições muito grandes
# MAGIC
# MAGIC **Solução:** Scale-up do warehouse, otimização de joins, ou refatoração da lógica.

# COMMAND ----------

# DBTITLE 1,Spill to Disk Analysis
# MAGIC %sql
# MAGIC -- Queries com spill to disk (memória insuficiente)
# MAGIC -- ANTI-OOM: Identifica queries que precisam de mais memória ou otimização
# MAGIC SELECT 
# MAGIC     statement_id,
# MAGIC     executed_by,
# MAGIC     compute.warehouse_id,
# MAGIC     start_time,
# MAGIC     total_duration_ms / 1000.0 AS duration_sec,
# MAGIC     spilled_local_bytes / 1024 / 1024 / 1024 AS spilled_gb,
# MAGIC     read_bytes / 1024 / 1024 / 1024 AS read_gb,
# MAGIC     shuffle_read_bytes / 1024 / 1024 / 1024 AS shuffle_gb,
# MAGIC     (spilled_local_bytes / NULLIF(read_bytes, 0)) * 100 AS spill_ratio_pct,
# MAGIC     LEFT(statement_text, 80) AS query_preview
# MAGIC FROM system.query.history
# MAGIC WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC AND spilled_local_bytes > 0
# MAGIC ORDER BY spilled_local_bytes DESC
# MAGIC LIMIT 20

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🚀 Cache Hit Rate Analysis
# MAGIC
# MAGIC **Objetivo:** Mede efetividade do I/O cache (Delta cache) e result cache por warehouse.
# MAGIC
# MAGIC **Métricas:**
# MAGIC * `result_cache_hit_rate_pct` - Queries idênticas servidas do cache (ideal >30% para dashboards)
# MAGIC * `avg_io_cache_pct` - Dados lidos do cache local vs. cloud storage (ideal >50%)
# MAGIC
# MAGIC **Otimização:** Warehouses com baixo cache hit podem se beneficiar de:
# MAGIC * Photon habilitado (melhora Delta cache)
# MAGIC * Queries parametrizadas (aumenta result cache)
# MAGIC * Warm-up de warehouses antes de horários de pico

# COMMAND ----------

# DBTITLE 1,Cache Hit Rate Analysis
# MAGIC %sql
# MAGIC -- Análise de cache hit rate (I/O cache e result cache)
# MAGIC -- Identifica oportunidades de otimização via caching
# MAGIC SELECT 
# MAGIC     DATE(start_time) AS date,
# MAGIC     compute.warehouse_id,
# MAGIC     COUNT(*) AS total_queries,
# MAGIC     SUM(CASE WHEN from_result_cache THEN 1 ELSE 0 END) AS result_cache_hits,
# MAGIC     AVG(read_io_cache_percent) AS avg_io_cache_pct,
# MAGIC     SUM(read_bytes) / 1024 / 1024 / 1024 AS total_read_gb,
# MAGIC     AVG(total_duration_ms) / 1000.0 AS avg_duration_sec,
# MAGIC     -- Result cache hit rate
# MAGIC     (SUM(CASE WHEN from_result_cache THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS result_cache_hit_rate_pct
# MAGIC FROM system.query.history
# MAGIC WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC     AND execution_status = 'FINISHED'
# MAGIC GROUP BY DATE(start_time), compute.warehouse_id
# MAGIC ORDER BY date DESC, compute.warehouse_id

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Cost Analysis
# MAGIC
# MAGIC ### Consumo de DBUs e Alocação de Custos

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💰 Consumo de DBUs por Warehouse
# MAGIC
# MAGIC **Objetivo:** Identifica warehouses com maior consumo de DBUs para priorizar otimizações de custo.
# MAGIC
# MAGIC **Métricas:**
# MAGIC * `avg_dbus_per_day` - Consumo médio diário (detecta padrões irregulares)
# MAGIC * `estimated_cost_usd` - Custo estimado baseado em preço de SQL Compute ($0.22/DBU)
# MAGIC
# MAGIC **Filtro:** Apenas SKUs SQL (remova o filtro para ver Jobs e All-Purpose).
# MAGIC
# MAGIC **Ação:** Warehouses com alto custo e baixo uso podem ser candidatos para auto-stop mais agressivo ou downsize.

# COMMAND ----------

# DBTITLE 1,DBU Consumption by Warehouse
# MAGIC %sql
# MAGIC -- Consumo de DBUs por warehouse (últimos 30 dias)
# MAGIC -- Identifica warehouses com maior custo para otimização
# MAGIC SELECT 
# MAGIC     usage_metadata.warehouse_id,
# MAGIC     sku_name,
# MAGIC     SUM(usage_quantity) AS total_dbus,
# MAGIC     COUNT(DISTINCT usage_date) AS days_active,
# MAGIC     SUM(usage_quantity) / COUNT(DISTINCT usage_date) AS avg_dbus_per_day,
# MAGIC     -- Estimativa de custo (assumindo $0.22/DBU para SQL Compute)
# MAGIC     SUM(usage_quantity) * 0.22 AS estimated_cost_usd
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC     AND usage_metadata.warehouse_id IS NOT NULL
# MAGIC     AND sku_name LIKE '%SQL%'
# MAGIC GROUP BY usage_metadata.warehouse_id, sku_name
# MAGIC ORDER BY total_dbus DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 👥 Alocação de Custo por Usuário
# MAGIC
# MAGIC **Objetivo:** Atribui custos de DBUs proporcionalmente ao tempo de execução de queries por usuário (chargeback).
# MAGIC
# MAGIC **Método:** Cruza `query.history` (tempo de execução) com `billing.usage` (DBUs consumidos) usando window functions para alocação proporcional.
# MAGIC
# MAGIC **Limitação:** Não captura idle time de warehouses (apenas tempo de query ativa).
# MAGIC
# MAGIC **Uso:** Relatórios de chargeback por equipe/projeto ou identificação de usuários com queries ineficientes.

# COMMAND ----------

# DBTITLE 1,Cost by User
# MAGIC %sql
# MAGIC -- Consumo de DBUs por usuário (últimos 30 dias)
# MAGIC -- Cruzamento entre query.history e billing para atribuição de custo
# MAGIC WITH user_query_duration AS (
# MAGIC     SELECT 
# MAGIC         executed_by,
# MAGIC         compute.warehouse_id,
# MAGIC         SUM(total_duration_ms) / 1000.0 / 3600.0 AS total_hours,  -- Conversão para horas
# MAGIC         COUNT(*) AS query_count
# MAGIC     FROM system.query.history
# MAGIC     WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC         AND execution_status = 'FINISHED'
# MAGIC     GROUP BY executed_by, compute.warehouse_id
# MAGIC ),
# MAGIC warehouse_dbus AS (
# MAGIC     SELECT 
# MAGIC         usage_metadata.warehouse_id,
# MAGIC         SUM(usage_quantity) AS total_dbus
# MAGIC     FROM system.billing.usage
# MAGIC     WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC         AND usage_metadata.warehouse_id IS NOT NULL
# MAGIC     GROUP BY usage_metadata.warehouse_id
# MAGIC )
# MAGIC SELECT 
# MAGIC     u.executed_by,
# MAGIC     u.warehouse_id,
# MAGIC     u.query_count,
# MAGIC     u.total_hours,
# MAGIC     w.total_dbus AS warehouse_total_dbus,
# MAGIC     -- Alocação proporcional de DBUs baseada em tempo de execução
# MAGIC     (u.total_hours / SUM(u.total_hours) OVER (PARTITION BY u.warehouse_id)) * w.total_dbus AS allocated_dbus,
# MAGIC     (u.total_hours / SUM(u.total_hours) OVER (PARTITION BY u.warehouse_id)) * w.total_dbus * 0.22 AS estimated_cost_usd
# MAGIC FROM user_query_duration u
# MAGIC LEFT JOIN warehouse_dbus w ON u.warehouse_id = w.warehouse_id
# MAGIC WHERE w.total_dbus IS NOT NULL
# MAGIC ORDER BY allocated_dbus DESC
# MAGIC LIMIT 20

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📈 Tendências Diárias de Custo
# MAGIC
# MAGIC **Objetivo:** Visualiza evolução de custos ao longo do tempo com média móvel de 7 dias para suavizar variações.
# MAGIC
# MAGIC **Insights:**
# MAGIC * Picos inesperados → Investigação de jobs ou queries anômalas
# MAGIC * Tendência crescente → Necessidade de otimização ou budget review
# MAGIC * Padrões semanais → Oportunidade para scheduling de workloads
# MAGIC
# MAGIC **Janela:** Últimos 90 dias para capturar sazonalidade mensal.

# COMMAND ----------

# DBTITLE 1,Daily Cost Trends
# MAGIC %sql
# MAGIC -- Tendência diária de consumo de DBUs
# MAGIC -- Identifica picos de uso e padrões sazonais
# MAGIC SELECT 
# MAGIC     usage_date,
# MAGIC     sku_name,
# MAGIC     SUM(usage_quantity) AS total_dbus,
# MAGIC     SUM(usage_quantity) * 0.22 AS estimated_cost_usd,
# MAGIC     -- Média móvel de 7 dias
# MAGIC     AVG(SUM(usage_quantity)) OVER (
# MAGIC         PARTITION BY sku_name 
# MAGIC         ORDER BY usage_date 
# MAGIC         ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
# MAGIC     ) AS dbus_7day_avg
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= CURRENT_DATE() - INTERVAL 90 DAYS
# MAGIC     AND sku_name LIKE '%SQL%'
# MAGIC GROUP BY usage_date, sku_name
# MAGIC ORDER BY usage_date DESC, sku_name

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🎯 Breakdown de Custos por SKU
# MAGIC
# MAGIC **Objetivo:** Distribui custos entre tipos de compute (SQL, Jobs, All-Purpose, Serverless) para entender composição do gasto.
# MAGIC
# MAGIC **Preços de referência (Azure):**
# MAGIC * Serverless SQL: $0.70/DBU
# MAGIC * SQL Compute: $0.22/DBU
# MAGIC * All-Purpose: $0.55/DBU
# MAGIC * Jobs Compute: $0.15/DBU
# MAGIC
# MAGIC **Otimização:** Migrar workloads de All-Purpose para Jobs Compute pode reduzir custos em 73%.

# COMMAND ----------

# DBTITLE 1,Cost Breakdown by SKU
# MAGIC %sql
# MAGIC -- Breakdown de custos por tipo de SKU (últimos 30 dias)
# MAGIC -- Identifica distribuição entre SQL, Jobs, All-Purpose, etc.
# MAGIC SELECT 
# MAGIC     sku_name,
# MAGIC     usage_unit,
# MAGIC     SUM(usage_quantity) AS total_units,
# MAGIC     COUNT(DISTINCT usage_date) AS days_active,
# MAGIC     COUNT(DISTINCT usage_metadata.warehouse_id) AS unique_warehouses,
# MAGIC     SUM(usage_quantity) / COUNT(DISTINCT usage_date) AS avg_units_per_day,
# MAGIC     -- Estimativa de custo (preços aproximados)
# MAGIC     CASE 
# MAGIC         WHEN sku_name LIKE '%SERVERLESS%SQL%' THEN SUM(usage_quantity) * 0.70
# MAGIC         WHEN sku_name LIKE '%SQL%' THEN SUM(usage_quantity) * 0.22
# MAGIC         WHEN sku_name LIKE '%JOBS%' THEN SUM(usage_quantity) * 0.15
# MAGIC         WHEN sku_name LIKE '%ALL_PURPOSE%' THEN SUM(usage_quantity) * 0.55
# MAGIC         ELSE SUM(usage_quantity) * 0.20
# MAGIC     END AS estimated_cost_usd
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC GROUP BY sku_name, usage_unit
# MAGIC ORDER BY total_units DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Tags & Governança
# MAGIC
# MAGIC ### Rastreamento de Tags e Auditoria de Uso

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🏷️ Análise de Tags de Governance
# MAGIC
# MAGIC **Objetivo:** Extrai e agrega tags aplicadas via policies em warehouses/clusters para rastreamento de custos.
# MAGIC
# MAGIC **Fonte:** `system.billing.usage.custom_tags` (MAP<string, string>) - tags de governance policies, não query tags.
# MAGIC
# MAGIC **Uso típico:**
# MAGIC * `env` (dev/prod) - Separação de ambientes
# MAGIC * `centro_custo` / `CostCenter` - Chargeback por departamento
# MAGIC * `project` - Alocação por projeto/iniciativa
# MAGIC
# MAGIC **Próximo passo:** Use estas tags para criar dashboards de cost allocation por equipe.

# COMMAND ----------

# DBTITLE 1,Query Tags Analysis
# MAGIC %sql
# MAGIC -- Extração e análise de tags de governance (policies)
# MAGIC -- Tags aplicadas via policies em warehouses/clusters para cost allocation
# MAGIC SELECT 
# MAGIC     tag_key,
# MAGIC     tag_value,
# MAGIC     COUNT(*) AS usage_records,
# MAGIC     SUM(usage_quantity) AS total_dbus,
# MAGIC     COUNT(DISTINCT usage_date) AS days_active,
# MAGIC     COUNT(DISTINCT usage_metadata.warehouse_id) AS unique_warehouses,
# MAGIC     SUM(usage_quantity) * 0.22 AS estimated_cost_usd,
# MAGIC     -- Breakdown por SKU
# MAGIC     COUNT(DISTINCT sku_name) AS unique_skus
# MAGIC FROM system.billing.usage
# MAGIC LATERAL VIEW EXPLODE(custom_tags) AS tag_key, tag_value
# MAGIC WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC     AND custom_tags IS NOT NULL
# MAGIC GROUP BY tag_key, tag_value
# MAGIC ORDER BY total_dbus DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📊 Alocação de Custo por Tag
# MAGIC
# MAGIC **Objetivo:** Calcula custo total por tag com breakdown por tipo de workload (SQL/Jobs/All-Purpose).
# MAGIC
# MAGIC **Diferencial:** Aplica preços específicos por SKU para estimar custo real (não apenas DBUs).
# MAGIC
# MAGIC **Métricas:**
# MAGIC * `estimated_cost_usd` - Custo total considerando preço de cada SKU
# MAGIC * `sql_dbus`, `jobs_dbus`, `all_purpose_dbus` - Breakdown por tipo de compute
# MAGIC
# MAGIC **Caso de uso:** Relatórios de chargeback para finance ou identificação de projetos com custos elevados.

# COMMAND ----------

# DBTITLE 1,Cost Allocation by Tags
# MAGIC %sql
# MAGIC -- Alocação de custo por tag (governance policies)
# MAGIC -- Permite chargeback por projeto/equipe/ambiente usando tags de policies
# MAGIC SELECT 
# MAGIC     tag_key,
# MAGIC     tag_value,
# MAGIC     COUNT(*) AS usage_records,
# MAGIC     SUM(usage_quantity) AS total_dbus,
# MAGIC     COUNT(DISTINCT usage_date) AS days_active,
# MAGIC     COUNT(DISTINCT usage_metadata.warehouse_id) AS unique_warehouses,
# MAGIC     -- Custo estimado por tipo de SKU
# MAGIC     SUM(
# MAGIC         CASE 
# MAGIC             WHEN sku_name LIKE '%SERVERLESS%SQL%' THEN usage_quantity * 0.70
# MAGIC             WHEN sku_name LIKE '%SQL%' THEN usage_quantity * 0.22
# MAGIC             WHEN sku_name LIKE '%JOBS%' THEN usage_quantity * 0.15
# MAGIC             WHEN sku_name LIKE '%ALL_PURPOSE%' THEN usage_quantity * 0.55
# MAGIC             ELSE usage_quantity * 0.20
# MAGIC         END
# MAGIC     ) AS estimated_cost_usd,
# MAGIC     -- Breakdown por tipo de workload
# MAGIC     SUM(CASE WHEN sku_name LIKE '%SQL%' THEN usage_quantity ELSE 0 END) AS sql_dbus,
# MAGIC     SUM(CASE WHEN sku_name LIKE '%JOBS%' THEN usage_quantity ELSE 0 END) AS jobs_dbus,
# MAGIC     SUM(CASE WHEN sku_name LIKE '%ALL_PURPOSE%' THEN usage_quantity ELSE 0 END) AS all_purpose_dbus
# MAGIC FROM system.billing.usage
# MAGIC LATERAL VIEW EXPLODE(custom_tags) AS tag_key, tag_value
# MAGIC WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC     AND custom_tags IS NOT NULL
# MAGIC GROUP BY tag_key, tag_value
# MAGIC ORDER BY estimated_cost_usd DESC
# MAGIC LIMIT 30

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🖥️ Padrões de Uso por Cliente/Aplicação
# MAGIC
# MAGIC **Objetivo:** Identifica ferramentas e drivers mais utilizados para acessar Databricks SQL.
# MAGIC
# MAGIC **Insights:**
# MAGIC * `failure_rate_pct` - Ferramentas com alta taxa de erro podem ter problemas de conexão/timeout
# MAGIC * `avg_duration_sec` - Compara performance entre diferentes clientes
# MAGIC * `unique_users` - Adoção de ferramentas BI (Tableau, Power BI, etc.)
# MAGIC
# MAGIC **Exemplos comuns:**
# MAGIC * Databricks SQL Dashboard/Editor
# MAGIC * Databricks Notebooks
# MAGIC * JDBC/ODBC drivers (Power BI, Tableau)
# MAGIC * Python connectors (databricks-sql-connector)

# COMMAND ----------

# DBTITLE 1,Query Patterns by Client
# MAGIC %sql
# MAGIC -- Padrões de uso por aplicação/cliente
# MAGIC -- Identifica ferramentas e drivers mais utilizados
# MAGIC SELECT 
# MAGIC     client_application,
# MAGIC     client_driver,
# MAGIC     COUNT(*) AS query_count,
# MAGIC     COUNT(DISTINCT executed_by) AS unique_users,
# MAGIC     AVG(total_duration_ms) / 1000.0 AS avg_duration_sec,
# MAGIC     SUM(read_bytes) / 1024 / 1024 / 1024 AS total_read_gb,
# MAGIC     -- Padrões de erro
# MAGIC     SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_queries,
# MAGIC     (SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS failure_rate_pct
# MAGIC FROM system.query.history
# MAGIC WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC     AND client_application IS NOT NULL
# MAGIC GROUP BY client_application, client_driver
# MAGIC ORDER BY query_count DESC
# MAGIC LIMIT 20

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🔍 Auditoria de Atividade de Usuários
# MAGIC
# MAGIC **Objetivo:** Perfil de uso por usuário para identificação de padrões, anomalias e usuários inativos.
# MAGIC
# MAGIC **Métricas de alerta:**
# MAGIC * `failed_queries` alto → Usuário com problemas de permissão ou queries mal formadas
# MAGIC * `long_running_queries` >5min → Candidatos para otimização ou treinamento
# MAGIC * `active_days` baixo com `total_queries` alto → Uso concentrado (possível automação)
# MAGIC
# MAGIC **Governança:** Identifica usuários que não acessam há >30 dias para revisão de licenças.

# COMMAND ----------

# DBTITLE 1,User Activity Audit
# MAGIC %sql
# MAGIC -- Auditoria de atividade por usuário
# MAGIC -- Identifica padrões de uso, usuários inativos, e anomalias
# MAGIC SELECT 
# MAGIC     executed_by,
# MAGIC     COUNT(*) AS total_queries,
# MAGIC     COUNT(DISTINCT DATE(start_time)) AS active_days,
# MAGIC     MIN(start_time) AS first_query,
# MAGIC     MAX(start_time) AS last_query,
# MAGIC     SUM(total_duration_ms) / 1000.0 / 3600.0 AS total_hours,
# MAGIC     AVG(total_duration_ms) / 1000.0 AS avg_duration_sec,
# MAGIC     SUM(read_bytes) / 1024 / 1024 / 1024 AS total_read_gb,
# MAGIC     COUNT(DISTINCT compute.warehouse_id) AS warehouses_used,
# MAGIC     -- Padrões de erro
# MAGIC     SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_queries,
# MAGIC     -- Queries longas (>5min)
# MAGIC     SUM(CASE WHEN total_duration_ms > 300000 THEN 1 ELSE 0 END) AS long_running_queries
# MAGIC FROM system.query.history
# MAGIC WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC GROUP BY executed_by
# MAGIC ORDER BY total_queries DESC
# MAGIC LIMIT 30

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Warehouse Usage Patterns
# MAGIC
# MAGIC ### Utilização, Concorrência e Capacity Planning

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🕒 Padrões de Uso por Hora do Dia
# MAGIC
# MAGIC **Objetivo:** Identifica horários de pico para dimensionamento e scheduling de warehouses.
# MAGIC
# MAGIC **Métricas:**
# MAGIC * `queries_with_wait` - Queries que esperaram por recursos (indica subdimensionamento)
# MAGIC * `avg_wait_sec` - Tempo médio de espera por hora
# MAGIC * `total_hours` - Horas de compute consumidas
# MAGIC
# MAGIC **Otimização:**
# MAGIC * Picos com alto `queries_with_wait` → Aumentar min_clusters ou habilitar auto-scaling
# MAGIC * Horários de baixo uso → Reduzir auto-stop timeout para economizar
# MAGIC * Padrões previsíveis → Usar scheduled scaling

# COMMAND ----------

# DBTITLE 1,Hourly Query Patterns
# MAGIC %sql
# MAGIC -- Padrões de uso por hora do dia (identifica picos)
# MAGIC -- Útil para dimensionamento e scheduling de warehouses
# MAGIC SELECT 
# MAGIC     HOUR(start_time) AS hour_of_day,
# MAGIC     compute.warehouse_id,
# MAGIC     COUNT(*) AS query_count,
# MAGIC     AVG(total_duration_ms) / 1000.0 AS avg_duration_sec,
# MAGIC     SUM(total_duration_ms) / 1000.0 / 3600.0 AS total_hours,
# MAGIC     AVG(waiting_for_compute_duration_ms) / 1000.0 AS avg_wait_sec,
# MAGIC     -- Queries que esperaram por compute (indica necessidade de scale-up)
# MAGIC     SUM(CASE WHEN waiting_for_compute_duration_ms > 1000 THEN 1 ELSE 0 END) AS queries_with_wait
# MAGIC FROM system.query.history
# MAGIC WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC     AND execution_status = 'FINISHED'
# MAGIC GROUP BY HOUR(start_time), compute.warehouse_id
# MAGIC ORDER BY compute.warehouse_id, hour_of_day

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🔀 Análise de Concorrência
# MAGIC
# MAGIC **Objetivo:** Calcula concorrência real de queries por warehouse usando overlap de timestamps.
# MAGIC
# MAGIC **Método:** Self-join em `query_timeline` para contar queries simultâneas em cada momento.
# MAGIC
# MAGIC **Métricas:**
# MAGIC * `max_concurrency` - Pico de queries simultâneas (compara com max_clusters configurado)
# MAGIC * `p95_concurrency` - Concorrência no percentil 95 (mais confiável que máximo)
# MAGIC
# MAGIC **Capacity planning:** Se `p95_concurrency` ≈ `max_clusters`, warehouse está saturado. Considere aumentar limite.

# COMMAND ----------

# DBTITLE 1,Warehouse Concurrency
# MAGIC %sql
# MAGIC -- Análise de concorrência por warehouse
# MAGIC -- Identifica momentos de alta concorrência e necessidade de scaling
# MAGIC WITH query_timeline AS (
# MAGIC     SELECT 
# MAGIC         compute.warehouse_id,
# MAGIC         start_time,
# MAGIC         end_time,
# MAGIC         statement_id
# MAGIC     FROM system.query.history
# MAGIC     WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
# MAGIC         AND execution_status = 'FINISHED'
# MAGIC         AND end_time IS NOT NULL
# MAGIC ),
# MAGIC concurrency_calc AS (
# MAGIC     SELECT 
# MAGIC         a.warehouse_id,
# MAGIC         a.start_time,
# MAGIC         COUNT(DISTINCT b.statement_id) AS concurrent_queries
# MAGIC     FROM query_timeline a
# MAGIC     JOIN query_timeline b 
# MAGIC         ON a.warehouse_id = b.warehouse_id
# MAGIC         AND b.start_time <= a.start_time 
# MAGIC         AND b.end_time >= a.start_time
# MAGIC     GROUP BY a.warehouse_id, a.start_time
# MAGIC )
# MAGIC SELECT 
# MAGIC     warehouse_id,
# MAGIC     MAX(concurrent_queries) AS max_concurrency,
# MAGIC     AVG(concurrent_queries) AS avg_concurrency,
# MAGIC     PERCENTILE(concurrent_queries, 0.95) AS p95_concurrency,
# MAGIC     COUNT(*) AS sample_points
# MAGIC FROM concurrency_calc
# MAGIC GROUP BY warehouse_id
# MAGIC ORDER BY max_concurrency DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ### ⏱️ Tempo de Espera em Fila (ANTI-OOM)
# MAGIC
# MAGIC **Objetivo:** Detecta warehouses subdimensionados ou com alta contenção de recursos.
# MAGIC
# MAGIC **Métricas críticas:**
# MAGIC * `wait_rate_pct` - % de queries que esperaram (ideal <5%)
# MAGIC * `p95_wait_sec` - Tempo de espera no P95 (mais representativo que média)
# MAGIC * `avg_capacity_wait_sec` - Espera específica por warehouse at max capacity
# MAGIC
# MAGIC **Thresholds de alerta:**
# MAGIC * `wait_rate_pct` >10% → Warehouse subdimensionado
# MAGIC * `p95_wait_sec` >30s → Impacto severo em UX
# MAGIC * `avg_capacity_wait_sec` >0 → Max clusters insuficiente

# COMMAND ----------

# DBTITLE 1,Query Queue Wait Times
# MAGIC %sql
# MAGIC -- Análise de tempo de espera em fila
# MAGIC -- ANTI-OOM: Identifica warehouses subdimensionados ou com alta contenção
# MAGIC SELECT 
# MAGIC     compute.warehouse_id,
# MAGIC     DATE(start_time) AS date,
# MAGIC     COUNT(*) AS total_queries,
# MAGIC     -- Queries que esperaram por compute
# MAGIC     SUM(CASE WHEN waiting_for_compute_duration_ms > 0 THEN 1 ELSE 0 END) AS queries_with_wait,
# MAGIC     (SUM(CASE WHEN waiting_for_compute_duration_ms > 0 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS wait_rate_pct,
# MAGIC     -- Métricas de tempo de espera
# MAGIC     AVG(waiting_for_compute_duration_ms) / 1000.0 AS avg_wait_sec,
# MAGIC     MAX(waiting_for_compute_duration_ms) / 1000.0 AS max_wait_sec,
# MAGIC     PERCENTILE(waiting_for_compute_duration_ms, 0.95) / 1000.0 AS p95_wait_sec,
# MAGIC     -- Tempo de espera por capacidade (warehouse at max capacity)
# MAGIC     AVG(waiting_at_capacity_duration_ms) / 1000.0 AS avg_capacity_wait_sec
# MAGIC FROM system.query.history
# MAGIC WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC     AND execution_status = 'FINISHED'
# MAGIC GROUP BY compute.warehouse_id, DATE(start_time)
# MAGIC HAVING queries_with_wait > 0
# MAGIC ORDER BY date DESC, wait_rate_pct DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🎯 Métricas de Capacity Planning
# MAGIC
# MAGIC **Objetivo:** Combina performance, custo e utilização para gerar recomendações automatizadas de sizing.
# MAGIC
# MAGIC **Lógica de recomendação:**
# MAGIC 1. `high_wait_rate_pct` >10% → **SCALE UP** (adicionar clusters ou aumentar size)
# MAGIC 2. `spill_rate_pct` >5% → **SCALE UP** (aumentar memória por node)
# MAGIC 3. `avg_cache_hit_pct` <30% → **OPTIMIZE** (habilitar Photon, revisar queries)
# MAGIC 4. `avg_duration_sec` <5s → **SCALE DOWN** (possível over-provisioning)
# MAGIC
# MAGIC **Métrica de eficiência:** `cost_per_hour` - Custo por hora de compute (benchmark entre warehouses).

# COMMAND ----------

# DBTITLE 1,Capacity Planning Metrics
# MAGIC %sql
# MAGIC -- Métricas para capacity planning
# MAGIC -- Combina performance, custo e utilização para recomendações de sizing
# MAGIC WITH warehouse_metrics AS (
# MAGIC     SELECT 
# MAGIC         compute.warehouse_id,
# MAGIC         COUNT(*) AS total_queries,
# MAGIC         SUM(total_duration_ms) / 1000.0 / 3600.0 AS total_compute_hours,
# MAGIC         AVG(total_duration_ms) / 1000.0 AS avg_duration_sec,
# MAGIC         -- Indicadores de problemas de performance
# MAGIC         SUM(CASE WHEN waiting_for_compute_duration_ms > 5000 THEN 1 ELSE 0 END) AS high_wait_queries,
# MAGIC         SUM(CASE WHEN spilled_local_bytes > 0 THEN 1 ELSE 0 END) AS spill_queries,
# MAGIC         SUM(CASE WHEN total_duration_ms > 300000 THEN 1 ELSE 0 END) AS long_queries,
# MAGIC         -- Métricas de I/O
# MAGIC         SUM(read_bytes) / 1024 / 1024 / 1024 AS total_read_gb,
# MAGIC         AVG(read_io_cache_percent) AS avg_cache_hit_pct
# MAGIC     FROM system.query.history
# MAGIC     WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC         AND execution_status = 'FINISHED'
# MAGIC     GROUP BY compute.warehouse_id
# MAGIC ),
# MAGIC warehouse_costs AS (
# MAGIC     SELECT 
# MAGIC         usage_metadata.warehouse_id,
# MAGIC         SUM(usage_quantity) AS total_dbus,
# MAGIC         SUM(usage_quantity) * 0.22 AS total_cost_usd
# MAGIC     FROM system.billing.usage
# MAGIC     WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC         AND usage_metadata.warehouse_id IS NOT NULL
# MAGIC     GROUP BY usage_metadata.warehouse_id
# MAGIC )
# MAGIC SELECT 
# MAGIC     m.warehouse_id,
# MAGIC     m.total_queries,
# MAGIC     m.total_compute_hours,
# MAGIC     m.avg_duration_sec,
# MAGIC     c.total_dbus,
# MAGIC     c.total_cost_usd,
# MAGIC     -- Indicadores de problemas
# MAGIC     m.high_wait_queries,
# MAGIC     (m.high_wait_queries / m.total_queries) * 100 AS high_wait_rate_pct,
# MAGIC     m.spill_queries,
# MAGIC     (m.spill_queries / m.total_queries) * 100 AS spill_rate_pct,
# MAGIC     m.long_queries,
# MAGIC     -- Eficiência de custo
# MAGIC     c.total_cost_usd / NULLIF(m.total_compute_hours, 0) AS cost_per_hour,
# MAGIC     m.avg_cache_hit_pct,
# MAGIC     -- Recomendação simples
# MAGIC     CASE 
# MAGIC         WHEN (m.high_wait_queries / m.total_queries) > 0.1 THEN 'SCALE UP: High queue wait times'
# MAGIC         WHEN (m.spill_queries / m.total_queries) > 0.05 THEN 'SCALE UP: Frequent memory spills'
# MAGIC         WHEN m.avg_cache_hit_pct < 30 THEN 'OPTIMIZE: Low cache hit rate'
# MAGIC         WHEN m.avg_duration_sec < 5 THEN 'SCALE DOWN: Queries too fast, possible over-provisioning'
# MAGIC         ELSE 'OK: No immediate action needed'
# MAGIC     END AS recommendation
# MAGIC FROM warehouse_metrics m
# MAGIC LEFT JOIN warehouse_costs c ON m.warehouse_id = c.warehouse_id
# MAGIC ORDER BY c.total_cost_usd DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC ## Próximos Passos & Best Practices
# MAGIC
# MAGIC ### Monitoramento Contínuo
# MAGIC
# MAGIC * **Alertas Proativos**: Configure alertas para queries com spill >10GB, wait times >30s, ou custos diários acima do baseline
# MAGIC * **Dashboards**: Crie dashboards Lakeview com estas queries para monitoramento em tempo real
# MAGIC * **Automação**: Use Jobs para executar estas análises diariamente e enviar relatórios
# MAGIC
# MAGIC ### Otimizações Defensivas
# MAGIC
# MAGIC * **Anti-OOM**: Queries com spill frequente precisam de warehouses maiores ou otimização de joins
# MAGIC * **Cost Control**: Use tags consistentemente para chargeback preciso por projeto/equipe
# MAGIC * **Capacity Planning**: Revise métricas de concorrência semanalmente para ajustar sizing
# MAGIC
# MAGIC ### Recursos Adicionais
# MAGIC
# MAGIC * [System Tables Documentation](https://docs.databricks.com/administration-guide/system-tables/index.html)
# MAGIC * [Query Profile Analysis](https://docs.databricks.com/optimizations/query-profile.html)
# MAGIC * [Cost Management Best Practices](https://docs.databricks.com/administration-guide/account-settings/usage.html)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Compute Metrics (Classic Clusters)
# MAGIC
# MAGIC ### Detecção de Spill, Skew e Pressão de Recursos
# MAGIC
# MAGIC **⚠️ Escopo:** Apenas **All-Purpose** e **Jobs Compute** (não cobre SQL Warehouses ou Serverless).
# MAGIC
# MAGIC **Fonte:** `system.compute.node_timeline` - Métricas minuto-a-minuto por node.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💥 Pressão de Memória e Spill Detection
# MAGIC
# MAGIC **Objetivo:** Identifica nodes com alta utilização de memória e swap (indicadores de spill to disk).
# MAGIC
# MAGIC **Sinais de spill:**
# MAGIC * `mem_used_percent` >90% - Memória saturada
# MAGIC * `mem_swap_percent` >0 - Sistema começou a usar swap (OOM iminente)
# MAGIC * `cpu_wait_percent` alto - CPU esperando por I/O (spill to disk)
# MAGIC
# MAGIC **Ação:** Clusters com spill frequente precisam de nodes maiores ou otimização de jobs.

# COMMAND ----------

# DBTITLE 1,Memory Pressure Query
# MAGIC %sql
# MAGIC -- Nodes com alta pressão de memória (últimos 7 dias)
# MAGIC -- ANTI-OOM: Identifica spill to disk via memória e swap
# MAGIC SELECT 
# MAGIC     cluster_id,
# MAGIC     driver,
# MAGIC     DATE(start_time) AS date,
# MAGIC     COUNT(*) AS minutes_recorded,
# MAGIC     -- Métricas de memória
# MAGIC     AVG(mem_used_percent) AS avg_mem_used_pct,
# MAGIC     MAX(mem_used_percent) AS peak_mem_used_pct,
# MAGIC     AVG(mem_swap_percent) AS avg_swap_pct,
# MAGIC     MAX(mem_swap_percent) AS peak_swap_pct,
# MAGIC     -- CPU wait indica I/O (spill)
# MAGIC     AVG(cpu_wait_percent) AS avg_cpu_wait_pct,
# MAGIC     MAX(cpu_wait_percent) AS peak_cpu_wait_pct,
# MAGIC     -- Minutos com memória crítica
# MAGIC     SUM(CASE WHEN mem_used_percent > 90 THEN 1 ELSE 0 END) AS minutes_mem_critical,
# MAGIC     SUM(CASE WHEN mem_swap_percent > 0 THEN 1 ELSE 0 END) AS minutes_with_swap
# MAGIC FROM system.compute.node_timeline
# MAGIC WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
# MAGIC GROUP BY cluster_id, driver, DATE(start_time)
# MAGIC HAVING avg_mem_used_pct > 80 OR peak_swap_pct > 0
# MAGIC ORDER BY peak_mem_used_pct DESC, peak_swap_pct DESC
# MAGIC LIMIT 50

# COMMAND ----------

# MAGIC %md
# MAGIC ### ⚖️ Detecção de Skew entre Workers
# MAGIC
# MAGIC **Objetivo:** Identifica desbalanceamento de carga entre workers do mesmo cluster.
# MAGIC
# MAGIC **Método:** Calcula variância de CPU/memória entre workers. Alta variância = skew.
# MAGIC
# MAGIC **Causas de skew:**
# MAGIC * Partições desbalanceadas (chaves com alta cardinalidade)
# MAGIC * Joins sem broadcast hint
# MAGIC * Window functions sem particionamento adequado
# MAGIC
# MAGIC **Threshold:** Variância >30% indica skew significativo.

# COMMAND ----------

# DBTITLE 1,Worker Skew Query
# MAGIC %sql
# MAGIC -- Detecção de skew entre workers (últimos 3 dias)
# MAGIC -- Compara métricas entre workers do mesmo cluster
# MAGIC WITH worker_metrics AS (
# MAGIC     SELECT 
# MAGIC         cluster_id,
# MAGIC         instance_id,
# MAGIC         AVG(cpu_user_percent + cpu_system_percent) AS avg_cpu_pct,
# MAGIC         AVG(mem_used_percent) AS avg_mem_pct,
# MAGIC         AVG(network_sent_bytes) / 1024 / 1024 AS avg_network_mb_sent
# MAGIC     FROM system.compute.node_timeline
# MAGIC     WHERE start_time >= CURRENT_DATE() - INTERVAL 3 DAYS
# MAGIC         AND driver = FALSE  -- Apenas workers
# MAGIC     GROUP BY cluster_id, instance_id
# MAGIC ),
# MAGIC cluster_variance AS (
# MAGIC     SELECT 
# MAGIC         cluster_id,
# MAGIC         COUNT(DISTINCT instance_id) AS worker_count,
# MAGIC         AVG(avg_cpu_pct) AS cluster_avg_cpu,
# MAGIC         STDDEV(avg_cpu_pct) AS cpu_stddev,
# MAGIC         AVG(avg_mem_pct) AS cluster_avg_mem,
# MAGIC         STDDEV(avg_mem_pct) AS mem_stddev,
# MAGIC         AVG(avg_network_mb_sent) AS cluster_avg_network,
# MAGIC         STDDEV(avg_network_mb_sent) AS network_stddev,
# MAGIC         -- Coeficiente de variação (CV = stddev/mean)
# MAGIC         (STDDEV(avg_cpu_pct) / NULLIF(AVG(avg_cpu_pct), 0)) * 100 AS cpu_cv_pct,
# MAGIC         (STDDEV(avg_mem_pct) / NULLIF(AVG(avg_mem_pct), 0)) * 100 AS mem_cv_pct
# MAGIC     FROM worker_metrics
# MAGIC     GROUP BY cluster_id
# MAGIC     HAVING worker_count > 1  -- Apenas clusters multi-worker
# MAGIC )
# MAGIC SELECT 
# MAGIC     cluster_id,
# MAGIC     worker_count,
# MAGIC     ROUND(cluster_avg_cpu, 2) AS avg_cpu_pct,
# MAGIC     ROUND(cpu_stddev, 2) AS cpu_stddev,
# MAGIC     ROUND(cpu_cv_pct, 2) AS cpu_variation_pct,
# MAGIC     ROUND(cluster_avg_mem, 2) AS avg_mem_pct,
# MAGIC     ROUND(mem_stddev, 2) AS mem_stddev,
# MAGIC     ROUND(mem_cv_pct, 2) AS mem_variation_pct,
# MAGIC     ROUND(cluster_avg_network, 2) AS avg_network_mb,
# MAGIC     ROUND(network_stddev, 2) AS network_stddev,
# MAGIC     -- Diagnóstico
# MAGIC     CASE 
# MAGIC         WHEN cpu_cv_pct > 50 OR mem_cv_pct > 50 THEN 'SEVERE SKEW: Repartition data'
# MAGIC         WHEN cpu_cv_pct > 30 OR mem_cv_pct > 30 THEN 'MODERATE SKEW: Review partition keys'
# MAGIC         ELSE 'OK: Balanced workload'
# MAGIC     END AS skew_diagnosis
# MAGIC FROM cluster_variance
# MAGIC WHERE cpu_cv_pct > 20 OR mem_cv_pct > 20  -- Apenas clusters com skew
# MAGIC ORDER BY cpu_cv_pct DESC, mem_cv_pct DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🌐 Análise de Shuffle (Network Traffic)
# MAGIC
# MAGIC **Objetivo:** Identifica clusters com shuffle excessivo (indica joins/aggregations ineficientes).
# MAGIC
# MAGIC **Métricas:**
# MAGIC * `network_sent_bytes` / `network_received_bytes` - Volume de shuffle
# MAGIC * Assimetria entre sent/received indica broadcast vs. shuffle
# MAGIC
# MAGIC **Otimização:** Shuffle alto sugere:
# MAGIC * Usar broadcast hints para tabelas pequenas
# MAGIC * Reparticionar antes de joins
# MAGIC * Revisar window functions

# COMMAND ----------

# DBTITLE 1,Network Shuffle Query
# MAGIC %sql
# MAGIC -- Clusters com alto volume de shuffle (últimos 7 dias)
# MAGIC -- Identifica jobs com joins/aggregations ineficientes
# MAGIC SELECT 
# MAGIC     cluster_id,
# MAGIC     driver,
# MAGIC     COUNT(DISTINCT DATE(start_time)) AS days_active,
# MAGIC     -- Volume de rede
# MAGIC     SUM(network_sent_bytes) / 1024 / 1024 / 1024 AS total_sent_gb,
# MAGIC     SUM(network_received_bytes) / 1024 / 1024 / 1024 AS total_received_gb,
# MAGIC     AVG(network_sent_bytes) / 1024 / 1024 AS avg_sent_mb_per_min,
# MAGIC     AVG(network_received_bytes) / 1024 / 1024 AS avg_received_mb_per_min,
# MAGIC     -- Ratio sent/received (broadcast vs shuffle)
# MAGIC     (SUM(network_sent_bytes) / NULLIF(SUM(network_received_bytes), 0)) AS sent_received_ratio,
# MAGIC     -- Picos de rede
# MAGIC     MAX(network_sent_bytes) / 1024 / 1024 AS peak_sent_mb,
# MAGIC     MAX(network_received_bytes) / 1024 / 1024 AS peak_received_mb
# MAGIC FROM system.compute.node_timeline
# MAGIC WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
# MAGIC GROUP BY cluster_id, driver
# MAGIC HAVING total_sent_gb > 10 OR total_received_gb > 10  -- Apenas clusters com shuffle significativo
# MAGIC ORDER BY total_sent_gb + total_received_gb DESC
# MAGIC LIMIT 30

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📊 Utilização de Recursos por Cluster
# MAGIC
# MAGIC **Objetivo:** Visão consolidada de CPU, memória e rede para capacity planning.
# MAGIC
# MAGIC **Uso:** Identifica clusters:
# MAGIC * **Over-provisioned** - Baixa utilização consistente
# MAGIC * **Under-provisioned** - Alta utilização com picos frequentes
# MAGIC * **Idle** - Clusters ligados sem carga

# COMMAND ----------

# DBTITLE 1,Resource Utilization Query
# MAGIC %sql
# MAGIC -- Utilização consolidada de recursos (últimos 30 dias)
# MAGIC -- Para capacity planning e rightsizing
# MAGIC WITH cluster_metrics AS (
# MAGIC     SELECT 
# MAGIC         n.cluster_id,
# MAGIC         c.cluster_name,
# MAGIC         c.cluster_source,
# MAGIC         c.driver_node_type,
# MAGIC         c.worker_node_type,
# MAGIC         c.worker_count,
# MAGIC         COUNT(DISTINCT DATE(n.start_time)) AS days_active,
# MAGIC         COUNT(*) AS total_minutes,
# MAGIC         -- CPU
# MAGIC         AVG(n.cpu_user_percent + n.cpu_system_percent) AS avg_cpu_pct,
# MAGIC         MAX(n.cpu_user_percent + n.cpu_system_percent) AS peak_cpu_pct,
# MAGIC         -- Memória
# MAGIC         AVG(n.mem_used_percent) AS avg_mem_pct,
# MAGIC         MAX(n.mem_used_percent) AS peak_mem_pct,
# MAGIC         -- Rede
# MAGIC         SUM(n.network_sent_bytes + n.network_received_bytes) / 1024 / 1024 / 1024 AS total_network_gb
# MAGIC     FROM system.compute.node_timeline n
# MAGIC     LEFT JOIN system.compute.clusters c ON n.cluster_id = c.cluster_id
# MAGIC     WHERE n.start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC     GROUP BY 
# MAGIC         n.cluster_id, c.cluster_name, c.cluster_source, 
# MAGIC         c.driver_node_type, c.worker_node_type, c.worker_count
# MAGIC )
# MAGIC SELECT 
# MAGIC     cluster_id,
# MAGIC     cluster_name,
# MAGIC     cluster_source,
# MAGIC     driver_node_type,
# MAGIC     worker_node_type,
# MAGIC     worker_count,
# MAGIC     days_active,
# MAGIC     total_minutes,
# MAGIC     ROUND(avg_cpu_pct, 2) AS avg_cpu_pct,
# MAGIC     ROUND(peak_cpu_pct, 2) AS peak_cpu_pct,
# MAGIC     ROUND(avg_mem_pct, 2) AS avg_mem_pct,
# MAGIC     ROUND(peak_mem_pct, 2) AS peak_mem_pct,
# MAGIC     ROUND(total_network_gb, 2) AS total_network_gb,
# MAGIC     -- Diagnóstico de sizing
# MAGIC     CASE 
# MAGIC         WHEN avg_cpu_pct < 20 AND avg_mem_pct < 30 THEN 'OVER-PROVISIONED: Consider downsizing'
# MAGIC         WHEN peak_cpu_pct > 90 OR peak_mem_pct > 90 THEN 'UNDER-PROVISIONED: Scale up or optimize'
# MAGIC         WHEN avg_cpu_pct < 10 AND total_minutes > 1440 THEN 'IDLE: Review auto-termination'
# MAGIC         ELSE 'OK: Adequate sizing'
# MAGIC     END AS sizing_recommendation
# MAGIC FROM cluster_metrics
# MAGIC ORDER BY days_active DESC, total_minutes DESC
# MAGIC LIMIT 50
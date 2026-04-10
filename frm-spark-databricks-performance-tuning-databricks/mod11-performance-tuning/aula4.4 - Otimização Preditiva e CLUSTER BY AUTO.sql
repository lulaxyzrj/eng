-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Otimização Preditiva e CLUSTER BY AUTO
-- MAGIC
-- MAGIC ## Visão Geral
-- MAGIC
-- MAGIC Este notebook demonstra como configurar e utilizar duas funcionalidades poderosas do Databricks:
-- MAGIC
-- MAGIC ### 🔮 **Otimização Preditiva (Predictive Optimization)**
-- MAGIC * Executa manutenção automática em segundo plano (OPTIMIZE, VACUUM, ANALYZE)
-- MAGIC * Elimina a necessidade de jobs manuais de manutenção
-- MAGIC * Habilitada por padrão em contas criadas após 11/11/2024
-- MAGIC * Pode ser controlada em nível de catálogo ou schema
-- MAGIC
-- MAGIC ### 🎯 **CLUSTER BY AUTO**
-- MAGIC * O Databricks gerencia automaticamente o layout físico dos dados
-- MAGIC * Substitui particionamento manual e Z-ORDER
-- MAGIC * Aprende com os padrões de consulta e adapta o clustering dinamicamente
-- MAGIC * Requer Databricks Runtime 15.4 LTS ou superior
-- MAGIC * **Depende da Otimização Preditiva para funcionar**
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ## 📚 Estrutura da Aula
-- MAGIC
-- MAGIC 1. Configuração da Otimização Preditiva
-- MAGIC 2. Criação de tabelas com CLUSTER BY AUTO
-- MAGIC 3. Conversão de tabelas existentes
-- MAGIC 4. Verificação e monitoramento
-- MAGIC
-- MAGIC **Catálogo/Schema usado:** `sandbox.default`

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1️⃣ Configurando a Otimização Preditiva
-- MAGIC
-- MAGIC A Otimização Preditiva pode ser habilitada em diferentes níveis:
-- MAGIC
-- MAGIC * **Nível de Conta:** Via Account Console (requer permissões de administrador)
-- MAGIC * **Nível de Catálogo:** Via SQL (controle granular)
-- MAGIC * **Nível de Schema:** Via SQL (controle granular)
-- MAGIC
-- MAGIC ### ⚠️ Pré-requisito
-- MAGIC Para usar CLUSTER BY AUTO, a Otimização Preditiva **deve estar ativa**.

-- COMMAND ----------

-- DBTITLE 1,Enable at catalog level
-- Habilitar Otimização Preditiva no catálogo inteiro
-- Isso afetará todos os schemas e tabelas dentro do catálogo 'samples'
ALTER CATALOG sandbox ENABLE PREDICTIVE OPTIMIZATION;

-- COMMAND ----------

-- DBTITLE 1,Enable at schema level
-- Habilitar Otimização Preditiva apenas no schema 'wanderbricks'
-- Útil para testar em um escopo menor antes de expandir
ALTER SCHEMA sandbox.default DISABLE PREDICTIVE OPTIMIZATION;

-- COMMAND ----------

-- DBTITLE 1,Check optimization status
-- Verificar o status da Otimização Preditiva
-- Procure pela propriedade 'delta.enablePredictiveOptimization'
DESCRIBE SCHEMA EXTENDED sandbox.default;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### ⏱️ Configurando Retenção (Time Travel)
-- MAGIC
-- MAGIC **Importante:** A Otimização Preditiva executará VACUUM automaticamente com base na retenção padrão de **7 dias**.
-- MAGIC
-- MAGIC Se você precisa de mais tempo de histórico para Time Travel:
-- MAGIC * Configure a propriedade `delta.deletedFileRetentionDuration` **antes** de habilitar a otimização
-- MAGIC * Valores comuns: 7 days (padrão), 30 days, 90 days
-- MAGIC * Maior retenção = mais espaço de armazenamento usado

-- COMMAND ----------

-- DBTITLE 1,Set retention example
-- Exemplo: Configurar retenção de 30 dias em uma tabela
-- Execute ANTES de habilitar a Otimização Preditiva

-- ALTER TABLE samples.wanderbricks.sua_tabela 
-- SET TBLPROPERTIES ('delta.deletedFileRetentionDuration' = '30 days');

-- Nota: Este é um exemplo comentado. 
-- Descomente e substitua 'sua_tabela' pelo nome real da tabela.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2️⃣ Implementando CLUSTER BY AUTO
-- MAGIC
-- MAGIC ### Cenário 1: Criando uma Nova Tabela (SQL)
-- MAGIC
-- MAGIC Ao criar uma tabela gerenciada no Unity Catalog, basta adicionar `CLUSTER BY AUTO`.
-- MAGIC
-- MAGIC **Requisitos:**
-- MAGIC * Databricks Runtime 15.4 LTS ou superior ✅
-- MAGIC * Otimização Preditiva habilitada ✅
-- MAGIC * Tabela gerenciada no Unity Catalog ✅

-- COMMAND ----------

-- DBTITLE 1,Create table with explicit clustering
-- Criar tabela com CLUSTER BY explícito (colunas específicas)
-- Fonte: samples.wanderbricks.booking_updates (Delta Sharing - read-only)
-- Destino: sandbox.default (nosso catálogo com permissão de escrita)
-- Clustering manual por status e check_in (padrão comum de consulta)

CREATE OR REPLACE TABLE sandbox.default.booking_updates_gold
CLUSTER BY AUTO --(status, check_in)
COMMENT 'Tabela de atualizações de reservas com clustering manual'
AS
SELECT 
  booking_id,
  booking_update_id,
  check_in,
  check_out,
  created_at,
  guests_count,
  property_id,
  status,
  total_amount,
  updated_at,
  user_id
FROM samples.wanderbricks.booking_updates

-- COMMAND ----------

-- DBTITLE 1,Verify explicit clustering
-- Verificar configuração de clustering explícito
-- Note: clusteringColumns mostra ["status","check_in"]
-- clusterByAuto ainda não está habilitado
DESCRIBE DETAIL sandbox.default.booking_updates_gold;

-- COMMAND ----------

-- DBTITLE 1,Insert sample data
-- Inserir dados adicionais de exemplo para demonstração
INSERT INTO sandbox.default.booking_updates_gold 
  (booking_id, booking_update_id, check_in, check_out, created_at, guests_count, property_id, status, total_amount, updated_at, user_id)
VALUES
  (99001, 17570289999001, CURRENT_DATE() + INTERVAL 30 DAYS, CURRENT_DATE() + INTERVAL 35 DAYS, CURRENT_TIMESTAMP(), 2, 5001, 'confirmed', 1250.00, CURRENT_TIMESTAMP(), 10001),
  (99002, 17570289999002, CURRENT_DATE() + INTERVAL 45 DAYS, CURRENT_DATE() + INTERVAL 50 DAYS, CURRENT_TIMESTAMP(), 4, 5002, 'pending', 2100.50, CURRENT_TIMESTAMP(), 10002),
  (99003, 17570289999003, CURRENT_DATE() + INTERVAL 60 DAYS, CURRENT_DATE() + INTERVAL 62 DAYS, CURRENT_TIMESTAMP(), 1, 5003, 'confirmed', 450.00, CURRENT_TIMESTAMP(), 10003),
  (99004, 17570289999004, CURRENT_DATE() + INTERVAL 15 DAYS, CURRENT_DATE() + INTERVAL 20 DAYS, CURRENT_TIMESTAMP(), 3, 5004, 'cancelled', 890.00, CURRENT_TIMESTAMP(), 10004),
  (99005, 17570289999005, CURRENT_DATE() + INTERVAL 90 DAYS, CURRENT_DATE() + INTERVAL 97 DAYS, CURRENT_TIMESTAMP(), 5, 5005, 'pending', 3200.00, CURRENT_TIMESTAMP(), 10005);

-- COMMAND ----------

-- Verificar configuração de clustering explícito
-- Note: clusteringColumns mostra ["status","check_in"]
-- clusterByAuto ainda não está habilitado
DESCRIBE DETAIL sandbox.default.booking_updates_gold;

-- COMMAND ----------

OPTIMIZE sandbox.default.booking_updates_gold

-- COMMAND ----------

-- Verificar configuração de clustering explícito
-- Note: clusteringColumns mostra ["status","check_in"]
-- clusterByAuto ainda não está habilitado
DESCRIBE DETAIL sandbox.default.booking_updates_gold;

-- COMMAND ----------

-- DBTITLE 1,Query sample data
-- Visualizar os dados inseridos
SELECT 
  booking_id,
  check_in,
  check_out,
  guests_count,
  status,
  total_amount,
  updated_at
FROM sandbox.default.booking_updates_gold
ORDER BY updated_at DESC
LIMIT 20;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Cenário 2: Convertendo uma Tabela Existente
-- MAGIC
-- MAGIC Se você já tem uma tabela (mesmo que particionada ou com Z-ORDER manual), pode convertê-la para clustering automático.
-- MAGIC
-- MAGIC **Processo:**
-- MAGIC 1. Habilitar CLUSTER BY AUTO na tabela
-- MAGIC 2. (Opcional) Forçar reorganização imediata com OPTIMIZE FULL
-- MAGIC
-- MAGIC **Nota:** A Otimização Preditiva irá eventualmente otimizar a tabela. O OPTIMIZE FULL é opcional para efeito imediato.

-- COMMAND ----------

-- DBTITLE 1,Enable auto clustering on existing table
-- Converter de CLUSTER BY explícito para AUTO
-- A tabela foi criada com CLUSTER BY (status, check_in)
-- Agora vamos deixar o Databricks gerenciar automaticamente
ALTER TABLE sandbox.default.booking_updates_gold 
CLUSTER BY AUTO;

-- COMMAND ----------

-- DBTITLE 1,Verify AUTO clustering
-- Verificar configuração após conversão para AUTO
-- Note: clusteringColumns mostra ["status","check_in"]
-- delta.clusterByAuto = true nas propriedades
DESCRIBE DETAIL sandbox.default.booking_updates_gold;

-- COMMAND ----------

-- DBTITLE 1,Force immediate optimization
-- (OPCIONAL) Forçar reorganização imediata de todos os dados
-- ATENÇÃO: Pode demorar em tabelas grandes, pois reescreve os dados
-- O FULL garante que dados antigos sejam re-clusterizados

OPTIMIZE sandbox.default.booking_updates_gold FULL;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3️⃣ Verificação e Monitoramento
-- MAGIC
-- MAGIC ### Como Confirmar se CLUSTER BY AUTO está Ativo
-- MAGIC
-- MAGIC Use `DESCRIBE EXTENDED` para inspecionar as propriedades da tabela.
-- MAGIC
-- MAGIC **O que procurar:**
-- MAGIC * `delta.clusterByAuto` = `true` nas TBLPROPERTIES
-- MAGIC * Ausência de colunas de particionamento manual
-- MAGIC * Histórico de otimizações automáticas

-- COMMAND ----------

-- DBTITLE 1,Verify booking_updates_gold table configuration
-- Verificar configuração da tabela booking_updates_gold
-- Procure por 'delta.clusterByAuto' nas propriedades
DESCRIBE EXTENDED sandbox.default.booking_updates_gold;

-- COMMAND ----------

-- DBTITLE 1,Check table properties
-- Visualizar apenas as propriedades da tabela (mais limpo)
SHOW TBLPROPERTIES sandbox.default.booking_updates_gold;

-- COMMAND ----------

-- DBTITLE 1,Monitor optimization history
-- Verificar histórico de otimizações (OPTIMIZE, VACUUM, etc.)
-- Isso mostrará quando a Otimização Preditiva executou manutenção
DESCRIBE HISTORY sandbox.default.booking_updates_gold
LIMIT 10;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 🎯 Resumo e Boas Práticas
-- MAGIC
-- MAGIC ### ✅ Checklist de Implementação
-- MAGIC
-- MAGIC 1. **Habilitar Otimização Preditiva** (nível de catálogo ou schema)
-- MAGIC 2. **Configurar retenção** se precisar de Time Travel > 7 dias
-- MAGIC 3. **Criar tabelas com CLUSTER BY AUTO** ou converter existentes
-- MAGIC 4. **Verificar** com DESCRIBE EXTENDED
-- MAGIC 5. **Monitorar** com DESCRIBE HISTORY
-- MAGIC
-- MAGIC ### 💡 Boas Práticas
-- MAGIC
-- MAGIC * **Confie no sistema**: O Databricks aprende com seus padrões de consulta
-- MAGIC * **Remova Z-ORDER manual**: CLUSTER BY AUTO substitui essa necessidade
-- MAGIC * **Remova particionamento manual**: Deixe o sistema decidir o layout ideal
-- MAGIC * **Monitore custos**: A otimização consome recursos, mas geralmente compensa com queries mais rápidas
-- MAGIC
-- MAGIC ### 🔗 Recursos Adicionais
-- MAGIC
-- MAGIC * [Documentação Oficial - Predictive Optimization](https://docs.databricks.com/en/optimizations/predictive-optimization.html)
-- MAGIC * [Documentação Oficial - CLUSTER BY AUTO](https://docs.databricks.com/en/delta/clustering.html)
-- MAGIC * [Delta Lake Best Practices](https://docs.databricks.com/en/delta/best-practices.html)

-- COMMAND ----------

-- Ver operações recentes na sua tabela
SELECT 
*
FROM system.storage.predictive_optimization_operations_history
-- WHERE catalog_name = 'sandbox'
--   AND schema_name = 'default'
--   AND table_name = 'booking_updates_gold'
-- ORDER BY start_time DESC
-- LIMIT 10;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ⏱️ Quando Esperar Execução Automática?
-- MAGIC
-- MAGIC Primeira execução: Pode levar horas/dias após habilitar
-- MAGIC
-- MAGIC Frequência: Baseada em heurísticas (volume de writes, fragmentação, etc.)
-- MAGIC
-- MAGIC Não é imediato: Não há SLA garantido
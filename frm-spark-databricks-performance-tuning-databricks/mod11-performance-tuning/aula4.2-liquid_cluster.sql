-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 🎓 Demonstração Completa: Liquid Clustering no Databricks
-- MAGIC
-- MAGIC ## 📋 Objetivo da Aula
-- MAGIC Este notebook demonstra o **ciclo de vida completo** do Liquid Clustering no Databricks, comparando quatro cenários:
-- MAGIC 1. **Greenfield**: Criação de tabela nova com clustering desde o início
-- MAGIC 2. **Anti-padrão**: Tabela particionada por alta cardinalidade (o problema)
-- MAGIC 3. **Migração**: Conversão de tabela particionada para Liquid Clustering (a solução)
-- MAGIC 4. **Z-Ordering**: Técnica legacy e migração para Liquid Clustering (modernização)
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ## 🎯 O Que é Liquid Clustering?
-- MAGIC
-- MAGIC **Liquid Clustering** é uma técnica de organização física de dados no Delta Lake que:
-- MAGIC * **Substitui o particionamento tradicional** para colunas de alta cardinalidade
-- MAGIC * **Organiza dados automaticamente** com base em padrões de consulta
-- MAGIC * **Melhora performance** de leitura sem criar milhares de arquivos pequenos
-- MAGIC * **Adapta-se dinamicamente** conforme os dados evoluem
-- MAGIC * **Moderniza Z-Ordering** com manutenção automática e metadados persistidos
-- MAGIC
-- MAGIC ### Quando Usar?
-- MAGIC ✅ Colunas com **alta cardinalidade** (user_id, customer_id, transaction_id)  
-- MAGIC ✅ Queries que **filtram por múltiplas colunas**  
-- MAGIC ✅ Dados que **crescem continuamente**  
-- MAGIC ✅ Necessidade de **flexibilidade** (alterar colunas de clustering sem reescrever dados)  
-- MAGIC ✅ **Substituição de Z-Ordering** em projetos modernos (DBR 13.3+)

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC
-- MAGIC ## 📦 Fase 0: Preparação do Ambiente
-- MAGIC
-- MAGIC ### Objetivo
-- MAGIC Configurar o workspace e garantir um ambiente limpo para a demonstração.
-- MAGIC
-- MAGIC ### O Que Fazemos
-- MAGIC * Selecionamos o **catálogo** (`sandbox`) e **schema** (`default`) do Unity Catalog
-- MAGIC * Removemos tabelas de execuções anteriores para evitar conflitos
-- MAGIC * Garantimos que todos os alunos comecem do zero
-- MAGIC
-- MAGIC ### Tabelas Criadas Nesta Demo
-- MAGIC 1. `demo_bookings_new` → Tabela greenfield com clustering
-- MAGIC 2. `demo_chaos_partitioned` → Tabela com particionamento problemático
-- MAGIC 3. `demo_bookings_migration` → Tabela migrada para clustering
-- MAGIC 4. `demo_bookings_zorder` → Tabela com Z-Ordering (legacy) que será migrada IN-PLACE para Liquid Clustering
-- MAGIC
-- MAGIC ### Dataset Utilizado
-- MAGIC **`samples.wanderbricks.booking_updates`**  
-- MAGIC https://marketplace.databricks.com/details/ed6cf259-81e7-4758-94c5-b444f8a5275a/Databricks_Wanderbricks-Dataset-DAIS-2025
-- MAGIC
-- MAGIC Tabela de exemplo do Databricks contendo atualizações de reservas de hotéis com:
-- MAGIC * **11 colunas**: booking_id, user_id, property_id, status, check_in, check_out, etc.
-- MAGIC * **Alta cardinalidade** em `user_id` (milhares de usuários únicos)
-- MAGIC * **Padrões de consulta típicos**: filtros por user_id, property_id, status

-- COMMAND ----------

-- ========================================
-- FASE 0: PREPARAÇÃO DO AMBIENTE
-- ========================================
-- Configuramos o catálogo e schema do Unity Catalog
-- e limpamos tabelas de execuções anteriores

USE CATALOG sandbox;
USE SCHEMA default;

-- Limpeza: Remove tabelas da demonstração anterior
DROP TABLE IF EXISTS demo_bookings_new;
DROP TABLE IF EXISTS demo_bookings_migration;
DROP TABLE IF EXISTS demo_chaos_partitioned;
DROP TABLE IF EXISTS demo_bookings_zorder;

-- COMMAND ----------

-- ========================================
-- EXPLORAÇÃO DO DATASET
-- ========================================
-- Analisamos a cardinalidade das colunas principais
-- para entender por que user_id é inadequado para particionamento

SELECT 
  COUNT(DISTINCT booking_id) AS total_bookings,
  COUNT(DISTINCT booking_update_id) AS total_updates,
  COUNT(DISTINCT user_id) AS total_users
FROM samples.wanderbricks.booking_updates;

-- Resultado esperado: milhares de user_id únicos (alta cardinalidade)

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC
-- MAGIC ## 🌱 Fase 1: Cenário Greenfield (Tabela Nova)
-- MAGIC
-- MAGIC ### Objetivo
-- MAGIC Demonstrar a **forma ideal** de criar uma tabela com Liquid Clustering desde o início.
-- MAGIC
-- MAGIC ### Estratégia
-- MAGIC * Usamos **CTAS** (Create Table As Select) com cláusula `CLUSTER BY`
-- MAGIC * Escolhemos colunas estratégicas: `property_id` e `status`
-- MAGIC * Estas colunas são frequentemente usadas em filtros WHERE
-- MAGIC
-- MAGIC ### Sintaxe
-- MAGIC ```sql
-- MAGIC CREATE TABLE <nome>
-- MAGIC USING DELTA
-- MAGIC CLUSTER BY (coluna1, coluna2)
-- MAGIC AS SELECT ...
-- MAGIC ```
-- MAGIC
-- MAGIC ### Por Que property_id e status?
-- MAGIC * **property_id**: Queries frequentemente filtram por propriedade específica
-- MAGIC * **status**: Análises comuns filtram por status (confirmado, cancelado, pendente)
-- MAGIC * **Combinação**: Permite data skipping eficiente em queries multi-filtro
-- MAGIC
-- MAGIC ### Passo Crítico: OPTIMIZE
-- MAGIC Após criar a tabela, executamos `OPTIMIZE` para:
-- MAGIC * **Consolidar arquivos pequenos** em arquivos maiores
-- MAGIC * **Aplicar o clustering físico** aos dados
-- MAGIC * **Gerar estatísticas** para data skipping
-- MAGIC
-- MAGIC ⚠️ **Importante**: O `CLUSTER BY` define apenas os metadados. O `OPTIMIZE` efetiva a organização física!
-- MAGIC
-- MAGIC ### Validação
-- MAGIC Usamos `DESCRIBE EXTENDED` para confirmar:
-- MAGIC * Propriedade `clusteringColumns` mostra `["property_id","status"]`
-- MAGIC * Propriedade `delta.feature.clustering` está `supported`

-- COMMAND ----------

-- ========================================
-- FASE 1: CENÁRIO GREENFIELD
-- ========================================
-- Criação de tabela NOVA com Liquid Clustering desde o início
-- Esta é a FORMA IDEAL de implementar clustering

CREATE TABLE demo_bookings_new
USING DELTA
CLUSTER BY (property_id, status)  -- Colunas estratégicas frequentemente filtradas
AS
SELECT *
FROM samples.wanderbricks.booking_updates;

-- CLUSTER BY define apenas os METADADOS de clustering
-- O próximo passo (OPTIMIZE) efetiva a organização física

-- COMMAND ----------

-- ========================================
-- FASE 1: APLICANDO O CLUSTERING FÍSICO
-- ========================================
-- OPTIMIZE consolida arquivos e efetiva a organização física dos dados
-- conforme as colunas definidas no CLUSTER BY

OPTIMIZE demo_bookings_new;

-- COMMAND ----------

-- ========================================
-- FASE 1: VALIDAÇÃO DO CLUSTERING
-- ========================================
-- Verificamos se o Liquid Clustering foi ativado corretamente
-- Procure por:
--   - clusteringColumns: ["property_id","status"]
--   - delta.feature.clustering: supported

DESCRIBE EXTENDED demo_bookings_new;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC
-- MAGIC ## ⚠️ Fase 2: O Anti-Padrão (Particionamento por Alta Cardinalidade)
-- MAGIC
-- MAGIC ### Objetivo
-- MAGIC Demonstrar **o que NÃO fazer**: particionar por coluna de alta cardinalidade.
-- MAGIC
-- MAGIC ### O Problema
-- MAGIC Criamos `demo_chaos_partitioned` com `PARTITIONED BY (user_id)`.
-- MAGIC
-- MAGIC ### Por Que Isso é Ruim?
-- MAGIC
-- MAGIC #### 1. **Explosão de Arquivos Pequenos**
-- MAGIC * Cada `user_id` único cria uma **partição separada**
-- MAGIC * Com milhares de usuários → milhares de diretórios
-- MAGIC * Cada partição pode ter apenas **alguns registros**
-- MAGIC * Resultado: **small files problem**
-- MAGIC
-- MAGIC #### 2. **Degradação de Performance**
-- MAGIC * **Listagem de diretórios** se torna lenta (overhead do filesystem)
-- MAGIC * **Metastore overhead**: milhares de partições para gerenciar
-- MAGIC * **Compactação ineficiente**: OPTIMIZE precisa processar milhares de arquivos
-- MAGIC * **Data skipping limitado**: estatísticas por partição são menos eficazes
-- MAGIC
-- MAGIC #### 3. **Inflexibilidade**
-- MAGIC * Não é possível **alterar a coluna de particionamento** sem reescrever toda a tabela
-- MAGIC * Queries que **não filtram por user_id** fazem full scan de todas as partições
-- MAGIC
-- MAGIC ### Demonstração Prática
-- MAGIC * Limitamos a 100 registros para acelerar a demo
-- MAGIC * Mesmo assim, criamos múltiplas partições
-- MAGIC * `DESCRIBE DETAIL` mostra a estrutura de particionamento
-- MAGIC * Query por `user_id = 100467` funciona, mas com overhead desnecessário
-- MAGIC
-- MAGIC ### Lição Aprendida
-- MAGIC 🚫 **NUNCA particione por colunas de alta cardinalidade**  
-- MAGIC ✅ **Use Liquid Clustering para esses casos**

-- COMMAND ----------

-- ========================================
-- FASE 2: O ANTI-PADRÃO (NÃO FAÇA ISSO!)
-- ========================================
-- Criamos uma tabela PARTICIONADA por user_id (alta cardinalidade)
-- Isso demonstra o PROBLEMA que o Liquid Clustering resolve

CREATE TABLE demo_chaos_partitioned
USING DELTA
PARTITIONED BY (user_id)  -- ⚠️ ERRO: Alta cardinalidade causa explosão de arquivos
AS
SELECT *
FROM samples.wanderbricks.booking_updates
LIMIT 100;  -- Limitamos para acelerar a demo, mas o problema persiste

-- Resultado: Múltiplas partições, cada uma com poucos registros

-- COMMAND ----------

-- ========================================
-- FASE 2: DIAGNÓSTICO DO PROBLEMA
-- ========================================
-- Analisamos a estrutura da tabela particionada
-- Observe:
--   - partitionColumns: ["user_id"]
--   - numFiles: Quantidade elevada de arquivos pequenos

DESCRIBE DETAIL demo_chaos_partitioned;

-- COMMAND ----------

-- ========================================
-- FASE 2: QUERY NA TABELA PARTICIONADA
-- ========================================
-- Esta query funciona, mas com overhead desnecessário:
-- - Precisa listar todas as partições
-- - Acessa apenas uma partição específica
-- - Ineficiente para queries que não filtram por user_id

SELECT *
FROM demo_chaos_partitioned
WHERE user_id = 100467;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC
-- MAGIC ## 🔄 Fase 3: Migração para Liquid Clustering
-- MAGIC
-- MAGIC ### Objetivo
-- MAGIC Demonstrar como **corrigir** uma tabela particionada incorretamente, migrando para Liquid Clustering.
-- MAGIC
-- MAGIC ### O Desafio
-- MAGIC ⚠️ **Limitação do Databricks**: Não é possível usar `ALTER TABLE CLUSTER BY` em tabelas particionadas.
-- MAGIC
-- MAGIC ### A Solução: Estratégia de Migração
-- MAGIC
-- MAGIC #### Passo 1: Criar Nova Tabela com Clustering
-- MAGIC ```sql
-- MAGIC CREATE OR REPLACE TABLE demo_bookings_migration
-- MAGIC USING DELTA
-- MAGIC CLUSTER BY (user_id)
-- MAGIC AS SELECT * FROM demo_chaos_partitioned;
-- MAGIC ```
-- MAGIC
-- MAGIC **O que acontece:**
-- MAGIC * Criamos uma **nova tabela sem particionamento**
-- MAGIC * Definimos `CLUSTER BY (user_id)` desde o início
-- MAGIC * Copiamos todos os dados da tabela particionada
-- MAGIC * A nova tabela **não herda** o particionamento da origem
-- MAGIC
-- MAGIC #### Passo 2: Aplicar OPTIMIZE
-- MAGIC ```sql
-- MAGIC OPTIMIZE demo_bookings_migration;
-- MAGIC ```
-- MAGIC
-- MAGIC **O que acontece:**
-- MAGIC * Consolida arquivos pequenos
-- MAGIC * Aplica o clustering físico por `user_id`
-- MAGIC * Gera estatísticas de data skipping
-- MAGIC * Organiza dados para queries eficientes
-- MAGIC
-- MAGIC #### Passo 3: Validar a Migração
-- MAGIC ```sql
-- MAGIC DESCRIBE DETAIL demo_bookings_migration;
-- MAGIC ```
-- MAGIC
-- MAGIC **Verificamos:**
-- MAGIC * `clusteringColumns` agora mostra `["user_id"]`
-- MAGIC * Não há mais `partitionColumns`
-- MAGIC * Número de arquivos reduzido significativamente
-- MAGIC
-- MAGIC ### Comparação: Antes vs Depois
-- MAGIC
-- MAGIC | Aspecto | Particionado | Liquid Clustering |
-- MAGIC |---------|--------------|-------------------|
-- MAGIC | **Arquivos** | Milhares de pequenos arquivos | Arquivos consolidados otimizados |
-- MAGIC | **Metadados** | Partições no metastore | Estatísticas de clustering |
-- MAGIC | **Flexibilidade** | Fixo (requer reescrita) | Dinâmico (ALTER TABLE) |
-- MAGIC | **Performance** | Degradada (overhead) | Otimizada (data skipping) |
-- MAGIC | **Manutenção** | Complexa | Automática |
-- MAGIC
-- MAGIC ### Estratégia de Cutover em Produção
-- MAGIC
-- MAGIC 1. **Criar tabela nova** com clustering (como fizemos)
-- MAGIC 2. **Validar performance** com queries reais
-- MAGIC 3. **Renomear tabelas** (swap atômico):
-- MAGIC    ```sql
-- MAGIC    ALTER TABLE demo_chaos_partitioned RENAME TO demo_chaos_partitioned_old;
-- MAGIC    ALTER TABLE demo_bookings_migration RENAME TO demo_chaos_partitioned;
-- MAGIC    ```
-- MAGIC 4. **Atualizar aplicações** (se necessário)
-- MAGIC 5. **Monitorar** por período de transição
-- MAGIC 6. **Deletar tabela antiga** após validação completa

-- COMMAND ----------

-- ========================================
-- FASE 3: MIGRAÇÃO - PASSO 1
-- ========================================
-- Criamos uma NOVA tabela com Liquid Clustering
-- copiando os dados da tabela particionada problemática
--
-- IMPORTANTE: Não é possível usar ALTER TABLE CLUSTER BY
-- em tabelas particionadas. A solução é criar uma nova tabela.

CREATE OR REPLACE TABLE demo_bookings_migration
USING DELTA
CLUSTER BY (user_id)  -- Agora usamos clustering em vez de particionamento
AS
SELECT *
FROM demo_chaos_partitioned;

-- A nova tabela NÃO herda o particionamento da origem

-- COMMAND ----------

-- ========================================
-- FASE 3: MIGRAÇÃO - PASSO 2
-- ========================================
-- Aplicamos OPTIMIZE para efetivar a organização física
-- Isso consolida arquivos e aplica o clustering por user_id

OPTIMIZE demo_bookings_migration;

-- Agora os dados estão fisicamente organizados para queries eficientes

-- COMMAND ----------

-- ========================================
-- FASE 3: MIGRAÇÃO - PASSO 3 (VALIDAÇÃO)
-- ========================================
-- Verificamos que a migração foi bem-sucedida
-- Observe:
--   - clusteringColumns: ["user_id"]
--   - partitionColumns: [] (vazio - não há mais partições!)
--   - numFiles: Reduzido significativamente

DESCRIBE DETAIL demo_bookings_migration;

-- COMMAND ----------

-- ========================================
-- FASE 3: QUERY NA TABELA MIGRADA
-- ========================================
-- Mesma query da Fase 2, mas agora com Liquid Clustering
-- Performance melhorada:
-- - Data skipping eficiente
-- - Sem overhead de listagem de partições
-- - Arquivos consolidados

SELECT *
FROM demo_bookings_migration
WHERE user_id = 100467;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC
-- MAGIC ## 📊 Fase 4: Z-Ordering e Migração para Liquid Clustering
-- MAGIC
-- MAGIC ### Objetivo
-- MAGIC Demonstrar o **Z-Ordering** (técnica legacy) e como migrar para **Liquid Clustering** (técnica moderna).
-- MAGIC
-- MAGIC ### O Que é Z-Ordering?
-- MAGIC
-- MAGIC **Z-Ordering** é uma técnica de otimização do Delta Lake que:
-- MAGIC * **Organiza dados usando curvas Z** (space-filling curves)
-- MAGIC * **Coloca dados relacionados próximos** fisicamente
-- MAGIC * **Melhora data skipping** para múltiplas colunas
-- MAGIC * Foi a **solução padrão** antes do Liquid Clustering (DBR < 13.3)
-- MAGIC
-- MAGIC ### Z-Ordering vs Liquid Clustering
-- MAGIC
-- MAGIC | Aspecto | Z-Ordering | Liquid Clustering |
-- MAGIC |---------|------------|-------------------|
-- MAGIC | **Disponibilidade** | DBR 7.0+ | DBR 13.3 LTS+ |
-- MAGIC | **Sintaxe** | `OPTIMIZE ... ZORDER BY` | `CLUSTER BY` + `OPTIMIZE` |
-- MAGIC | **Flexibilidade** | Fixo (requer re-ZORDER) | Dinâmico (ALTER TABLE) |
-- MAGIC | **Manutenção** | Manual (executar ZORDER) | Automática (incremental) |
-- MAGIC | **Metadados** | Não armazena configuração | Armazena em table properties |
-- MAGIC | **Performance** | Boa | Melhor (otimizado) |
-- MAGIC | **Recomendação** | Legacy | **Preferido** |
-- MAGIC
-- MAGIC ### Por Que Migrar?
-- MAGIC
-- MAGIC #### ✅ Vantagens do Liquid Clustering
-- MAGIC 1. **Flexibilidade**: Altere colunas sem reescrever dados
-- MAGIC 2. **Automação**: OPTIMIZE incremental automático
-- MAGIC 3. **Metadados**: Configuração persistida na tabela
-- MAGIC 4. **Performance**: Algoritmos otimizados para alta cardinalidade
-- MAGIC 5. **Futuro**: Suporte ativo e melhorias contínuas
-- MAGIC
-- MAGIC #### ⚠️ Quando Manter Z-Ordering
-- MAGIC * DBR < 13.3 (Liquid Clustering não disponível)
-- MAGIC * Tabelas pequenas onde migração não justifica esforço
-- MAGIC * Ambientes com restrições de upgrade
-- MAGIC
-- MAGIC ### Estratégia de Migração
-- MAGIC
-- MAGIC A migração de Z-Ordering para Liquid Clustering é **simples e não destrutiva**:
-- MAGIC
-- MAGIC 1. **Aplicar ALTER TABLE** com `CLUSTER BY` na tabela existente
-- MAGIC 2. **Executar OPTIMIZE** para reorganizar dados fisicamente
-- MAGIC 3. **Validar** com `DESCRIBE DETAIL`
-- MAGIC
-- MAGIC ✅ **Vantagem**: Migração IN-PLACE - sem criar nova tabela ou copiar dados!

-- COMMAND ----------

-- DBTITLE 1,Fase 4 - Criar tabela com Z-Ordering
-- ========================================
-- FASE 4: CRIANDO TABELA COM Z-ORDERING
-- ========================================
-- Demonstramos a técnica LEGACY de otimização
-- Z-Ordering foi a solução padrão antes do Liquid Clustering

CREATE OR REPLACE TABLE demo_bookings_zorder
USING DELTA
AS
SELECT *
FROM samples.wanderbricks.booking_updates

-- Nota: A tabela é criada SEM otimização inicial
-- O Z-Ordering será aplicado no próximo passo

-- COMMAND ----------

-- DBTITLE 1,Fase 4 - Aplicar Z-Ordering
-- ========================================
-- FASE 4: APLICANDO Z-ORDERING
-- ========================================
-- Executamos OPTIMIZE com ZORDER BY para organizar os dados
-- Escolhemos booking_id e property_id como colunas de ordenação

OPTIMIZE demo_bookings_zorder
ZORDER BY (booking_id, property_id);

-- ⚠️ PROBLEMA: Esta configuração NÃO é persistida!
-- Se executarmos OPTIMIZE novamente sem ZORDER BY, a organização é perdida
-- Precisamos SEMPRE lembrar de incluir ZORDER BY em cada OPTIMIZE

-- COMMAND ----------

-- DBTITLE 1,Fase 4 - Validar Z-Ordering
-- ========================================
-- FASE 4: VALIDAÇÃO DO Z-ORDERING
-- ========================================
-- Verificamos a estrutura da tabela
-- Observe que NÃO há propriedade "zorderColumns" ou similar
-- A configuração de Z-Ordering não fica armazenada nos metadados

DESCRIBE DETAIL demo_bookings_zorder;

-- ⚠️ Limitação: Não há como saber quais colunas foram usadas no ZORDER
-- Isso dificulta a manutenção e documentação

-- COMMAND ----------

-- DBTITLE 1,Fase 4 - Query na tabela Z-Ordered
-- ========================================
-- FASE 4: QUERY NA TABELA COM Z-ORDERING
-- ========================================
-- Testamos uma query que filtra pelas colunas Z-Ordered
-- Performance é boa devido ao data skipping

SELECT *
FROM demo_bookings_zorder
WHERE booking_id = 1699
  AND property_id = 1537;

-- Performance: Boa (data skipping funciona)
-- Problema: Manutenção manual necessária

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC
-- MAGIC ## 🔄 Fase 4: Migração de Z-Ordering para Liquid Clustering
-- MAGIC
-- MAGIC ### Objetivo
-- MAGIC Demonstrar como **modernizar** uma tabela que usa Z-Ordering para Liquid Clustering.
-- MAGIC
-- MAGIC ### Processo de Migração
-- MAGIC
-- MAGIC #### Passo 1: Aplicar Liquid Clustering na Tabela Existente
-- MAGIC ```sql
-- MAGIC ALTER TABLE demo_bookings_zorder 
-- MAGIC CLUSTER BY (booking_id, property_id);
-- MAGIC ```
-- MAGIC
-- MAGIC **O que acontece:**
-- MAGIC * **Migração IN-PLACE** - não precisa criar nova tabela!
-- MAGIC * Usamos as **mesmas colunas** do Z-Ordering anterior
-- MAGIC * A configuração é **persistida nos metadados**
-- MAGIC * **Não há cópia de dados** - muito mais rápido!
-- MAGIC
-- MAGIC ✅ **Vantagem**: Migração simples e não destrutiva
-- MAGIC
-- MAGIC #### Passo 2: Aplicar OPTIMIZE
-- MAGIC ```sql
-- MAGIC OPTIMIZE demo_bookings_zorder;
-- MAGIC ```
-- MAGIC
-- MAGIC **Diferença importante:**
-- MAGIC * **Antes (Z-Ordering)**: Precisava `OPTIMIZE ... ZORDER BY (booking_id, property_id)` toda vez
-- MAGIC * **Depois (Liquid Clustering)**: Apenas `OPTIMIZE` (configuração já está salva!)
-- MAGIC
-- MAGIC #### Passo 3: Validar a Migração
-- MAGIC ```sql
-- MAGIC DESCRIBE DETAIL demo_bookings_zorder;
-- MAGIC ```
-- MAGIC
-- MAGIC **Verificamos:**
-- MAGIC * `clusteringColumns` mostra `["booking_id","property_id"]`
-- MAGIC * Configuração **persistida** (não precisa lembrar)
-- MAGIC * Futuras otimizações são **automáticas**
-- MAGIC
-- MAGIC ### Comparação Prática: Manutenção
-- MAGIC
-- MAGIC #### Com Z-Ordering (Antigo)
-- MAGIC ```sql
-- MAGIC -- Toda vez que otimizar, precisa especificar:
-- MAGIC OPTIMIZE demo_bookings_zorder ZORDER BY (booking_id, property_id);
-- MAGIC
-- MAGIC -- Se esquecer o ZORDER BY:
-- MAGIC OPTIMIZE demo_bookings_zorder;  -- ❌ Perde a organização!
-- MAGIC ```
-- MAGIC
-- MAGIC #### Com Liquid Clustering (Moderno)
-- MAGIC ```sql
-- MAGIC -- Apenas uma vez:
-- MAGIC ALTER TABLE demo_bookings_zorder CLUSTER BY (booking_id, property_id);
-- MAGIC
-- MAGIC -- Depois, sempre simples:
-- MAGIC OPTIMIZE demo_bookings_zorder;  -- ✅ Mantém clustering!
-- MAGIC ```
-- MAGIC
-- MAGIC ### Benefícios da Migração
-- MAGIC
-- MAGIC 1. **Simplicidade**: Apenas um ALTER TABLE - sem recriar tabela
-- MAGIC 2. **Não destrutivo**: Dados permanecem intactos
-- MAGIC 3. **Sem downtime**: Tabela continua disponível durante migração
-- MAGIC 4. **Documentação**: Metadados mostram a configuração
-- MAGIC 5. **Flexibilidade**: Pode alterar colunas novamente com ALTER TABLE
-- MAGIC 6. **Automação**: Suporte a Auto Optimize
-- MAGIC 7. **Performance**: Algoritmos mais eficientes
-- MAGIC
-- MAGIC ### Migração Completa em 3 Comandos
-- MAGIC
-- MAGIC ```sql
-- MAGIC -- 1. Aplicar Liquid Clustering
-- MAGIC ALTER TABLE demo_bookings_zorder CLUSTER BY (booking_id, property_id);
-- MAGIC
-- MAGIC -- 2. Reorganizar dados fisicamente
-- MAGIC OPTIMIZE demo_bookings_zorder;
-- MAGIC
-- MAGIC -- 3. Validar
-- MAGIC DESCRIBE DETAIL demo_bookings_zorder;
-- MAGIC ```
-- MAGIC
-- MAGIC ⚠️ **Importante**: A partir deste momento, NUNCA mais use `ZORDER BY`. Apenas `OPTIMIZE` simples!

-- COMMAND ----------

-- DBTITLE 1,Fase 4 - Migração para Liquid Clustering
-- ========================================
-- FASE 4: MIGRAÇÃO - PASSO 1
-- ========================================
-- Migramos a tabela existente para Liquid Clustering
-- usando ALTER TABLE (sem precisar recriar a tabela!)

ALTER TABLE demo_bookings_zorder 
CLUSTER BY (booking_id, property_id, user_id);  -- Mesmas colunas do ZORDER

-- ✅ VANTAGEM: Migração IN-PLACE!
-- Não precisa criar nova tabela ou copiar dados
-- A configuração CLUSTER BY fica PERSISTIDA nos metadados
-- Próximo passo: OPTIMIZE para reorganizar os dados fisicamente

-- COMMAND ----------

-- DBTITLE 1,Fase 4 - Aplicar OPTIMIZE na tabela migrada
-- ========================================
-- FASE 4: MIGRAÇÃO - PASSO 2
-- ========================================
-- Aplicamos OPTIMIZE para efetivar o clustering físico
-- Note que NÃO precisamos especificar as colunas!

OPTIMIZE demo_bookings_zorder;

-- ✅ Compare com o que era necessário antes:
--    Antes:  OPTIMIZE demo_bookings_zorder ZORDER BY (booking_id, property_id)
--    Agora:  OPTIMIZE demo_bookings_zorder

-- Muito mais simples e menos propenso a erros!
-- A configuração de clustering já está persistida nos metadados

-- COMMAND ----------

-- DBTITLE 1,Fase 4 - Validar migração
-- ========================================
-- FASE 4: MIGRAÇÃO - PASSO 3 (VALIDAÇÃO)
-- ========================================
-- Verificamos que a migração foi bem-sucedida
-- Observe:
--   - clusteringColumns: ["booking_id","property_id"]
--   - delta.feature.clustering: supported
--   - Configuração VISÍVEL nos metadados!

DESCRIBE DETAIL demo_bookings_zorder;

-- ✅ Agora qualquer pessoa pode ver quais colunas estão configuradas
-- Facilita documentação e manutenção
-- A tabela foi migrada IN-PLACE sem recriar!

-- COMMAND ----------

-- DBTITLE 1,Fase 4 - Query na tabela migrada
-- ========================================
-- FASE 4: QUERY NA TABELA MIGRADA
-- ========================================
-- Mesma query de antes, mas agora com Liquid Clustering ativo
-- Performance equivalente ou melhor que Z-Ordering

SELECT *
FROM demo_bookings_zorder
WHERE booking_id = 1699
  AND property_id = 1537;

-- Performance: Excelente (data skipping otimizado)
-- Manutenção: Simplificada (OPTIMIZE sem parâmetros)
-- Flexibilidade: Alta (pode alterar colunas com ALTER TABLE)

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC
-- MAGIC ## 🎯 Melhores Práticas e Recomendações
-- MAGIC
-- MAGIC ### 1. Escolha de Colunas para Clustering
-- MAGIC
-- MAGIC #### ✅ Boas Escolhas
-- MAGIC * Colunas **frequentemente usadas em WHERE**
-- MAGIC * Colunas com **cardinalidade média a alta** (centenas a milhões de valores)
-- MAGIC * Colunas usadas em **JOINs**
-- MAGIC * Até **4 colunas** (ordem importa: mais seletiva primeiro)
-- MAGIC
-- MAGIC #### ❌ Más Escolhas
-- MAGIC * Colunas de **baixa cardinalidade** (< 100 valores únicos)
-- MAGIC * Colunas **raramente filtradas**
-- MAGIC * Colunas com **distribuição muito desigual** (skewed)
-- MAGIC * Mais de 4 colunas (diminui efetividade)
-- MAGIC
-- MAGIC ### 2. Manutenção e Otimização
-- MAGIC
-- MAGIC #### OPTIMIZE Regular
-- MAGIC ```sql
-- MAGIC OPTIMIZE <tabela>;
-- MAGIC ```
-- MAGIC * Execute após **grandes cargas de dados**
-- MAGIC * Configure **Auto Optimize** para tabelas com writes frequentes:
-- MAGIC   ```sql
-- MAGIC   ALTER TABLE <tabela> SET TBLPROPERTIES (
-- MAGIC     'delta.autoOptimize.optimizeWrite' = 'true',
-- MAGIC     'delta.autoOptimize.autoCompact' = 'true'
-- MAGIC   );
-- MAGIC   ```
-- MAGIC
-- MAGIC #### Monitoramento
-- MAGIC ```sql
-- MAGIC DESCRIBE DETAIL <tabela>;
-- MAGIC ```
-- MAGIC Verifique:
-- MAGIC * `numFiles`: Deve ser razoável (não milhares)
-- MAGIC * `sizeInBytes`: Tamanho total da tabela
-- MAGIC * `clusteringColumns`: Confirma configuração
-- MAGIC
-- MAGIC ### 3. Alteração de Colunas de Clustering
-- MAGIC
-- MAGIC **Vantagem do Liquid Clustering**: Você pode mudar!
-- MAGIC
-- MAGIC ```sql
-- MAGIC ALTER TABLE <tabela> CLUSTER BY (nova_coluna1, nova_coluna2);
-- MAGIC OPTIMIZE <tabela>;
-- MAGIC ```
-- MAGIC
-- MAGIC * Não requer reescrita completa imediata
-- MAGIC * Novos dados usam novo clustering
-- MAGIC * OPTIMIZE gradualmente reorganiza dados antigos
-- MAGIC
-- MAGIC ### 4. Quando Re-avaliar a Estratégia
-- MAGIC
-- MAGIC 🔍 **Sinais de que precisa ajustar:**
-- MAGIC * Queries lentas mesmo com clustering
-- MAGIC * Padrões de consulta mudaram
-- MAGIC * Crescimento desproporcional de arquivos
-- MAGIC * Novas colunas se tornaram críticas para filtros
-- MAGIC
-- MAGIC ### 5. Comparação com Z-Ordering
-- MAGIC
-- MAGIC | Aspecto | Liquid Clustering | Z-Ordering |
-- MAGIC |---------|-------------------|------------|
-- MAGIC | **Flexibilidade** | Alta (ALTER TABLE) | Baixa (fixo) |
-- MAGIC | **Manutenção** | Automática | Manual (OPTIMIZE ZORDER) |
-- MAGIC | **Performance** | Melhor para alta cardinalidade | Bom para múltiplas colunas |
-- MAGIC | **Recomendação** | **Preferido para novos projetos** | Legacy (DBR < 13) |
-- MAGIC
-- MAGIC ⚠️ **Importante**: Não é possível usar Liquid Clustering e Z-Ordering na mesma tabela!

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC
-- MAGIC ## 🎓 Conclusão e Próximos Passos
-- MAGIC
-- MAGIC ### Resumo do Que Aprendemos
-- MAGIC
-- MAGIC 1. **Liquid Clustering é a solução moderna** para organização de dados de alta cardinalidade
-- MAGIC 2. **Particionamento tradicional** deve ser reservado para baixa cardinalidade
-- MAGIC 3. **Migração de tabelas particionadas** é possível através de recriação de tabela
-- MAGIC 4. **Z-Ordering é legacy** - Liquid Clustering oferece manutenção mais simples
-- MAGIC 5. **Migração de Z-Ordering** para Liquid Clustering é direta e não destrutiva
-- MAGIC 6. **OPTIMIZE é essencial** para efetivar o clustering físico
-- MAGIC 7. **Flexibilidade** é a grande vantagem: podemos alterar colunas sem reescrita completa
-- MAGIC
-- MAGIC ### Checklist de Implementação
-- MAGIC
-- MAGIC #### Para Tabelas Novas (Greenfield)
-- MAGIC - [ ] Identificar colunas de alta cardinalidade usadas em filtros
-- MAGIC - [ ] Criar tabela com `CLUSTER BY`
-- MAGIC - [ ] Executar `OPTIMIZE` após carga inicial
-- MAGIC - [ ] Configurar Auto Optimize se houver writes frequentes
-- MAGIC - [ ] Validar com `DESCRIBE DETAIL`
-- MAGIC
-- MAGIC #### Para Migração de Tabelas Particionadas
-- MAGIC - [ ] Analisar padrões de consulta atuais
-- MAGIC - [ ] Identificar problemas de performance (small files, partições excessivas)
-- MAGIC - [ ] Criar tabela nova com clustering
-- MAGIC - [ ] Validar performance em ambiente de teste
-- MAGIC - [ ] Planejar cutover (renomeação, downtime)
-- MAGIC - [ ] Executar migração
-- MAGIC - [ ] Monitorar performance pós-migração
-- MAGIC - [ ] Remover tabela antiga após período de validação
-- MAGIC
-- MAGIC #### Para Migração de Z-Ordering
-- MAGIC - [ ] Identificar tabelas que usam `OPTIMIZE ... ZORDER BY`
-- MAGIC - [ ] Documentar colunas usadas no ZORDER BY
-- MAGIC - [ ] Criar tabela nova com `CLUSTER BY` usando as mesmas colunas
-- MAGIC - [ ] Executar `OPTIMIZE` (sem precisar especificar colunas!)
-- MAGIC - [ ] Comparar performance entre Z-Order e Liquid Clustering
-- MAGIC - [ ] Fazer cutover (renomear tabelas)
-- MAGIC - [ ] Atualizar scripts de manutenção (remover ZORDER BY)
-- MAGIC - [ ] Validar que OPTIMIZE simples mantém clustering
-- MAGIC
-- MAGIC ### Recursos Adicionais
-- MAGIC
-- MAGIC 📚 **Documentação Oficial:**
-- MAGIC * [Liquid Clustering Documentation](https://docs.databricks.com/delta/clustering.html)
-- MAGIC * [Delta Lake Optimization](https://docs.databricks.com/delta/optimize.html)
-- MAGIC * [Z-Ordering (Legacy)](https://docs.databricks.com/delta/data-skipping.html)
-- MAGIC
-- MAGIC 🔬 **Experimentos Sugeridos:**
-- MAGIC 1. Compare performance de queries antes/depois do clustering
-- MAGIC 2. Teste diferentes combinações de colunas
-- MAGIC 3. Meça impacto do OPTIMIZE em tabelas grandes
-- MAGIC 4. Analise planos de execução (EXPLAIN) para entender data skipping
-- MAGIC 5. Compare tempo de manutenção: Z-Order vs Liquid Clustering
-- MAGIC
-- MAGIC ### Perguntas Frequentes
-- MAGIC
-- MAGIC **Q: Posso usar Liquid Clustering em qualquer versão do Databricks?**  
-- MAGIC A: Requer DBR 13.3 LTS ou superior.
-- MAGIC
-- MAGIC **Q: Liquid Clustering substitui completamente o particionamento?**  
-- MAGIC A: Não. Particionamento ainda é útil para baixa cardinalidade (país, ano, etc.).
-- MAGIC
-- MAGIC **Q: Quantas colunas posso usar no CLUSTER BY?**  
-- MAGIC A: Até 4 colunas. Mais que isso reduz efetividade.
-- MAGIC
-- MAGIC **Q: Preciso executar OPTIMIZE toda vez que insiro dados?**  
-- MAGIC A: Não necessariamente. Configure Auto Optimize ou execute periodicamente (diário/semanal).
-- MAGIC
-- MAGIC **Q: Posso combinar Liquid Clustering com particionamento?**  
-- MAGIC A: Não. São estratégias mutuamente exclusivas.
-- MAGIC
-- MAGIC **Q: Devo migrar todas as tabelas Z-Ordered para Liquid Clustering?**  
-- MAGIC A: Priorize tabelas grandes, com writes frequentes, ou onde a manutenção manual é problemática. Tabelas pequenas e estáticas podem permanecer com Z-Order.
-- MAGIC
-- MAGIC **Q: Posso usar Z-Ordering e Liquid Clustering na mesma tabela?**  
-- MAGIC A: Não. São técnicas mutuamente exclusivas.
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ## 🚀 Parabéns!
-- MAGIC
-- MAGIC Você completou a demonstração completa do Liquid Clustering! 
-- MAGIC
-- MAGIC Agora você entende:
-- MAGIC * Como criar tabelas com clustering (greenfield)
-- MAGIC * Por que evitar particionamento de alta cardinalidade
-- MAGIC * Como migrar tabelas particionadas existentes
-- MAGIC * Diferenças entre Z-Ordering e Liquid Clustering
-- MAGIC * Como modernizar tabelas Z-Ordered
-- MAGIC * Melhores práticas de manutenção
-- MAGIC
-- MAGIC **Boa aula! 🎉**
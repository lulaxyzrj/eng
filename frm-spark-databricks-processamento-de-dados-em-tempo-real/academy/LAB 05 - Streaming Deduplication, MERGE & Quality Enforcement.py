# Databricks notebook source
# MAGIC %md
# MAGIC #Deduplicação 
# MAGIC Neste Notebook, você aprenderá como eliminar registros duplicados enquanto trabalha com Structured Streaming e Delta Lake. 
# MAGIC
# MAGIC Embora o Spark Structured Streaming ofereça garantias de processamento exatamente uma vez, muitos sistemas de origem introduzirão registros duplicados, que devem ser removidos para que os joins e atualizações produzam resultados logicamente corretos em consultas a jusante. 
# MAGIC
# MAGIC ##Objetivos de Aprendizagem 
# MAGIC No final desta lição, você deve ser capaz de: 
# MAGIC - Aplicar dropDuplicates para streaming de dados 
# MAGIC - Use marca d'água para gerenciar informações do estado 
# MAGIC - Escreva um MERGE somente de inserção para impedir a inserção de registros duplicados em uma tabela Delta 
# MAGIC - Use foreachBatch para executar um upsert de streaming
# MAGIC
# MAGIC
# MAGIC Pré-Requisitos para o LAB 6:
# MAGIC - Acesso a um workspace Databricks.
# MAGIC - Acesso a um SQL Warehouse (Opcional).
# MAGIC - Acesso a um cluster.
# MAGIC - Acesso a um catálogo com as seguintes permissões:
# MAGIC - USE CATALOG, CREATE SCHEMA e CREATE TABLE no catálogo

# COMMAND ----------

# DBTITLE 1,Importanto libs
from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %run ./utils/simula_deduplicado_bronze

# COMMAND ----------

# MAGIC %md
# MAGIC ##Identificar Registros Duplicados
# MAGIC Uma vez que a Kafka fornece garantias pelo menos uma vez sobre a entrega de dados, todos os consumidores da Kafka devem estar preparados para lidar com registros duplicados.
# MAGIC
# MAGIC Os métodos de duplicação mostrados aqui também podem ser aplicados quando necessário em outras partes de suas aplicações Delta Lake.
# MAGIC
# MAGIC Vamos começar identificando o número de registros duplicados na tabela de bronze.

# COMMAND ----------

count_bronze = (spark.read
              .table("bronze.gcn.lab_deduplication")    
              .count())

print(count_bronze)

# COMMAND ----------

count_bronze_deduplicate = (spark.read
                  .table("bronze.gcn.lab_deduplication")
                  .dropDuplicates(["timestamp", "topic"])
                )

count_bronze_count = count_bronze_deduplicate.count()

print(count_bronze_count)

# COMMAND ----------

spark.sql("select * from bronze.gcn.lab_deduplication limit 5").display()

# COMMAND ----------

# MAGIC %md
# MAGIC Note que aqui nós estamos escolhendo aplicar a deduplicação no nível da camada silver ao invés da camada bronze. 
# MAGIC
# MAGIC Enquanto estamos armazenando alguns registros duplicados, nossa tabela bronze mantém um histórico do verdadeiro estado de nossa fonte de streaming, apresentando todos os registros à medida que chegaram (com alguns metadados adicionais gravados). 
# MAGIC
# MAGIC Isso nos permite recriar qualquer estado do nosso sistema a frente, se necessário, e evita a perda potencial de dados devido à imposição de qualidade na ingestão inicial, bem como minimizar as latências para a ingestão de dados.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Realizando uma leitura stream na bronze  

# COMMAND ----------

df_stream = (spark.readStream
                  .table("bronze.gcn.lab_deduplication")
                  .selectExpr("offset",
                              "topic",
                              "value",
                              "cast(ingestion_blob_time as timestamp) as ingestion_blob_time",
                              "cast(from_unixtime(timestamp[1]/1000) as timestamp) as timestamp"
                              )
        )

# COMMAND ----------

df_stream.display()

# COMMAND ----------

# MAGIC %md
# MAGIC Quando trabalhamos com dados em tempo real ou próximo de tempo real (streaming), remover dados repetidos é mais difícil do que quando os dados são estáticos.
# MAGIC
# MAGIC Para cada pequeno micro-batch de dados que chega, precisamos verificar duas coisas:
# MAGIC 1. Se dentro deste grupo não há informações repetidas
# MAGIC 2. Se estas informações já não existem na tabela final
# MAGIC
# MAGIC O Spark Structured Streaming consegue acompanhar quais dados já passaram por ele, evitando duplicações tanto dentro de um grupo quanto entre grupos diferentes e com o tempo, esse histórico vai crescendo muito. 
# MAGIC
# MAGIC Para resolver isso, usamos um limite de tempo (watermark) - assim o sistema só precisa se lembrar dos dados que chegaram neste período, tornando tudo mais eficiente.
# MAGIC
# MAGIC Esta é uma melhoria da nossa consulta anterior:

# COMMAND ----------

df_stream_deduped = (spark.readStream
                  .table("bronze.gcn.lab_deduplication")
                  .selectExpr("offset",
                              "topic",
                              "value",
                              "cast(ingestion_blob_time as timestamp) as ingestion_blob_time",
                              "cast(from_unixtime(timestamp[1]/1000) as timestamp) as timestamp"
                              )
                  .withWatermark("timestamp", "30 seconds")
                  .dropDuplicates(["timestamp", "topic"])
        )

# COMMAND ----------

# MAGIC %md 
# MAGIC - .withWatermark("timestamp", "30 seconds"):
# MAGIC   - Define um watermark na coluna timestamp com um atraso de 30 segundos.
# MAGIC   - Isso significa que o sistema irá tolerar dados que cheguem até 30 segundos após o tempo indicado no campo timestamp.
# MAGIC   - O watermark é usado para controlar o estado do processamento e descartar dados que cheguem muito atrasados, ajudando a evitar o acúmulo excessivo de estado e a garantir a eficiência do processamento.
# MAGIC - .dropDuplicates(["timestamp", "topic"]):
# MAGIC   - Remove linhas duplicadas com base nas colunas timestamp e topic dentro da janela definida pelo watermark.
# MAGIC   - Se duas ou mais linhas tiverem os mesmos valores para timestamp e topic e chegarem dentro do intervalo de watermark, apenas a primeira será mantida e as outras serão descartadas.
# MAGIC   - Isso garante que apenas registros únicos sejam processados, evitando o processamento duplicado de eventos.

# COMMAND ----------

query = (df_stream_deduped.writeStream
                   .option("checkpointLocation", "/Volumes/silver/gcn/_checkpoints/lab_deduplication")
                   .trigger(availableNow=True)
                   .table("silver.gcn.lab_deduplication")
                   )

query.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from silver.gcn.lab_deduplication

# COMMAND ----------

# MAGIC %md
# MAGIC # Insert Only Merge
# MAGIC
# MAGIC O Delta Lake possui funcionalidade otimizada para operações de `MERGE` apenas com `INSERT`. 
# MAGIC
# MAGIC Esta operação permite a remoção de dados duplicados enquanto gravamos o dado na nossa camada SILVER.

# COMMAND ----------

# MAGIC %run ./utils/simula_deduplicado_bronze_merge

# COMMAND ----------

count_bronze = (spark.read
              .table("bronze.gcn.lab_merge")    
              .count())

print(count_bronze)

# COMMAND ----------

count_bronze_deduplicate = (spark.read
                  .table("bronze.gcn.lab_deduplication")
                  .dropDuplicates(["timestamp", "topic"])
                )

count_bronze_count = count_bronze_deduplicate.count()

print(count_bronze_count)

# COMMAND ----------

df_stream_merge = (spark.readStream
                  .table("bronze.gcn.lab_merge")
                  .selectExpr("offset",
                              "topic",
                              "value",
                              "cast(ingestion_blob_time as timestamp) as ingestion_blob_time",
                              "cast(from_unixtime(timestamp[1]/1000) as timestamp) as timestamp"
                              )
        )

# COMMAND ----------

sql_merge_query = """
MERGE INTO silver.gcn.lab_merge t
USING stream_update s
ON t.timestamp = s.timestamp AND t.topic = s.topic
WHEN NOT MATCHED THEN INSERT *
"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## Definindo uma função de Microbatch (`foreachBatch`)
# MAGIC
# MAGIC - O método `foreachBatch` do Spark Structured Streaming, permite criarmos lógicas customizadas para gravação
# MAGIC - A lógica aplicada durante o `foreachBatch` aborda o `microbatch` como se fosse um `batch` ao invés de um streaming

# COMMAND ----------

class Upsert:
    def __init__(self, sql_merge_query, update_temp="stream_update"):
        self.sql_merge_query = sql_merge_query
        self.update_temp = update_temp 
        
    def upsert_to_delta(self, microBatchDF, batch):
        microBatchDF.createOrReplaceTempView(self.update_temp)
        microBatchDF._jdf.sparkSession().sql(self.sql_merge_query)

# COMMAND ----------

# MAGIC %md
# MAGIC Passando a lógica do do nosso `MERGE` para a classe Upsert

# COMMAND ----------

streaming_merge = Upsert(sql_merge_query)

# COMMAND ----------

# MAGIC %md
# MAGIC Como estamos usando SQL na nossa lógica, temos que criar a tabela de destino antes

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS silver.gcn.lab_merge
# MAGIC (offset int, topic string, value string, ingestion_blob_time timestamp, timestamp timestamp)

# COMMAND ----------

query = (df_stream_merge.writeStream
                   .foreachBatch(streaming_merge.upsert_to_delta)
                   .outputMode("update")
                   .option("checkpointLocation", "/Volumes/silver/gcn/_checkpoints/lab_merge")
                   .trigger(availableNow=True)
                   .start())

query.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from silver.gcn.lab_merge 

# COMMAND ----------

print("Carregando batch 3")
df = spark.read.format("json").load("/Volumes/landing/gcn/gcn/arquivos/")
df.write.format("delta").mode("append").saveAsTable("bronze.gcn.lab_merge")
print("Fim do batch 3")

# COMMAND ----------

spark.sql("""select count(1) from bronze.gcn.lab_merge""").display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Streaming Deduplication & Upsert

# COMMAND ----------

print("Carregando batch 4")
df = spark.read.format("json").load("/Volumes/landing/gcn/gcn/arquivos/")
df.write.format("delta").mode("append").saveAsTable("bronze.gcn.lab_merge")
print("Fim do batch 4")

# COMMAND ----------

spark.sql("""select count(1) from bronze.gcn.lab_merge""").display()

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS silver.gcn.lab_dedup_merge
# MAGIC (offset int, topic string, value string, ingestion_blob_time timestamp, timestamp timestamp)

# COMMAND ----------

sql_query = """
MERGE INTO silver.gcn.lab_dedup_merge t
USING stream_update s
ON t.timestamp = s.timestamp AND t.topic = s.topic
WHEN NOT MATCHED THEN INSERT *
"""

# COMMAND ----------

streaming_merge = Upsert(sql_query)

# COMMAND ----------

df_stream_deduped = (spark.readStream
                  .table("bronze.gcn.lab_merge")
                  .selectExpr("offset",
                              "topic",
                              "value",
                              "cast(ingestion_blob_time as timestamp) as ingestion_blob_time",
                              "cast(from_unixtime(timestamp[1]/1000) as timestamp) as timestamp"
                              )
                  .withWatermark("timestamp", "30 seconds")
                  .dropDuplicates(["timestamp", "topic"])
        )

# COMMAND ----------

query = (df_stream_deduped.writeStream
                   .foreachBatch(streaming_merge.upsert_to_delta)
                   .outputMode("update")
                   .option("checkpointLocation", "/Volumes/silver/gcn/_checkpoints/lab_dedup_merge")
                   .trigger(availableNow=True)
                   .start())

query.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from silver.gcn.lab_dedup_merge

# COMMAND ----------

print("Carregando batch 5")
df = spark.read.format("json").load("/Volumes/landing/gcn/gcn/arquivos/")
df.write.format("delta").mode("append").saveAsTable("bronze.gcn.lab_merge")
print("Fim do batch 5")

# COMMAND ----------

# MAGIC %md
# MAGIC #Quality Enforcement
# MAGIC Uma das principais vantagens do Delta Lake é garantir a qualidade dos dados. Além da validação automática do esquema (schema), podemos adicionar verificações extras para garantir que apenas dados que atendam aos nossos critérios sejam armazenados no Lakehouse.
# MAGIC
# MAGIC Vamos ver algumas formas de garantir a qualidade dos dados, incluindo recursos específicos do Databricks e princípios gerais de design.
# MAGIC
# MAGIC Objetivos de Aprendizado:
# MAGIC - Adicionar regras de validação em tabelas Delta
# MAGIC - Entender e implementar uma tabela de quarentena
# MAGIC - Aplicar lógica para adicionar marcadores de qualidade nas tabelas Delta
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ##Table Constrainst on Databricks
# MAGIC
# MAGIC É possível utilizarmos [table constraints](https://docs.databricks.com/en/tables/constraints.html) no Databricks quando trabalhamos com tabelas Delta.
# MAGIC
# MAGIC As constrainst aplicam filtros booleanos nas colunas e previne que dados que não passem pelo filtro sejam inseridos no destino.

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE silver.gcn.lab_deduplication ADD CONSTRAINT date_within_range CHECK (timestamp > '2025-02-01');

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS silver.gcn.lab_constraints
# MAGIC (offset bigint, topic string, value string, ingestion_blob_time timestamp, timestamp timestamp)

# COMMAND ----------

# MAGIC %sql 
# MAGIC desc extended silver.gcn.lab_constraints

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE silver.gcn.lab_constraints ADD CONSTRAINT date_within_range CHECK (timestamp > '2025-02-01');

# COMMAND ----------

# MAGIC %sql 
# MAGIC desc extended silver.gcn.lab_constraints

# COMMAND ----------

df_stream_deduped = (spark.readStream
                  .table("bronze.gcn.lab_deduplication")
                  .selectExpr("offset",
                              "topic",
                              "value",
                              "cast(ingestion_blob_time as timestamp) as ingestion_blob_time",
                              "cast(from_unixtime(timestamp[1]/1000) as timestamp) as timestamp"
                              )
                  .withWatermark("timestamp", "30 seconds")
                  .dropDuplicates(["timestamp", "topic"])
        )

# COMMAND ----------

query = (df_stream_deduped.writeStream
                   .option("checkpointLocation", "/Volumes/silver/gcn/_checkpoints/lab_constraints")
                   .trigger(availableNow=True)
                   .table("silver.gcn.lab_constraints")
                   )

query.awaitTermination()

# COMMAND ----------

from pyspark.sql.functions import col

# Filter out rows that violate the CHECK constraint
df_filtered = df_stream_deduped.filter(col("timestamp") > '2025-02-01')

query = (df_filtered.writeStream
                   .option("checkpointLocation", "/Volumes/silver/gcn/_checkpoints/lab_constraints")
                   .trigger(availableNow=True)
                   .table("silver.gcn.lab_constraints")
                   )

query.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC select min(timestamp) 
# MAGIC from silver.gcn.lab_constraints

# COMMAND ----------

# MAGIC %md
# MAGIC Como lidamos com isso?
# MAGIC
# MAGIC Poderíamos excluir manualmente os registros ofensores da silver e, em seguida, definir a restrição de verificação
# MAGIC
# MAGIC Ou definir a restrição de verificação antes de processar os dados da nossa tabela de bronze e filtrar os dados para o insert na Silver.
# MAGIC
# MAGIC No entanto, se definirmos uma restrição de verificação e um lote de dados contiver registros que a violem, a tarefa falhará e teremos um erro.
# MAGIC
# MAGIC Se nosso objetivo é identificar registros ruins, mas manter os trabalhos de streaming em execução, precisaremos de uma solução diferente.
# MAGIC
# MAGIC Uma ideia seria colocar em quarentena registros inválidos.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Quarentena
# MAGIC A idea da quarentena é que os registros ruins serão gravados em uma tabela separada.
# MAGIC
# MAGIC Isso permite que dados bons sejam processados na tabela silver, enquanto uma lógica adicional ou manual pode revisar os dados em quarentena para decidir se esses dados serão gravados ou processados.
# MAGIC
# MAGIC Com isso, podemos facilmente fazer o backfill desses dados se for necessário
# MAGIC
# MAGIC Vamos implantar uma lógica com o Structured Streaming utilizando o `foreachBatch` para gravar em duas tabelas distintas.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS silver.gcn.gcn_quarantine
# MAGIC (offset bigint, topic string, value string, ingestion_blob_time timestamp, timestamp timestamp)

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS silver.gcn.gcn_notices_quality
# MAGIC (offset bigint, topic string, value string, ingestion_blob_time timestamp, timestamp timestamp)

# COMMAND ----------

sql_quality_query = """
MERGE INTO silver.gcn.gcn_notices_quality t
USING stream_update s
ON t.timestamp = s.timestamp AND t.topic = s.topic
WHEN NOT MATCHED THEN INSERT *
"""

class Upsert:
    def __init__(self, sql_quality_query, update_temp="stream_update"):
        self.query = sql_quality_query
        self.update_temp = update_temp 
        
    def upsert_to_delta(self, micro_batch_df, batch):
        micro_batch_df.filter(F.col("timestamp") >= '2025-02-01').createOrReplaceTempView(self.update_temp)
        micro_batch_df._jdf.sparkSession().sql(self.query)
        micro_batch_df.filter(F.col("timestamp") < '2025-02-01').write.format("delta").mode("append").saveAsTable("silver.gcn.gcn_quarantine")

# COMMAND ----------

# MAGIC %md
# MAGIC Observe que, dentro da lógica foreachBatch, as operações DataFrame estão tratando os dados em cada lote como se fossem estáticos em vez de streaming.
# MAGIC
# MAGIC Como tal, usamos a sintaxe de write em vez de writeStream.
# MAGIC
# MAGIC Isso também significa que nossas garantias exactly-once (exatamente uma vez) são relaxadas. Em nosso exemplo acima, temos duas transações ACID:
# MAGIC
# MAGIC 1. Nossa consulta SQL é feita para executar uma MERGE somente de inserção para evitar gravar registros duplicados em nossa tabela de Silver.
# MAGIC 2. Nós escrevemos um microbatch de registros com datas abaixo de 2025-02-01 na tabela de quarentena
# MAGIC
# MAGIC Se o nosso trabalho falhar após a conclusão da primeira transação, mas antes da segunda ser concluída, executaremos novamente a lógica de microbatch completa no reinício do trabalho.
# MAGIC
# MAGIC No entanto, como nossa mesclagem somente de inserção já impede que registros duplicados sejam salvos em nossa tabela, isso não resultará em corrupção de dados.

# COMMAND ----------

streaming_merge = Upsert(sql_quality_query)

# COMMAND ----------

df_stream_deduped = (spark.readStream
                  .table("bronze.gcn.lab_merge")
                  .selectExpr("offset",
                              "topic",
                              "value",
                              "cast(ingestion_blob_time as timestamp) as ingestion_blob_time",
                              "cast(from_unixtime(timestamp[1]/1000) as timestamp) as timestamp"
                              )
                  .withWatermark("timestamp", "30 seconds")
                  .dropDuplicates(["timestamp", "topic"])
        )

query = (df_stream_deduped.writeStream
                   .foreachBatch(streaming_merge.upsert_to_delta)
                   .outputMode("update")
                   .option("checkpointLocation", "/Volumes/silver/gcn/_checkpoints/gcn_notices_quality")
                   .trigger(availableNow=True)
                   .start())

query.awaitTermination()

# COMMAND ----------

# MAGIC %sql
# MAGIC select min(`timestamp`), max(`timestamp`)
# MAGIC from silver.gcn.gcn_quarantine

# COMMAND ----------

# MAGIC %sql
# MAGIC select min(`timestamp`), max(`timestamp`)
# MAGIC from silver.gcn.gcn_notices_quality
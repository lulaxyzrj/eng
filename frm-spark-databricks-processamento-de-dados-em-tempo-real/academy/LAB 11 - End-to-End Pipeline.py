# Databricks notebook source
# MAGIC %md
# MAGIC # Apache Spark Structured Streaming End-to-End Pipeline Notebook
# MAGIC
# MAGIC Objetivo: Neste notebook construiremos um pipeline completo (Bronze → Silver → Gold) consumindo dados de satélites via Kafka (GCN NASA) e preparando visões para análise e dashboards.

# COMMAND ----------

# MAGIC %md
# MAGIC # 🚀 Seção 0: Configurações Iniciais
# MAGIC
# MAGIC Descrição: Definimos configurações do Spark, paths, broker Kafka, esquemas, import de libs, etc.

# COMMAND ----------

from pyspark.sql.functions import (
    col, regexp_extract, regexp_replace, to_timestamp, to_date,
    current_timestamp, current_date, upper, trim
)
from pyspark.sql import functions as F

# COMMAND ----------

spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")

# COMMAND ----------

"""
Variáveis de configuração para leitura de dados do Kafka:

- topic_pattern: Padrão de tópicos Kafka a serem assinados.
"""
topic_pattern = "gcn.classic.text.*"

# COMMAND ----------

catalog_bronze = "bronze"
catalog_silver = "silver"

schema = "gcn"

table_bronze = "classic_text"

volume_checkpoint = "_checkpoints"
volume_schema = "_schema"
bronze_table_name = f"{catalog_bronze}.{schema}.{table_bronze}"
print("Nome completo da tabela :",bronze_table_name)

source_files = "/Volumes/landing/gcn/gcn/arquivos/"
checkpoint_path = f"/Volumes/{catalog_bronze}/{schema}/{volume_checkpoint}/{table}"
schema_path = f"/Volumes/{catalog_bronze}/{schema}/{volume_schema}/{table}"
print("Caminho dos arquivos: ", source_files)
print("Caminho do checkpoint: ", checkpoint_path)
print("Caminho do schema: ", schema_path)

# COMMAND ----------

# MAGIC %md
# MAGIC # 🥉 Camada Bronze: Ingestão Única (Multiplex)
# MAGIC
# MAGIC 1. Autoloader para todas as mensagens GCN em tabela Bronze única.
# MAGIC
# MAGIC 2. Arquitetura Multiplex: um único DataFrame para todos os tópicos.

# COMMAND ----------

# MAGIC %md
# MAGIC * Para começar, precisa colocar a ingestão do Kafka para o lake para rodar: utils/gcn_consumer_classic
# MAGIC

# COMMAND ----------

def autoloader_to_bronze_multiplex():

    query = (spark
            # Configurando a origem do stream
             .readStream
                .format("cloudfiles")
                .option("cloudFiles.format", "json") 
                .option("subscribePattern", topic_pattern)  
                .option("cloudFiles.schemaLocation", schema_path)  # Specify schema location
                .load(source_files) # Specify source directory
                .withColumn("ingestion_timestamp", F.current_timestamp())
                .withColumn("sistema_origem", F.lit("gcn.classic.text"))
            # Gravando no destino
            .writeStream
                .format("delta")
                .option("checkpointLocation", checkpoint_path)
                .option("mergeSchema", True)
                .option("delta.enableChangeDataFeed", "true")
                .clusterBy("topic") # NOVIDADE!!
                .trigger(availableNow=True) # Executa o processo em batch
                .table(bronze_table_name)
    )
    query.awaitTermination()

# COMMAND ----------

autoloader_to_bronze_multiplex()

# COMMAND ----------

spark.sql(f"OPTIMIZE {bronze_table_name}").display()
spark.sql(f"VACUUM {bronze_table_name} RETAIN 48 HOURS")

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1)
# MAGIC from bronze.gcn.classic_text

# COMMAND ----------

# MAGIC %md
# MAGIC # 🥈 Camada Silver: Separação por Tópico e Enriquecimento
# MAGIC
# MAGIC 1. Leitura da tabela Bronze apenas do tópico que precisa ser processado
# MAGIC
# MAGIC 2. Filtragem por topic e parsing de texto → colunas estruturadas
# MAGIC
# MAGIC 3. Escrita em Delta Silver por satélite

# COMMAND ----------

# Leitura da Bronze filtrando o tópico desejado
bronze_stream = (spark.readStream
                  .table(bronze_table_name).where("topic =  'gcn.classic.text.SWIFT_POINTDIR'"))

# COMMAND ----------

bronze_stream.display()

# COMMAND ----------

from pyspark.sql.functions import col, regexp_extract
silver_parsed = (
    bronze_stream
      # regexp_extract: grupo 1 pega só os dígitos após “1,” e possíveis espaços
      .withColumn("ts_millis",
          regexp_extract(
            col("timestamp"),
            r"\[1,\s*([0-9]+)\]",
            1
          ).cast("long")
      )
      # converte ms→s e cast para TimestampType
      .withColumn("timestamp",
          (col("ts_millis")/1000).cast("timestamp")
      )
      .drop("ts_millis")
)

# COMMAND ----------

silver_parsed.display()

# COMMAND ----------

# Watermark e deduplicação
silver_clean = (
    silver_parsed
      .withWatermark("timestamp", "30 seconds")
      .dropDuplicates(["timestamp", "topic"])
)

# COMMAND ----------

# Explodindo as linhas de texto por quebra de linha
exploded = (
    silver_clean
        .withColumn("line", F.explode(F.split(F.col("value"), "\n")))
        .filter(F.col("line") != "")
)

# COMMAND ----------

exploded.display()

# COMMAND ----------

# Separando chave e valor
key_value = (
    exploded
        .withColumn("key", F.split(F.col("line"), ":").getItem(0))
        .withColumn("value_parsed", F.trim(F.expr("substring(line, instr(line, ':') + 1)")))
        .drop("line")
)

# COMMAND ----------

key_value.display()

# COMMAND ----------

# Pivotando de chave-valor para colunas
silver_pivoted = (
    key_value.groupBy("timestamp")
        .pivot("key", [
            'TITLE', 'NOTICE_DATE', 'NOTICE_TYPE', 'NEXT_POINT_RA', 'NEXT_POINT_DEC', 
            'NEXT_POINT_ROLL', 'SLEW_TIME', 'SLEW_DATE', 'OBS_TIME', 'TGT_NAME', 'TGT_NUM', 
            'MERIT', 'INST_MODES', 'SUN_POSTN', 'SUN_DIST', 'MOON_POSTN', 'MOON_DIST', 
            'MOON_ILLUM', 'GAL_COORDS', 'ECL_COORDS', 'COMMENTS'
        ])
        .agg(F.first("value_parsed"))
)

# COMMAND ----------

silver_pivoted.display()

# COMMAND ----------

# =======================================
# Construção do DataFrame Silver
# =======================================
silver = (
    silver_pivoted

    # =====================
    # Tratamento de Datas
    # =====================

    # NOTICE_DATE para timestamp
    .withColumn(
        "notice_date_clean",
        regexp_replace(regexp_replace(col("NOTICE_DATE"), r"^\w{3}\s", ""), " UT$", "")
    )
    .withColumn(
        "notice_date_ts",
        to_timestamp(col("notice_date_clean"), "dd MMM yy HH:mm:ss")
    )
    .drop("notice_date_clean")

    # TIMESTAMP do evento
    .withColumn("event_timestamp", col("timestamp").cast("timestamp"))

    # Extrair slew_date como data
    # Garantir remoção de espaços laterais
    .withColumn("SLEW_DATE_CLEAN", F.trim(F.col("SLEW_DATE")))
    .withColumn("TGT_NUM_CLEAN", F.trim(F.col("TGT_NUM")))

    # Extrair slew_date como data
    .withColumn("slew_date_str", F.regexp_extract(F.col("SLEW_DATE_CLEAN"), r"(\d{2}/\d{2}/\d{2})", 1))
    .withColumn("slew_date", F.to_date(F.col("slew_date_str"), "yy/MM/dd"))

    # Extrair slew_doy e slew_tjd
    .withColumn("slew_doy", F.regexp_extract(F.col("SLEW_DATE_CLEAN"), r"(\d+)\s*DOY", 1).cast("int"))
    .withColumn("slew_tjd", F.regexp_extract(F.col("SLEW_DATE_CLEAN"), r"(\d+)\s*TJD", 1).cast("int"))

    # =====================
    # Coordenadas do Ponto
    # =====================

    .withColumn("next_point_ra_deg", regexp_extract(col("NEXT_POINT_RA"), r"([+-]?\d+\.?\d*)d", 1).cast("double"))
    .withColumn("next_point_dec_deg", regexp_extract(col("NEXT_POINT_DEC"), r"([+-]?\d+\.?\d*)d", 1).cast("double"))
    .withColumn("next_point_roll_deg", col("NEXT_POINT_ROLL").cast("double"))

    # =====================
    # Tempos e Métricas
    # =====================

    .withColumn("slew_time_sec", F.regexp_extract("SLEW_TIME", r"^([0-9]+\.[0-9]+)", 1).cast("double")) 
    .withColumn("obs_time_sec",F.regexp_extract("OBS_TIME", r"^([0-9]+\.[0-9]+)", 1).cast("double"))
    .withColumn("merit", col("MERIT").cast("double"))

    # =====================
    # Sol
    # =====================

    .withColumn("sun_ra_deg", regexp_extract(col("SUN_POSTN"), r"([+-]?\d+\.?\d*)d", 1).cast("double"))
    .withColumn("sun_dec_deg", regexp_extract(col("SUN_POSTN"), r"([+-]?\d+\.?\d*)d.*?([+-]?\d+\.?\d*)d", 2).cast("double"))
    .withColumn("sun_dist_deg", regexp_extract(col("SUN_DIST"), r"([0-9.]+)", 1).cast("double"))

    # =====================
    # Lua
    # =====================

    .withColumn("moon_ra_deg", regexp_extract(col("MOON_POSTN"), r"([+-]?\d+\.?\d*)d", 1).cast("double"))
    .withColumn("moon_dec_deg", regexp_extract(col("MOON_POSTN"), r"([+-]?\d+\.?\d*)d.*?([+-]?\d+\.?\d*)d", 2).cast("double"))
    .withColumn("moon_dist_deg", regexp_extract(col("MOON_DIST"), r"([0-9.]+)", 1).cast("double"))
    .withColumn("moon_illum_pct", regexp_extract(col("MOON_ILLUM"), r"([0-9.]+)", 1).cast("double"))

    # =====================
    # Coordenadas Galácticas e Eclípticas
    # =====================

    .withColumn("gal_lon", regexp_extract(col("GAL_COORDS"), r"([+-]?\d+\.?\d*),", 1).cast("double"))
    .withColumn("gal_lat", regexp_extract(col("GAL_COORDS"), r",\s*([+-]?\d+\.?\d*)", 1).cast("double"))

    .withColumn("ecl_lon", regexp_extract(col("ECL_COORDS"), r"([+-]?\d+\.?\d*),", 1).cast("double"))
    .withColumn("ecl_lat", regexp_extract(col("ECL_COORDS"), r",\s*([+-]?\d+\.?\d*)", 1).cast("double"))

    # =====================
    # Target e Segmento
    # =====================

    .withColumn("tgt_num", F.regexp_extract(F.col("TGT_NUM_CLEAN"), r"^(\d+)", 1).cast("int"))
    .withColumn("seg_num", F.regexp_extract(F.col("TGT_NUM_CLEAN"), r"Seg_Num:\s*(\d+)", 1).cast("int"))
    
    # =====================
    # Limpeza e Padronização
    # =====================

    .withColumn("title", upper(trim(col("TITLE"))))
    .withColumn("notice_type", upper(trim(col("NOTICE_TYPE"))))
    .withColumn("tgt_name", upper(trim(col("TGT_NAME"))))
    .withColumn("comments", trim(col("COMMENTS")))

    # =====================
    # INST_MODES
    # =====================
    # BAT
    .withColumn("bat_dec", regexp_extract(col("INST_MODES"), r"BAT=(\d+)=0x", 1).cast("int"))
    .withColumn("bat_hex", regexp_extract(col("INST_MODES"), r"BAT=\d+=0x([0-9A-Fa-f]+)", 1))

    # XRT
    .withColumn("xrt_dec", regexp_extract(col("INST_MODES"), r"XRT=(\d+)=0x", 1).cast("int"))
    .withColumn("xrt_hex", regexp_extract(col("INST_MODES"), r"XRT=\d+=0x([0-9A-Fa-f]+)", 1))

    # UVOT
    .withColumn("uvot_dec", regexp_extract(col("INST_MODES"), r"UVOT=(\d+)=0x", 1).cast("int"))
    .withColumn("uvot_hex", regexp_extract(col("INST_MODES"), r"UVOT=\d+=0x([0-9A-Fa-f]+)", 1))

    # =====================
    # Colunas Técnicas
    # =====================

    .withColumn("processing_time", current_timestamp())
    .withColumn("ingestion_date", current_date())


)

# COMMAND ----------

silver_clean = silver.drop(
    "NOTICE_DATE", "TIMESTAMP", "slew_date_str", "TGT_NUM_CLEAN",
    "SLEW_TIME", "OBS_TIME", "NEXT_POINT_RA", "NEXT_POINT_DEC", "NEXT_POINT_ROLL",
    "SUN_POSTN", "SUN_DIST", "MOON_POSTN", "MOON_DIST", "MOON_ILLUM",
    "GAL_COORDS", "ECL_COORDS","INST_MODES","SLEW_DATE_CLEAN"
)


# COMMAND ----------

silver_clean.display()

# COMMAND ----------

# Escrita no Delta Lake (Silver)
df = (silver_clean
        .writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", "/Volumes/silver/gcn/_checkpoints/silver_swift_notices")
        .option("clusterByAuto", "true") #NOVIDADE!!!!
        .trigger(availableNow=True)  # Execução em batch
        .table("silver.gcn.swift_notices")
)

df.awaitTermination()

# COMMAND ----------

spark.sql(f"OPTIMIZE silver.gcn.swift_notices").display()
spark.sql(f"VACUUM silver.gcn.swift_notices RETAIN 48 HOURS")

# COMMAND ----------

# MAGIC %sql
# MAGIC desc extended silver.gcn.swift_notices

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from silver.gcn.swift_notices
# MAGIC limit 10

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE silver.gcn.swift_notices
# MAGIC SET TBLPROPERTIES (
# MAGIC   'comment' = 'Tabela Silver contendo eventos astronômicos processados a partir dos avisos (notices) de observação. Inclui informações sobre alvos, manobras (slews), posições solares e lunares, coordenadas equatoriais, galácticas, eclípticas, tempos associados e modos dos instrumentos BAT, XRT e UVOT.'
# MAGIC );

# COMMAND ----------

column_comments = {
    "title": "Título da observação ou evento",
    "notice_type": "Tipo de aviso ou alerta (ex.: SLEW, OBS, etc.)",
    "tgt_name": "Nome do alvo observado",
    "tgt_num": "Identificador numérico do alvo",
    "merit": "Pontuação de prioridade para observação (merit score)",
    "comments": "Comentários adicionais da observação ou evento",
    "notice_date_ts": "Data e hora do aviso emitido (NOTICE_DATE)",
    "event_timestamp": "Timestamp do evento associado (campo timestamp bruto)",
    "slew_date": "Data da manobra no formato string (yy/MM/dd)",
    "slew_doy": "Dia do ano (DOY) da manobra",
    "slew_tjd": "Tempo juliano truncado (TJD) da manobra",
    "next_point_ra_deg": "Coordenada RA do próximo ponto, em graus",
    "next_point_dec_deg": "Coordenada DEC do próximo ponto, em graus",
    "next_point_roll_deg": "Ângulo de rotação (roll) do próximo ponto, em graus",
    "slew_time_sec": "Tempo de manobra (slew) em segundos",
    "obs_time_sec": "Tempo de observação em segundos",
    "sun_ra_deg": "Ascensão Reta do Sol no momento, em graus",
    "sun_dec_deg": "Declinação do Sol no momento, em graus",
    "sun_dist_deg": "Distância angular do Sol até o alvo, em graus",
    "moon_ra_deg": "Ascensão Reta da Lua no momento, em graus",
    "moon_dec_deg": "Declinação da Lua no momento, em graus",
    "moon_dist_deg": "Distância angular da Lua até o alvo, em graus",
    "moon_illum_pct": "Porcentagem de iluminação da Lua (%)",
    "gal_lon": "Longitude galáctica do alvo, em graus",
    "gal_lat": "Latitude galáctica do alvo, em graus",
    "ecl_lon": "Longitude eclíptica do alvo, em graus",
    "ecl_lat": "Latitude eclíptica do alvo, em graus",
    "seg_num": "Número do segmento da observação",
    "bat_dec": "Modo decimal do instrumento BAT",
    "bat_hex": "Modo hexadecimal do instrumento BAT",
    "xrt_dec": "Modo decimal do instrumento XRT",
    "xrt_hex": "Modo hexadecimal do instrumento XRT",
    "uvot_dec": "Modo decimal do instrumento UVOT",
    "uvot_hex": "Modo hexadecimal do instrumento UVOT",
    "processing_time": "Timestamp do processamento da linha (data e hora do pipeline)",
    "ingestion_date": "Data de ingestão no pipeline"
}


# COMMAND ----------

# Loop para gerar os comandos ALTER TABLE
for col, comment in column_comments.items():
    sql_command = f"""
ALTER TABLE silver.gcn.swift_notices
ALTER COLUMN {col} 
COMMENT '{comment}';
""".strip()
    print(sql_command)
    spark.sql(sql_command)

# COMMAND ----------

# MAGIC %md
# MAGIC # 🥇 Camada Gold: Visões Analíticas e Dados Prontos para Consumo
# MAGIC
# MAGIC 1. Leitura dos dados estruturados e enriquecidos da camada Silver.
# MAGIC
# MAGIC 2. Construção de visões analíticas agregadas, segmentadas por tempo, espaço celeste, performance operacional e alvos observados.
# MAGIC
# MAGIC 3. Persistência em tabelas Delta otimizadas para exploração analítica, consumo em dashboards, relatórios e consultas em linguagem natural via Genie Space.
# MAGIC

# COMMAND ----------

# 1. Leitura da tabela silver
silver_stream = (
    spark.readStream.format("delta")
    .table("silver.gcn.swift_notices")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Observações por dia

# COMMAND ----------

# 2. Agregação: Observações por Data

obs_by_date = (
    silver_stream
    .groupBy(F.col("slew_date"))
    .agg(
        F.count("*").alias("total_observations")
    )
)


# COMMAND ----------

obs_by_date.display()

# COMMAND ----------

#3. Escrita da Tabela Gold em Streaming
query = (
    obs_by_date.writeStream
    .format("delta")
    .outputMode("complete")  # para agregações com groupBy fixo
    .option("checkpointLocation", "/Volumes/gold/gcn/_checkpoints/gold_swift_obs_by_date")
    .option("clusterByAuto", "true") #NOVIDADE!!!!
    .trigger(availableNow=True)  # ou processingTime="1 minute"
    .table("gold.gcn.swift_obs_by_date")
)


# COMMAND ----------

spark.sql(f"OPTIMIZE gold.gcn.swift_obs_by_date").display()
spark.sql(f"VACUUM gold.gcn.swift_obs_by_date RETAIN 48 HOURS")

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE gold.gcn.swift_obs_by_date SET TBLPROPERTIES ('comment' = 'Contagem total de observações realizadas por data de observação (slew_date).');
# MAGIC
# MAGIC ALTER TABLE gold.gcn.swift_obs_by_date ALTER COLUMN slew_date COMMENT 'Data da observação (data da manobra).';
# MAGIC ALTER TABLE gold.gcn.swift_obs_by_date ALTER COLUMN total_observations COMMENT 'Total de observações realizadas nesta data.';

# COMMAND ----------

# MAGIC %md
# MAGIC ##  Observações por Target (Alvo)
# MAGIC Quantidade de observações por alvo (tgt_name ou tgt_num).

# COMMAND ----------

obs_by_target = (
    silver_stream
    .groupBy(F.col("tgt_name"), F.col("tgt_num"))
    .agg(
        F.count("*").alias("total_observations"),
        F.avg("merit").alias("avg_merit"),
        F.avg("obs_time_sec").alias("avg_obs_time_sec")
    )
)


# COMMAND ----------

obs_by_target.display()

# COMMAND ----------

query = (
    obs_by_target.writeStream
    .format("delta")
    .outputMode("complete")
    .option("checkpointLocation", "/Volumes/gold/gcn/_checkpoints/obs_by_target")
    .option("clusterByAuto", "true") #NOVIDADE!!!!
    .trigger(availableNow=True)
    .table("gold.gcn.obs_by_target")
)

# COMMAND ----------

spark.sql(f"OPTIMIZE gold.gcn.obs_by_target").display()
spark.sql(f"VACUUM gold.gcn.obs_by_target RETAIN 48 HOURS")

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE gold.gcn.obs_by_target SET TBLPROPERTIES ('comment' = 'Contagem e estatísticas das observações agrupadas por alvo (target), incluindo média de mérito e tempo de observação.');
# MAGIC
# MAGIC ALTER TABLE gold.gcn.obs_by_target CHANGE COLUMN tgt_name COMMENT 'Nome do alvo observado.';
# MAGIC ALTER TABLE gold.gcn.obs_by_target CHANGE COLUMN tgt_num COMMENT 'Código numérico do alvo.';
# MAGIC ALTER TABLE gold.gcn.obs_by_target CHANGE COLUMN total_observations COMMENT 'Total de observações deste alvo.';
# MAGIC ALTER TABLE gold.gcn.obs_by_target CHANGE COLUMN avg_merit COMMENT 'Mérito médio associado às observações deste alvo.';
# MAGIC ALTER TABLE gold.gcn.obs_by_target CHANGE COLUMN avg_obs_time_sec COMMENT 'Tempo médio de observação (em segundos) deste alvo.';
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Métricas de Slew (manobras) por Data

# COMMAND ----------

slew_metrics_by_date = (
    silver_stream
    .groupBy("slew_date")
    .agg(
        F.count("*").alias("total_slews"),
        F.avg("slew_time_sec").alias("avg_slew_time_sec"),
        F.max("slew_time_sec").alias("max_slew_time_sec"),
        F.min("slew_time_sec").alias("min_slew_time_sec")
    )
)

# COMMAND ----------

slew_metrics_by_date.display()

# COMMAND ----------

query = (
    slew_metrics_by_date.writeStream
    .format("delta")
    .outputMode("complete")
    .option("checkpointLocation", "/Volumes/gold/gcn/_checkpoints/slew_metrics_by_date")
    .option("clusterByAuto", "true") #NOVIDADE!!!!
    .trigger(availableNow=True)
    .table("gold.gcn.slew_metrics_by_date")
)


# COMMAND ----------

spark.sql(f"OPTIMIZE gold.gcn.slew_metrics_by_date").display()
spark.sql(f"VACUUM gold.gcn.slew_metrics_by_date RETAIN 48 HOURS")

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE gold.gcn.slew_metrics_by_date SET TBLPROPERTIES ('comment' = 'Métricas estatísticas sobre os tempos de manobra (slew) por data de observação.');
# MAGIC
# MAGIC ALTER TABLE gold.gcn.slew_metrics_by_date CHANGE COLUMN slew_date COMMENT 'Data da manobra (slew).';
# MAGIC ALTER TABLE gold.gcn.slew_metrics_by_date CHANGE COLUMN total_slews COMMENT 'Total de manobras realizadas na data.';
# MAGIC ALTER TABLE gold.gcn.slew_metrics_by_date CHANGE COLUMN avg_slew_time_sec COMMENT 'Tempo médio de manobra (em segundos).';
# MAGIC ALTER TABLE gold.gcn.slew_metrics_by_date CHANGE COLUMN max_slew_time_sec COMMENT 'Maior tempo registrado de manobra (em segundos) na data.';
# MAGIC ALTER TABLE gold.gcn.slew_metrics_by_date CHANGE COLUMN min_slew_time_sec COMMENT 'Menor tempo registrado de manobra (em segundos) na data.';
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Distribuição dos Modos dos Instrumentos

# COMMAND ----------

instrument_modes = (
    silver_stream
    .groupBy("slew_date")
    .agg(
        F.sum((F.col("bat_dec") > 0).cast("int")).alias("bat_active_count"),
        F.sum((F.col("xrt_dec") > 0).cast("int")).alias("xrt_active_count"),
        F.sum((F.col("uvot_dec") > 0).cast("int")).alias("uvot_active_count")
    )
)

# COMMAND ----------

instrument_modes.display()

# COMMAND ----------

query = (
    instrument_modes.writeStream
    .format("delta")
    .outputMode("complete")
    .option("checkpointLocation", "/Volumes/gold/gcn/_checkpoints/instrument_modes")
    .option("clusterByAuto", "true") #NOVIDADE!!!!
    .trigger(availableNow=True)
    .table("gold.gcn.instrument_modes")
)

# COMMAND ----------

spark.sql(f"OPTIMIZE gold.gcn.instrument_modes").display()
spark.sql(f"VACUUM gold.gcn.instrument_modes RETAIN 48 HOURS")

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE gold.gcn.instrument_modes SET TBLPROPERTIES (
# MAGIC   'comment' = 'Contagem diária de ativações dos instrumentos BAT, XRT e UVOT.'
# MAGIC );
# MAGIC
# MAGIC ALTER TABLE gold.gcn.instrument_modes CHANGE COLUMN slew_date COMMENT 'Data da manobra (slew) associada à observação.';
# MAGIC ALTER TABLE gold.gcn.instrument_modes CHANGE COLUMN bat_active_count COMMENT 'Quantidade de eventos em que o instrumento BAT estava ativo na data.';
# MAGIC ALTER TABLE gold.gcn.instrument_modes CHANGE COLUMN xrt_active_count COMMENT 'Quantidade de eventos em que o instrumento XRT estava ativo na data.';
# MAGIC ALTER TABLE gold.gcn.instrument_modes CHANGE COLUMN uvot_active_count COMMENT 'Quantidade de eventos em que o instrumento UVOT estava ativo na data.';
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC # Limpando ambiente

# COMMAND ----------

spark.sql("drop table if exists bronze.gcn.classic_text")
spark.sql("drop table if exists silver.gcn.swift_notices")
spark.sql("drop table if exists gold.gcn.swift_obs_by_date")
spark.sql("drop table if exists gold.gcn.obs_by_target")
spark.sql("drop table if exists gold.gcn.slew_metrics_by_date")
spark.sql("drop table if exists gold.gcn.instrument_modes")

# COMMAND ----------

dbutils.fs.rm("/Volumes/landing/gcn/gcn/arquivos/", True)
dbutils.fs.rm("/Volumes/silver/gcn/_checkpoints/silver_swift_notices", True)
dbutils.fs.rm("/Volumes/silver/gcn/_checkpoints/gold_swift_obs_by_date", True)
dbutils.fs.rm("/Volumes/silver/gcn/_checkpoints/obs_by_target", True)
dbutils.fs.rm("/Volumes/silver/gcn/_checkpoints/slew_metrics_by_date", True)
dbutils.fs.rm("/Volumes/silver/gcn/_checkpoints/instrument_modes", True)
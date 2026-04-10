-- =====================================================
-- DDL COMPLETO PARA SISTEMA SPT - ALLOYDB POSTGRESQL
-- =====================================================
-- Autor: Sistema de IA para Análise de Riscos SPT
-- Data: 2025-01-14
-- Versão: 2.0
-- Descrição: Schema otimizado para AlloyDB com recursos avançados
--            de IA/ML, processamento vetorial e análise de riscos
-- =====================================================

-- Configurações específicas do AlloyDB
SET alloydb.enable_columnar_scan = on;
SET alloydb.enable_accelerated_queries = on;
SET alloydb.logical_decoding_mode = 'pgoutput';
SET work_mem = '256MB';
SET maintenance_work_mem = '1GB';

-- Criar schemas
CREATE SCHEMA IF NOT EXISTS spt;
CREATE SCHEMA IF NOT EXISTS spt_ai;
CREATE SCHEMA IF NOT EXISTS spt_historico;
CREATE SCHEMA IF NOT EXISTS spt_ml; -- Schema para modelos ML

-- Definir search_path
SET search_path TO spt, spt_ai, public;

-- =====================================================
-- EXTENSÕES NECESSÁRIAS - ALLOYDB ENHANCED
-- =====================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Para busca por similaridade
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- Para índices compostos
CREATE EXTENSION IF NOT EXISTS "vector"; -- Para embeddings (pgvector)
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Monitoramento
CREATE EXTENSION IF NOT EXISTS "google_ml_integration"; -- AlloyDB ML
CREATE EXTENSION IF NOT EXISTS "google_columnar_engine"; -- Columnar storage

-- =====================================================
-- TABELAS CORE (BIDT-CORE)
-- =====================================================

-- Tabela: local_instalacao
CREATE TABLE IF NOT EXISTS spt.local_instalacao (
    loin_cd_local_instalacao NUMERIC PRIMARY KEY,
    loin_nm_local_instalacao VARCHAR(100) NOT NULL,
    loin_cd_local_instalacao_sup NUMERIC,
    loin_in_tipo_local_instalacao CHAR(3),
    refi_cd_refinaria NUMERIC,
    loin_ds_status VARCHAR(10) NOT NULL DEFAULT 'ATIVO',
    loin_ds_local_instalacao VARCHAR(300),
    loin_dt_criacao DATE NOT NULL DEFAULT CURRENT_DATE,
    teco_cd_terminal NUMERIC(5),
    loin_cd_centro_localizacao VARCHAR(6),
    loin_cd_centro_planejamento CHAR(4),
    loin_cd_divisao CHAR(4),
    loin_cd_grupo_planejamento VARCHAR(4),
    -- Campos adicionais para IA
    loin_tx_embedding VECTOR(1536), -- Para busca semântica
    loin_dt_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    loin_tx_metadata JSONB, -- Metadados flexíveis
    
    CONSTRAINT fk_loin_loin FOREIGN KEY (loin_cd_local_instalacao_sup) 
        REFERENCES spt.local_instalacao(loin_cd_local_instalacao)
);

-- Tabela: equipamento
CREATE TABLE IF NOT EXISTS spt.equipamento (
    equi_cd_equipamento NUMERIC PRIMARY KEY,
    equi_nm_equipamento VARCHAR(100) NOT NULL,
    equi_nm_fabricante VARCHAR(40),
    equi_nm_modelo VARCHAR(100),
    equi_cd_sap NUMERIC NOT NULL,
    equi_in_criticidade CHAR(1),
    equi_nr_serie VARCHAR(100),
    cleq_cd_classe_equipamento NUMERIC,
    equi_tx_ordenacao_sap VARCHAR(100),
    loin_cd_local_instalacao NUMERIC,
    equi_ds_status VARCHAR(100) NOT NULL DEFAULT 'ATIVO',
    equi_tx_potencia VARCHAR(30),
    equi_tx_rotacao VARCHAR(30),
    equi_in_utiliza_saim CHAR(1),
    equi_nr_potencia FLOAT8,
    equi_nr_rotacao FLOAT8,
    equi_tx_vazao VARCHAR(30),
    equi_tx_pressao_succao VARCHAR(30),
    equi_tx_pressao_carga VARCHAR(30),
    equi_tx_ano_fabricacao VARCHAR(30),
    equi_tx_tensao VARCHAR(30),
    equi_tx_corrente_nominal VARCHAR(30),
    equi_tx_capacidade_bateria VARCHAR(30),
    equi_nr_bateria_banco VARCHAR(30),
    equi_tx_tecnologia_bateria VARCHAR(30),
    equi_tx_regime_descarga VARCHAR(30),
    equi_tx_ambiente_bateria VARCHAR(30),
    equi_tx_tensao_saida VARCHAR(30),
    equi_tx_tensao_alimentacao VARCHAR(30),
    equi_cd_centro_localizacao VARCHAR(6),
    equi_cd_centro_planejamento CHAR(4),
    equi_cd_divisao CHAR(4),
    equi_cd_grupo_planejamento VARCHAR(4),
    equi_cd_area_operacional CHAR(3),
    equi_in_status_usuario NUMERIC,
    -- Campos para IA
    equi_tx_embedding VECTOR(1536),
    equi_dt_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    equi_tx_historico_manutencao JSONB,
    equi_nr_risk_score FLOAT DEFAULT 0,
    
    CONSTRAINT fk_equi_loin FOREIGN KEY (loin_cd_local_instalacao) 
        REFERENCES spt.local_instalacao(loin_cd_local_instalacao)
);

-- Tabela: terminal_corp
CREATE TABLE IF NOT EXISTS spt.terminal_corp (
    teco_cd_terminal NUMERIC(5) PRIMARY KEY,
    teco_nm_terminal VARCHAR(100) NOT NULL,
    orcb_cd_orgao_cbi NUMERIC,
    port_cd_porto NUMERIC,
    tite_cd_tipo_terminal NUMERIC,
    teco_nr_latitude FLOAT8,
    teco_nr_longitude FLOAT8,
    teco_in_ativo NUMERIC(1) DEFAULT 1,
    teco_ds_terminal VARCHAR(100),
    teco_sg_terminal VARCHAR(15),
    teco_in_origem CHAR(20) NOT NULL
);

-- Tabela: forca_trabalho
CREATE TABLE IF NOT EXISTS spt.forca_trabalho (
    fotr_cd_forca_trabalho NUMERIC PRIMARY KEY,
    fotr_nm_forca_trabalho VARCHAR(100) NOT NULL,
    carg_cd_cargo NUMERIC NOT NULL,
    apca_cd_aplicacao_cargo CHAR(3) NOT NULL,
    grem_cd_grupo_empregado CHAR(1) NOT NULL,
    fotr_in_terra_mar CHAR(1) NOT NULL,
    fotr_dt_cessao DATE,
    func_cd_funcao NUMERIC,
    fotr_cd_login CHAR(4),
    fotr_nr_cpf VARCHAR(11) UNIQUE,
    fotr_tx_passaporte VARCHAR(14),
    fotr_nr_matricula NUMERIC(8) NOT NULL,
    fotr_in_sexo CHAR(1) NOT NULL,
    fotr_tx_email VARCHAR(255) NOT NULL,
    imov_cd_imovel CHAR(15),
    orga_cd_orgao NUMERIC NOT NULL,
    fotr_dt_nascimento DATE NOT NULL,
    fotr_dt_admissao DATE NOT NULL,
    fotr_nr_ramal NUMERIC(7),
    fotr_tx_endereco VARCHAR(100) NOT NULL,
    fotr_tx_endereco_complemento VARCHAR(60),
    fotr_tx_endereco_bairro VARCHAR(40),
    pais_cd_pais NUMERIC(3) NOT NULL,
    unfe_sg_uf CHAR(2) NOT NULL,
    cida_cd_cidade NUMERIC NOT NULL,
    fotr_tx_cep CHAR(10) NOT NULL,
    fotr_tx_telefone VARCHAR(14),
    fotr_tx_celular VARCHAR(14),
    fotr_in_tipo_sanguineo CHAR(3) NOT NULL,
    raca_cd_raca NUMERIC NOT NULL,
    reli_cd_religiao NUMERIC NOT NULL,
    esco_cd_escolaridade NUMERIC NOT NULL,
    esci_cd_especialidade_civil NUMERIC NOT NULL,
    fotr_in_estado_civil NUMERIC(1) NOT NULL,
    fotr_tx_empresa_origem VARCHAR(100),
    cate_cd_categoria_externo CHAR(15),
    fotr_tx_email_particular1 VARCHAR(100),
    fotr_tx_email_particular2 VARCHAR(100),
    fotr_nr_externo NUMERIC(10),
    fotr_dt_cadastro DATE NOT NULL DEFAULT CURRENT_DATE,
    fotr_ds_req_ced VARCHAR(11),
    fotr_ds_motivo_req_ced VARCHAR(30),
    fotr_cd_inativo CHAR(18),
    fotr_ds_motivo_inativo VARCHAR(30),
    fotr_tx_centro_custo CHAR(8),
    fotr_dt_vencimento_aso DATE,
    fotr_nr_matricula_pb VARCHAR(8),
    pais_cd_pais_nascimento NUMERIC(3)
);

-- =====================================================
-- TABELAS SPT NIVEL 1
-- =====================================================

-- Tabela: usuario_portal
CREATE TABLE IF NOT EXISTS spt.usuario_portal (
    uspo_cd_usuario NUMERIC PRIMARY KEY,
    uspo_in_status CHAR(1) NOT NULL DEFAULT 'A',
    uspo_dt_inclusao DATE NOT NULL DEFAULT CURRENT_DATE,
    
    CONSTRAINT fk_uspo_fotr FOREIGN KEY (uspo_cd_usuario) 
        REFERENCES spt.forca_trabalho(fotr_cd_forca_trabalho)
);

-- Tabela: especialidade
CREATE TABLE IF NOT EXISTS spt.especialidade (
    espe_sq_especialidade NUMERIC PRIMARY KEY,
    espe_ds_especialidade VARCHAR(100) NOT NULL UNIQUE,
    espe_in_situacao CHAR(1) NOT NULL DEFAULT 'A',
    espe_sg_especialidade VARCHAR(5) NOT NULL,
    espe_nm_arquivo_icone VARCHAR(250) NOT NULL,
    espe_cd_cor VARCHAR(6) NOT NULL
);

-- Tabela: servico_basico
CREATE TABLE IF NOT EXISTS spt.servico_basico (
    seba_sq_servico_basico NUMERIC PRIMARY KEY,
    seba_ds_servico_basico VARCHAR(150) NOT NULL UNIQUE,
    seba_in_situacao CHAR(1) NOT NULL DEFAULT 'A'
);

-- Tabela: especialidade_servico
CREATE TABLE IF NOT EXISTS spt.especialidade_servico (
    seba_sq_servico_basico NUMERIC NOT NULL,
    espe_sq_especialidade NUMERIC NOT NULL,
    
    PRIMARY KEY (seba_sq_servico_basico, espe_sq_especialidade),
    CONSTRAINT fk_esse_seba FOREIGN KEY (seba_sq_servico_basico) 
        REFERENCES spt.servico_basico(seba_sq_servico_basico),
    CONSTRAINT fk_esse_espe FOREIGN KEY (espe_sq_especialidade) 
        REFERENCES spt.especialidade(espe_sq_especialidade)
);

-- Tabela: ordem_manutencao
CREATE TABLE IF NOT EXISTS spt.ordem_manutencao (
    orma_cd_ordem NUMERIC(12) PRIMARY KEY,
    orma_nm_ordem VARCHAR(40) NOT NULL,
    orma_tx_descricao VARCHAR(40) NOT NULL,
    orma_in_tipo_manutencao NUMERIC(1) NOT NULL,
    orma_ds_centro_custo VARCHAR(50) NOT NULL,
    orma_tx_situacao_ordem VARCHAR(24) NOT NULL,
    orma_in_tipo_ordem VARCHAR(40) NOT NULL,
    orma_tx_campo_selecao DATE NOT NULL,
    orma_cd_projeto NUMERIC(1) NOT NULL,
    equi_cd_equipamento NUMERIC,
    orba_sq_orgao_base NUMERIC NOT NULL,
    orma_in_origem_om CHAR(2) NOT NULL,
    orma_in_situacao NUMERIC(1) NOT NULL,
    orma_sd_localizacao VARCHAR(100),
    orma_tx_autorizacao VARCHAR(40) NOT NULL,
    orma_dt_inclusao DATE NOT NULL DEFAULT CURRENT_DATE,
    orma_in_tipo_carga NUMERIC(1) NOT NULL,
    
    CONSTRAINT fk_orma_equi FOREIGN KEY (equi_cd_equipamento) 
        REFERENCES spt.equipamento(equi_cd_equipamento)
);

-- Tabela: lista_operacao_om
CREATE TABLE IF NOT EXISTS spt.lista_operacao_om (
    lioo_sq_operacao_ordem NUMERIC PRIMARY KEY,
    lioo_ds_operacao VARCHAR(80) NOT NULL,
    lioo_tx_situacao VARCHAR(40) NOT NULL,
    lioo_dt_inicio DATE NOT NULL
);

-- Tabela: oper_ordem_manutencao
CREATE TABLE IF NOT EXISTS spt.oper_ordem_manutencao (
    orma_cd_ordem NUMERIC(12) NOT NULL,
    lioo_sq_operacao_ordem NUMERIC NOT NULL,
    
    PRIMARY KEY (orma_cd_ordem, lioo_sq_operacao_ordem),
    CONSTRAINT fk_opom_orma FOREIGN KEY (orma_cd_ordem) 
        REFERENCES spt.ordem_manutencao(orma_cd_ordem),
    CONSTRAINT fk_opom_lioo FOREIGN KEY (lioo_sq_operacao_ordem) 
        REFERENCES spt.lista_operacao_om(lioo_sq_operacao_ordem)
);

-- Tabela: motivo_cancelamento
CREATE TABLE IF NOT EXISTS spt.motivo_cancelamento (
    moca_sq_motivo_cancelamento NUMERIC PRIMARY KEY,
    moca_ds_motivo_cancelamento VARCHAR(200) NOT NULL,
    moca_in_situacao CHAR(1) NOT NULL DEFAULT 'A'
);

-- =====================================================
-- TABELAS SPT LIBRA (ANÁLISE DE RISCO)
-- =====================================================

-- Tabela: matriz_isolamento
CREATE TABLE IF NOT EXISTS spt.matriz_isolamento (
    mais_sq_matriz_isolamento NUMERIC PRIMARY KEY,
    mais_nm_matriz_isolamento VARCHAR(100) NOT NULL,
    uspo_cd_usuario_elaborador NUMERIC NOT NULL,
    uspo_cd_usuario_revisor NUMERIC,
    mais_in_status CHAR(1) NOT NULL DEFAULT 'A',
    mais_dt_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    equi_cd_equipamento NUMERIC,
    loin_cd_local_instalacao NUMERIC NOT NULL,
    mais_sq_matriz_isolamento_orig NUMERIC,
    mais_tx_observacao VARCHAR(4000),
    mais_dt_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mais_tx_objetivo VARCHAR(500),
    mais_dt_revisao TIMESTAMP,
    mais_dt_exclusao TIMESTAMP,
    orba_sq_orgao_base NUMERIC NOT NULL,
    mais_sq_matriz_isolamento_inic NUMERIC,
    
    CONSTRAINT fk_mais_uspo_elab FOREIGN KEY (uspo_cd_usuario_elaborador) 
        REFERENCES spt.usuario_portal(uspo_cd_usuario),
    CONSTRAINT fk_mais_uspo_rev FOREIGN KEY (uspo_cd_usuario_revisor) 
        REFERENCES spt.usuario_portal(uspo_cd_usuario),
    CONSTRAINT fk_mais_equi FOREIGN KEY (equi_cd_equipamento) 
        REFERENCES spt.equipamento(equi_cd_equipamento),
    CONSTRAINT fk_mais_loin FOREIGN KEY (loin_cd_local_instalacao) 
        REFERENCES spt.local_instalacao(loin_cd_local_instalacao)
);

-- Tabela: analise_risco (CORE DA SOLUÇÃO)
CREATE TABLE IF NOT EXISTS spt.analise_risco (
    anri_sq_analise_risco NUMERIC PRIMARY KEY,
    anri_in_nivel_analise NUMERIC(1) NOT NULL CHECK (anri_in_nivel_analise IN (1, 2)),
    anri_dt_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    anri_dt_elaboracao TIMESTAMP,
    anri_dt_exclusao TIMESTAMP,
    anri_in_situacao CHAR(1) NOT NULL DEFAULT 'A',
    -- Campos de texto livre que precisam estruturação
    anri_tx_perigos TEXT,
    anri_tx_causas TEXT,
    anri_tx_efeitos TEXT,
    anri_tx_recomendacoes TEXT,
    anri_tx_medidas_controle TEXT,
    -- Novos campos para IA
    anri_tx_perigos_estruturado JSONB, -- Versão estruturada
    anri_tx_causas_estruturado JSONB,
    anri_tx_efeitos_estruturado JSONB,
    anri_tx_recomendacoes_estruturado JSONB,
    anri_tx_embedding VECTOR(1536), -- Embedding do cenário completo
    anri_nr_risk_score FLOAT,
    anri_tx_metadata JSONB,
    anri_in_validado_ia BOOLEAN DEFAULT FALSE,
    anri_dt_processamento_ia TIMESTAMP,
    anri_tx_feedback_usuario JSONB
);

-- Tabela: permissao_trabalho (PT)
CREATE TABLE IF NOT EXISTS spt.permissao_trabalho (
    petr_sq_permissao_trabalho NUMERIC PRIMARY KEY,
    anri_sq_analise_risco NUMERIC,
    mais_sq_matriz_isolamento NUMERIC,
    petr_in_tipo_permissao CHAR(1) NOT NULL,
    petr_in_ras CHAR(1),
    petr_in_espaco_confinado CHAR(1),
    petr_in_area_operacional CHAR(1),
    petr_in_combinada CHAR(1),
    petr_in_servico_apoio CHAR(1),
    petr_in_servico_rotina CHAR(1),
    petr_in_situacao CHAR(1) NOT NULL DEFAULT 'A',
    petr_in_om CHAR(1),
    petr_in_forma_trabalho CHAR(1),
    petr_ds_servico VARCHAR(4000),
    petr_dt_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    petr_tx_recomendacao VARCHAR(5000),
    petr_dt_exclusao TIMESTAMP,
    petr_dt_emissao TIMESTAMP,
    petr_dt_rejeicao TIMESTAMP,
    petr_dt_encerramento TIMESTAMP,
    petr_dt_inicio_programado TIMESTAMP,
    petr_dt_reemissao TIMESTAMP,
    petr_dt_cancelamento TIMESTAMP,
    petr_in_status CHAR(1) NOT NULL DEFAULT 'P',
    petr_dt_encerr_programado TIMESTAMP,
    loin_cd_local_instalacao NUMERIC,
    equi_cd_equipamento NUMERIC,
    seba_sq_servico_basico NUMERIC,
    espe_sq_especialidade NUMERIC,
    uspo_cd_usuario_elaborador NUMERIC,
    uspo_cd_usuario_emitente NUMERIC,
    uspo_cd_usuario_associador NUMERIC,
    uspo_cd_usuario_cancelamento NUMERIC,
    uspo_cd_usuario_encerramento NUMERIC,
    uspo_cd_usuario_rejeicao NUMERIC,
    uspo_cd_usuario_substituicao NUMERIC,
    uspo_cd_usuario_exclusao NUMERIC,
    petr_in_pendencia CHAR(1),
    petr_tx_obs_encerramento VARCHAR(500),
    petr_dt_substituicao TIMESTAMP,
    petr_tx_justificativa_om VARCHAR(500),
    orba_sq_orgao_base NUMERIC,
    -- Campos para IA
    petr_tx_embedding VECTOR(1536),
    petr_tx_ia_recommendations JSONB,
    petr_nr_ia_confidence FLOAT,
    
    CONSTRAINT fk_petr_anri FOREIGN KEY (anri_sq_analise_risco) 
        REFERENCES spt.analise_risco(anri_sq_analise_risco),
    CONSTRAINT fk_petr_mais FOREIGN KEY (mais_sq_matriz_isolamento) 
        REFERENCES spt.matriz_isolamento(mais_sq_matriz_isolamento),
    CONSTRAINT fk_petr_loin FOREIGN KEY (loin_cd_local_instalacao) 
        REFERENCES spt.local_instalacao(loin_cd_local_instalacao),
    CONSTRAINT fk_petr_equi FOREIGN KEY (equi_cd_equipamento) 
        REFERENCES spt.equipamento(equi_cd_equipamento),
    CONSTRAINT fk_petr_seba FOREIGN KEY (seba_sq_servico_basico) 
        REFERENCES spt.servico_basico(seba_sq_servico_basico),
    CONSTRAINT fk_petr_espe FOREIGN KEY (espe_sq_especialidade) 
        REFERENCES spt.especialidade(espe_sq_especialidade)
);

-- Tabela: motivo_cancelamento_pt
CREATE TABLE IF NOT EXISTS spt.motivo_cancelamento_pt (
    moca_sq_motivo_cancelamento NUMERIC NOT NULL,
    petr_sq_permissao_trabalho NUMERIC NOT NULL,
    
    PRIMARY KEY (moca_sq_motivo_cancelamento, petr_sq_permissao_trabalho),
    CONSTRAINT fk_mocp_moca FOREIGN KEY (moca_sq_motivo_cancelamento) 
        REFERENCES spt.motivo_cancelamento(moca_sq_motivo_cancelamento),
    CONSTRAINT fk_mocp_petr FOREIGN KEY (petr_sq_permissao_trabalho) 
        REFERENCES spt.permissao_trabalho(petr_sq_permissao_trabalho)
);

-- Tabela: operacao_om_pt
CREATE TABLE IF NOT EXISTS spt.operacao_om_pt (
    petr_sq_permissao_trabalho NUMERIC NOT NULL,
    orma_cd_ordem NUMERIC(12) NOT NULL,
    lioo_sq_operacao_ordem NUMERIC NOT NULL,
    
    PRIMARY KEY (petr_sq_permissao_trabalho, orma_cd_ordem, lioo_sq_operacao_ordem),
    CONSTRAINT fk_opop_petr FOREIGN KEY (petr_sq_permissao_trabalho) 
        REFERENCES spt.permissao_trabalho(petr_sq_permissao_trabalho),
    CONSTRAINT fk_opop_opom FOREIGN KEY (orma_cd_ordem, lioo_sq_operacao_ordem) 
        REFERENCES spt.oper_ordem_manutencao(orma_cd_ordem, lioo_sq_operacao_ordem)
);

-- Tabela: participante_analise_risco
CREATE TABLE IF NOT EXISTS spt.participante_analise_risco (
    fotr_cd_forca_trabalho NUMERIC NOT NULL,
    anri_sq_analise_risco NUMERIC NOT NULL,
    tipa_nr_tipo_participante NUMERIC NOT NULL,
    
    PRIMARY KEY (fotr_cd_forca_trabalho, anri_sq_analise_risco),
    CONSTRAINT fk_paar_fotr FOREIGN KEY (fotr_cd_forca_trabalho) 
        REFERENCES spt.forca_trabalho(fotr_cd_forca_trabalho),
    CONSTRAINT fk_paar_anri FOREIGN KEY (anri_sq_analise_risco) 
        REFERENCES spt.analise_risco(anri_sq_analise_risco)
);

-- =====================================================
-- TABELAS ESPECÍFICAS PARA IA (NOVO SCHEMA)
-- =====================================================

-- Tabela: perigos_catalogados
CREATE TABLE IF NOT EXISTS spt_ai.perigos_catalogados (
    peri_cd_perigo SERIAL PRIMARY KEY,
    peri_ds_perigo VARCHAR(500) NOT NULL UNIQUE,
    peri_cd_categoria VARCHAR(100),
    peri_in_ativo BOOLEAN DEFAULT TRUE,
    peri_tx_embedding VECTOR(1536),
    peri_dt_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    peri_dt_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    peri_nr_frequencia INTEGER DEFAULT 0,
    peri_tx_metadata JSONB
);

-- Tabela: causas_catalogadas
CREATE TABLE IF NOT EXISTS spt_ai.causas_catalogadas (
    caus_cd_causa SERIAL PRIMARY KEY,
    caus_ds_causa VARCHAR(500) NOT NULL UNIQUE,
    caus_cd_categoria VARCHAR(100),
    caus_in_ativo BOOLEAN DEFAULT TRUE,
    caus_tx_embedding VECTOR(1536),
    caus_dt_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    caus_dt_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    caus_nr_frequencia INTEGER DEFAULT 0,
    caus_tx_metadata JSONB
);

-- Tabela: efeitos_catalogados
CREATE TABLE IF NOT EXISTS spt_ai.efeitos_catalogados (
    efei_cd_efeito SERIAL PRIMARY KEY,
    efei_ds_efeito VARCHAR(500) NOT NULL UNIQUE,
    efei_cd_categoria VARCHAR(100),
    efei_cd_severidade INTEGER,
    efei_in_ativo BOOLEAN DEFAULT TRUE,
    efei_tx_embedding VECTOR(1536),
    efei_dt_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    efei_dt_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    efei_nr_frequencia INTEGER DEFAULT 0,
    efei_tx_metadata JSONB
);

-- Tabela: relacao_perigo_causa_efeito (MAPEAMENTO INTELIGENTE)
CREATE TABLE IF NOT EXISTS spt_ai.relacao_perigo_causa_efeito (
    rpce_cd_relacao SERIAL PRIMARY KEY,
    peri_cd_perigo INTEGER NOT NULL,
    caus_cd_causa INTEGER NOT NULL,
    efei_cd_efeito INTEGER NOT NULL,
    rpce_nr_confianca FLOAT DEFAULT 0,
    rpce_nr_frequencia INTEGER DEFAULT 0,
    rpce_in_validado_humano BOOLEAN DEFAULT FALSE,
    rpce_dt_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rpce_dt_validacao TIMESTAMP,
    rpce_cd_usuario_validador NUMERIC,
    rpce_tx_observacao TEXT,
    rpce_tx_embedding VECTOR(1536),
    
    CONSTRAINT fk_rpce_peri FOREIGN KEY (peri_cd_perigo) 
        REFERENCES spt_ai.perigos_catalogados(peri_cd_perigo),
    CONSTRAINT fk_rpce_caus FOREIGN KEY (caus_cd_causa) 
        REFERENCES spt_ai.causas_catalogadas(caus_cd_causa),
    CONSTRAINT fk_rpce_efei FOREIGN KEY (efei_cd_efeito) 
        REFERENCES spt_ai.efeitos_catalogados(efei_cd_efeito),
    CONSTRAINT uk_rpce_unique UNIQUE (peri_cd_perigo, caus_cd_causa, efei_cd_efeito)
);

-- Tabela: recomendacoes_ia
CREATE TABLE IF NOT EXISTS spt_ai.recomendacoes_ia (
    reia_cd_recomendacao SERIAL PRIMARY KEY,
    anri_sq_analise_risco NUMERIC NOT NULL,
    reia_tx_recomendacao TEXT NOT NULL,
    reia_tx_tipo VARCHAR(100),
    reia_nr_confianca FLOAT,
    reia_in_aceita BOOLEAN,
    reia_dt_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reia_dt_feedback TIMESTAMP,
    reia_tx_feedback TEXT,
    reia_cd_usuario_feedback NUMERIC,
    reia_tx_embedding VECTOR(1536),
    reia_tx_contexto JSONB,
    
    CONSTRAINT fk_reia_anri FOREIGN KEY (anri_sq_analise_risco) 
        REFERENCES spt.analise_risco(anri_sq_analise_risco)
);

-- Tabela: historico_processamento_ia
CREATE TABLE IF NOT EXISTS spt_ai.historico_processamento_ia (
    hpia_cd_processamento SERIAL PRIMARY KEY,
    hpia_tx_tipo_processamento VARCHAR(100) NOT NULL,
    hpia_cd_registro_origem NUMERIC,
    hpia_tx_tabela_origem VARCHAR(100),
    hpia_dt_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hpia_dt_fim TIMESTAMP,
    hpia_in_status VARCHAR(20),
    hpia_tx_modelo_usado VARCHAR(100),
    hpia_tx_parametros JSONB,
    hpia_tx_resultado JSONB,
    hpia_tx_metricas JSONB,
    hpia_tx_erro TEXT,
    hpia_nr_tokens_usados INTEGER,
    hpia_nr_custo_estimado NUMERIC(10,4)
) WITH (enable_columnar = true); -- AlloyDB columnar storage

-- =====================================================
-- CONFIGURAÇÕES ALLOYDB ML
-- =====================================================

-- Criar modelo de classificação de risco usando AlloyDB ML
CREATE MODEL IF NOT EXISTS spt_ml.risk_classifier
TRANSFORM (
    anri_tx_perigos AS perigos,
    anri_tx_causas AS causas,
    anri_tx_efeitos AS efeitos,
    anri_nr_risk_score AS target
)
OPTIONS (
    model_type = 'BOOSTED_TREE_CLASSIFIER',
    input_label_cols = ['target'],
    optimization_objective = 'MINIMIZE_LOG_LOSS'
) AS
SELECT * FROM spt.analise_risco WHERE anri_in_validado_ia = TRUE;

-- Criar modelo de recomendação usando embeddings
CREATE MODEL IF NOT EXISTS spt_ml.recommendation_engine
OPTIONS (
    model_type = 'MATRIX_FACTORIZATION',
    num_factors = 128,
    l2_reg = 0.01
) AS
SELECT 
    petr_sq_permissao_trabalho as item_id,
    uspo_cd_usuario as user_id,
    reia_nr_confianca as rating
FROM spt.permissao_trabalho p
JOIN spt_ai.recomendacoes_ia r ON p.anri_sq_analise_risco = r.anri_sq_analise_risco;

-- =====================================================
-- ÍNDICES OTIMIZADOS PARA ALLOYDB
-- =====================================================

-- Índices para busca vetorial (AlloyDB optimized)
CREATE INDEX idx_anri_embedding ON spt.analise_risco 
USING ivfflat (anri_tx_embedding vector_cosine_ops)
WITH (lists = 1000);

CREATE INDEX idx_equi_embedding ON spt.equipamento
USING ivfflat (equi_tx_embedding vector_cosine_ops)
WITH (lists = 500);

CREATE INDEX idx_loin_embedding ON spt.local_instalacao
USING ivfflat (loin_tx_embedding vector_cosine_ops)
WITH (lists = 200);

-- Índices columnares para análise (AlloyDB specific)
ALTER TABLE spt.permissao_trabalho SET (enable_columnar = true);
ALTER TABLE spt.analise_risco SET (enable_columnar = true);
ALTER TABLE spt_historico.analise_risco_petrobras SET (enable_columnar = true);

-- Índices compostos para queries complexas
CREATE INDEX idx_petr_composite ON spt.permissao_trabalho 
USING btree (petr_dt_criacao, petr_in_status, loin_cd_local_instalacao)
INCLUDE (petr_sq_permissao_trabalho, anri_sq_analise_risco);

CREATE INDEX idx_anri_jsonb_perigos ON spt.analise_risco 
USING gin (anri_tx_perigos_estruturado);

CREATE INDEX idx_anri_jsonb_causas ON spt.analise_risco 
USING gin (anri_tx_causas_estruturado);

-- Índices para text search
CREATE INDEX idx_anri_text_search ON spt.analise_risco 
USING gin (to_tsvector('portuguese', 
    coalesce(anri_tx_perigos, '') || ' ' || 
    coalesce(anri_tx_causas, '') || ' ' || 
    coalesce(anri_tx_efeitos, '')));

-- =====================================================
-- PARTICIONAMENTO PARA PERFORMANCE
-- =====================================================

-- Particionar tabela de análise de risco por ano
ALTER TABLE spt.analise_risco 
PARTITION BY RANGE (EXTRACT(YEAR FROM anri_dt_criacao));

CREATE TABLE spt.analise_risco_2024 PARTITION OF spt.analise_risco
FOR VALUES FROM (2024) TO (2025);

CREATE TABLE spt.analise_risco_2025 PARTITION OF spt.analise_risco
FOR VALUES FROM (2025) TO (2026);

CREATE TABLE spt.analise_risco_default PARTITION OF spt.analise_risco
DEFAULT;

-- =====================================================
-- VIEWS MATERIALIZADAS PARA PERFORMANCE
-- =====================================================

-- View para análise de riscos frequentes
CREATE MATERIALIZED VIEW spt_ai.mv_riscos_frequentes AS
WITH risk_patterns AS (
    SELECT 
        peri_cd_perigo,
        caus_cd_causa,
        efei_cd_efeito,
        COUNT(*) as frequencia,
        AVG(rpce_nr_confianca) as confianca_media
    FROM spt_ai.relacao_perigo_causa_efeito
    WHERE rpce_in_validado_humano = TRUE
    GROUP BY peri_cd_perigo, caus_cd_causa, efei_cd_efeito
)
SELECT 
    p.peri_ds_perigo,
    c.caus_ds_causa,
    e.efei_ds_efeito,
    rp.frequencia,
    rp.confianca_media,
    p.peri_tx_embedding <=> c.caus_tx_embedding as similarity_pc,
    c.caus_tx_embedding <=> e.efei_tx_embedding as similarity_ce
FROM risk_patterns rp
JOIN spt_ai.perigos_catalogados p ON p.peri_cd_perigo = rp.peri_cd_perigo
JOIN spt_ai.causas_catalogadas c ON c.caus_cd_causa = rp.caus_cd_causa
JOIN spt_ai.efeitos_catalogados e ON e.efei_cd_efeito = rp.efei_cd_efeito
WHERE rp.frequencia > 10
ORDER BY rp.frequencia DESC, rp.confianca_media DESC;

-- Refresh automático a cada hora
CREATE UNIQUE INDEX ON spt_ai.mv_riscos_frequentes (peri_ds_perigo, caus_ds_causa, efei_ds_efeito);
REFRESH MATERIALIZED VIEW CONCURRENTLY spt_ai.mv_riscos_frequentes;

-- =====================================================
-- FUNCTIONS PARA PROCESSAMENTO DE IA
-- =====================================================

-- Function para busca semântica de riscos similares
CREATE OR REPLACE FUNCTION spt_ai.buscar_riscos_similares(
    p_embedding vector(1536),
    p_limit integer DEFAULT 10,
    p_threshold float DEFAULT 0.7
)
RETURNS TABLE (
    analise_id numeric,
    similarity float,
    perigos text,
    causas text,
    efeitos text,
    recomendacoes text
)
LANGUAGE plpgsql
AS $
BEGIN
    RETURN QUERY
    SELECT 
        anri_sq_analise_risco,
        1 - (anri_tx_embedding <=> p_embedding) as similarity,
        anri_tx_perigos,
        anri_tx_causas,
        anri_tx_efeitos,
        anri_tx_recomendacoes
    FROM spt.analise_risco
    WHERE anri_tx_embedding IS NOT NULL
        AND 1 - (anri_tx_embedding <=> p_embedding) > p_threshold
    ORDER BY anri_tx_embedding <=> p_embedding
    LIMIT p_limit;
END;
$;

-- Function para gerar recomendações baseadas em ML
CREATE OR REPLACE FUNCTION spt_ai.gerar_recomendacao_ml(
    p_analise_id numeric
)
RETURNS jsonb
LANGUAGE plpgsql
AS $
DECLARE
    v_result jsonb;
    v_embedding vector(1536);
BEGIN
    -- Buscar embedding da análise atual
    SELECT anri_tx_embedding INTO v_embedding
    FROM spt.analise_risco
    WHERE anri_sq_analise_risco = p_analise_id;
    
    -- Usar modelo ML do AlloyDB para predição
    SELECT jsonb_build_object(
        'risk_score', ml.predict('spt_ml.risk_classifier', anri_tx_perigos, anri_tx_causas, anri_tx_efeitos),
        'similar_cases', array_agg(
            jsonb_build_object(
                'id', s.analise_id,
                'similarity', s.similarity,
                'recomendacoes', s.recomendacoes
            )
        ),
        'confidence', 0.85,
        'timestamp', current_timestamp
    ) INTO v_result
    FROM spt_ai.buscar_riscos_similares(v_embedding, 5, 0.8) s
    CROSS JOIN spt.analise_risco a
    WHERE a.anri_sq_analise_risco = p_analise_id;
    
    RETURN v_result;
END;
$;

-- =====================================================
-- TRIGGERS PARA AUTOMAÇÃO
-- =====================================================

-- Trigger para gerar embeddings automaticamente
CREATE OR REPLACE FUNCTION spt_ai.gerar_embedding_trigger()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $
BEGIN
    -- Chamar API do Vertex AI para gerar embedding
    NEW.anri_tx_embedding = google_ml.generate_embedding(
        model_id => 'textembedding-gecko',
        content => COALESCE(NEW.anri_tx_perigos, '') || ' ' ||
                  COALESCE(NEW.anri_tx_causas, '') || ' ' ||
                  COALESCE(NEW.anri_tx_efeitos, '')
    );
    
    -- Processar estruturação do texto
    NEW.anri_tx_perigos_estruturado = spt_ai.estruturar_texto(NEW.anri_tx_perigos);
    NEW.anri_tx_causas_estruturado = spt_ai.estruturar_texto(NEW.anri_tx_causas);
    NEW.anri_tx_efeitos_estruturado = spt_ai.estruturar_texto(NEW.anri_tx_efeitos);
    
    RETURN NEW;
END;
$;

CREATE TRIGGER trg_gerar_embedding
BEFORE INSERT OR UPDATE ON spt.analise_risco
FOR EACH ROW
EXECUTE FUNCTION spt_ai.gerar_embedding_trigger();

-- =====================================================
-- POLÍTICAS DE SEGURANÇA (RLS)
-- =====================================================

ALTER TABLE spt.permissao_trabalho ENABLE ROW LEVEL SECURITY;
ALTER TABLE spt.analise_risco ENABLE ROW LEVEL SECURITY;

-- Política para usuários verem apenas suas análises
CREATE POLICY usuario_proprio_analise ON spt.analise_risco
FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM spt.participante_analise_risco par
        WHERE par.anri_sq_analise_risco = analise_risco.anri_sq_analise_risco
        AND par.fotr_cd_forca_trabalho = current_setting('app.current_user')::numeric
    )
);

-- =====================================================
-- JOBS AGENDADOS (USANDO ALLOYDB SCHEDULER)
-- =====================================================

-- Job para atualizar embeddings periodicamente
SELECT google_scheduler.create_job(
    job_name => 'atualizar_embeddings',
    job_type => 'PLPGSQL_BLOCK',
    job_action => '
        UPDATE spt.analise_risco 
        SET anri_tx_embedding = google_ml.generate_embedding(
            ''textembedding-gecko'',
            COALESCE(anri_tx_perigos, '''') || '' '' ||
            COALESCE(anri_tx_causas, '''') || '' '' ||
            COALESCE(anri_tx_efeitos, '''')
        )
        WHERE anri_tx_embedding IS NULL
        AND anri_dt_criacao > CURRENT_DATE - INTERVAL ''7 days'';
    ',
    start_date => CURRENT_TIMESTAMP,
    repeat_interval => 'FREQ=HOURLY;INTERVAL=1'
);

-- Job para refresh de materialized views
SELECT google_scheduler.create_job(
    job_name => 'refresh_mv_riscos',
    job_type => 'SQL',
    job_action => 'REFRESH MATERIALIZED VIEW CONCURRENTLY spt_ai.mv_riscos_frequentes;',
    start_date => CURRENT_TIMESTAMP,
    repeat_interval => 'FREQ=HOURLY;INTERVAL=1'
);

-- =====================================================
-- DADOS INICIAIS E CONFIGURAÇÕES
-- =====================================================

-- Inserir tipos de participantes
INSERT INTO spt.tipo_participante (tipa_nr_tipo_participante, tipa_ds_tipo) VALUES
(1, 'Responsável pela execução do trabalho'),
(2, 'Responsável pelo equipamento ou sistema'),
(3, 'Profissional de segurança');

-- Configurar parâmetros do AlloyDB
ALTER SYSTEM SET shared_buffers = '32GB';
ALTER SYSTEM SET effective_cache_size = '96GB';
ALTER SYSTEM SET max_parallel_workers = 32;
ALTER SYSTEM SET max_parallel_workers_per_gather = 16;
ALTER SYSTEM SET random_page_cost = 1.1;

-- =====================================================
-- MONITORAMENTO E OBSERVABILITY
-- =====================================================

-- View para monitorar performance de queries
CREATE VIEW spt_ai.v_query_performance AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    stddev_time,
    rows
FROM pg_stat_statements
WHERE query LIKE '%spt%'
ORDER BY total_time DESC
LIMIT 100;

-- View para monitorar uso de embeddings
CREATE VIEW spt_ai.v_embedding_stats AS
SELECT 
    schemaname,
    tablename,
    COUNT(*) FILTER (WHERE attname LIKE '%embedding%' AND NOT attisdropped) as embedding_columns,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size
FROM pg_stat_user_tables t
JOIN pg_attribute a ON a.attrelid = (schemaname||'.'||tablename)::regclass
WHERE schemaname IN ('spt', 'spt_ai')
GROUP BY schemaname, tablename
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- =====================================================
-- GRANTS E PERMISSÕES
-- =====================================================

-- Criar roles
CREATE ROLE spt_admin;
CREATE ROLE spt_user;
CREATE ROLE spt_ai_service;

-- Grants para admin
GRANT ALL ON SCHEMA spt, spt_ai, spt_historico, spt_ml TO spt_admin;
GRANT ALL ON ALL TABLES IN SCHEMA spt, spt_ai, spt_historico TO spt_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA spt, spt_ai, spt_historico TO spt_admin;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA spt, spt_ai TO spt_admin;

-- Grants para usuários
GRANT USAGE ON SCHEMA spt TO spt_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA spt TO spt_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA spt TO spt_user;

-- Grants para serviço de IA
GRANT USAGE ON SCHEMA spt, spt_ai, spt_ml TO spt_ai_service;
GRANT ALL ON ALL TABLES IN SCHEMA spt_ai, spt_ml TO spt_ai_service;
GRANT SELECT ON ALL TABLES IN SCHEMA spt TO spt_ai_service;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA spt_ai TO spt_ai_service;

-- =====================================================
-- COMENTÁRIOS E DOCUMENTAÇÃO
-- =====================================================

COMMENT ON SCHEMA spt IS 'Schema principal do Sistema de Permissão para Trabalho';
COMMENT ON SCHEMA spt_ai IS 'Schema para componentes de Inteligência Artificial';
COMMENT ON SCHEMA spt_ml IS 'Schema para modelos de Machine Learning';
COMMENT ON SCHEMA spt_historico IS 'Schema para dados históricos e migração';

COMMENT ON TABLE spt.analise_risco IS 'Tabela central de análises de risco com suporte a IA';
COMMENT ON COLUMN spt.analise_risco.anri_tx_embedding IS 'Embedding vetorial do cenário de risco para busca semântica';
COMMENT ON COLUMN spt.analise_risco.anri_tx_perigos_estruturado IS 'Versão estruturada (JSON) dos perigos identificados';

-- =====================================================
-- FIM DO DDL - ALLOYDB OPTIMIZED
-- =====================================================
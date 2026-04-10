#!/bin/bash
# =====================================================
# SETUP COMPLETO ALLOYDB PARA PROJETO SPT TRANSPETRO
# =====================================================
# Autor: Arquitetura IA SPT
# Data: 2025-01-14
# Versão: 1.0
# =====================================================

# =====================================================
# 1. CONFIGURAÇÕES INICIAIS
# =====================================================

# Variáveis do projeto
export PROJECT_ID="transpetro-spt-prod"
export REGION="southamerica-east1"  # São Paulo
export ZONE="southamerica-east1-a"
export CLUSTER_ID="spt-alloydb-cluster"
export PRIMARY_INSTANCE_ID="spt-primary-instance"
export READ_INSTANCE_ID="spt-read-replica"
export NETWORK_NAME="spt-vpc-network"
export SUBNET_NAME="spt-subnet-alloydb"
export RESERVED_RANGE_NAME="spt-google-managed-services"
export BACKUP_ID="spt-backup-$(date +%Y%m%d)"

# Configurar projeto
gcloud config set project $PROJECT_ID

# Habilitar APIs necessárias
echo "📦 Habilitando APIs necessárias..."
gcloud services enable \
    alloydb.googleapis.com \
    compute.googleapis.com \
    servicenetworking.googleapis.com \
    cloudresourcemanager.googleapis.com \
    aiplatform.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com

# =====================================================
# 2. CONFIGURAR REDE VPC
# =====================================================

echo "🌐 Configurando rede VPC..."

# Criar VPC Network
gcloud compute networks create $NETWORK_NAME \
    --subnet-mode=custom \
    --bgp-routing-mode=regional \
    --mtu=1460

# Criar Subnet
gcloud compute networks subnets create $SUBNET_NAME \
    --network=$NETWORK_NAME \
    --region=$REGION \
    --range=10.0.0.0/24 \
    --enable-private-ip-google-access

# Reservar range de IP para serviços gerenciados Google
gcloud compute addresses create $RESERVED_RANGE_NAME \
    --global \
    --purpose=VPC_PEERING \
    --prefix-length=16 \
    --network=$NETWORK_NAME

# Criar VPC peering com Google services
gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --network=$NETWORK_NAME \
    --ranges=$RESERVED_RANGE_NAME

# =====================================================
# 3. CRIAR CLUSTER ALLOYDB
# =====================================================

echo "🚀 Criando cluster AlloyDB..."

gcloud alloydb clusters create $CLUSTER_ID \
    --region=$REGION \
    --network=$NETWORK_NAME \
    --allocated-ip-range-name=$RESERVED_RANGE_NAME \
    --database-version=POSTGRES_15 \
    --cluster-type=PRIMARY \
    --enable-automated-backup \
    --automated-backup-start-times=03:00 \
    --automated-backup-days-of-week=SUNDAY,MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY \
    --automated-backup-retention-period=30d \
    --automated-backup-window=4h \
    --continuous-backup-enable \
    --continuous-backup-recovery-window-days=7 \
    --enable-point-in-time-recovery \
    --labels=projeto=spt,ambiente=producao,cliente=transpetro

# Aguardar criação do cluster
echo "⏳ Aguardando cluster ficar pronto..."
gcloud alloydb clusters describe $CLUSTER_ID \
    --region=$REGION \
    --format="value(state)" \
    | grep -q "READY" || sleep 60

# =====================================================
# 4. CRIAR INSTÂNCIA PRIMÁRIA
# =====================================================

echo "💾 Criando instância primária..."

gcloud alloydb instances create $PRIMARY_INSTANCE_ID \
    --cluster=$CLUSTER_ID \
    --region=$REGION \
    --instance-type=PRIMARY \
    --cpu-count=16 \
    --memory-size=64GiB \
    --read-pool-node-count=2 \
    --database-flags=shared_buffers=16GB,\
work_mem=256MB,\
maintenance_work_mem=2GB,\
effective_cache_size=48GB,\
max_connections=500,\
random_page_cost=1.1,\
effective_io_concurrency=200,\
max_parallel_workers=8,\
max_parallel_workers_per_gather=4,\
max_parallel_maintenance_workers=4,\
checkpoint_completion_target=0.9,\
wal_buffers=16MB,\
default_statistics_target=100,\
shared_preload_libraries='pg_stat_statements,pgaudit,pg_hint_plan',\
log_statement='all',\
log_duration='on',\
log_min_duration_statement=100 \
    --availability-type=ZONAL \
    --labels=tipo=primaria,projeto=spt

# =====================================================
# 5. CRIAR INSTÂNCIA READ REPLICA (OPCIONAL)
# =====================================================

echo "📖 Criando read replica..."

gcloud alloydb instances create $READ_INSTANCE_ID \
    --cluster=$CLUSTER_ID \
    --region=$REGION \
    --instance-type=READ_POOL \
    --cpu-count=8 \
    --memory-size=32GiB \
    --read-pool-node-count=1 \
    --availability-type=ZONAL \
    --labels=tipo=replica,projeto=spt

# =====================================================
# 6. CONFIGURAR USUÁRIOS E SENHAS
# =====================================================

echo "🔐 Configurando usuários..."

# Definir senha do usuário postgres
export POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Salvar senha no Secret Manager
echo -n $POSTGRES_PASSWORD | gcloud secrets create spt-postgres-password \
    --data-file=- \
    --replication-policy="automatic" \
    --labels="projeto=spt,tipo=senha"

# Atualizar senha do usuário postgres
gcloud alloydb users set-password postgres \
    --cluster=$CLUSTER_ID \
    --region=$REGION \
    --password=$POSTGRES_PASSWORD

# =====================================================
# 7. CONFIGURAR FIREWALL E ACESSO
# =====================================================

echo "🔥 Configurando firewall..."

# Criar regra de firewall para AlloyDB
gcloud compute firewall-rules create allow-alloydb-spt \
    --network=$NETWORK_NAME \
    --allow=tcp:5432 \
    --source-ranges=10.0.0.0/24 \
    --target-tags=alloydb-client \
    --description="Permitir acesso ao AlloyDB para projeto SPT"

# Criar regra para Cloud SQL Proxy (se necessário)
gcloud compute firewall-rules create allow-sql-proxy-spt \
    --network=$NETWORK_NAME \
    --allow=tcp:3307 \
    --source-ranges=10.0.0.0/24 \
    --target-tags=sql-proxy \
    --description="Permitir acesso via Cloud SQL Proxy"

# =====================================================
# 8. CRIAR VM BASTION PARA ACESSO (OPCIONAL)
# =====================================================

echo "🖥️ Criando VM Bastion..."

gcloud compute instances create spt-bastion \
    --zone=$ZONE \
    --machine-type=e2-medium \
    --network-interface=network=$NETWORK_NAME,subnet=$SUBNET_NAME \
    --metadata=enable-oslogin=true \
    --maintenance-policy=MIGRATE \
    --tags=alloydb-client,sql-proxy \
    --create-disk=auto-delete=yes,boot=yes,device-name=spt-bastion,image-project=ubuntu-os-cloud,image-family=ubuntu-2204-lts,size=20GB \
    --labels=projeto=spt,tipo=bastion

# =====================================================
# 9. INSTALAR FERRAMENTAS NA VM BASTION
# =====================================================

echo "🛠️ Configurando VM Bastion..."

# Conectar na VM e instalar ferramentas
gcloud compute ssh spt-bastion --zone=$ZONE --command='
    # Atualizar sistema
    sudo apt-get update && sudo apt-get upgrade -y
    
    # Instalar PostgreSQL client
    sudo apt-get install -y postgresql-client-15 postgresql-contrib
    
    # Instalar pgvector extension tools
    sudo apt-get install -y build-essential git
    git clone https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    sudo make install
    
    # Instalar Python e pip para scripts
    sudo apt-get install -y python3-pip python3-dev
    pip3 install psycopg2-binary pandas numpy google-cloud-alloydb
    
    # Instalar Cloud SQL Proxy
    wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
    chmod +x cloud_sql_proxy
    sudo mv cloud_sql_proxy /usr/local/bin/
    
    # Instalar ferramentas de monitoramento
    sudo apt-get install -y htop iotop nethogs pgbadger
'

# =====================================================
# 10. OBTER INFORMAÇÕES DE CONEXÃO
# =====================================================

echo "📋 Obtendo informações de conexão..."

# Obter IP da instância primária
export PRIMARY_IP=$(gcloud alloydb instances describe $PRIMARY_INSTANCE_ID \
    --cluster=$CLUSTER_ID \
    --region=$REGION \
    --format="value(ipAddress)")

# Obter connection string
export CONNECTION_NAME=$(gcloud alloydb instances describe $PRIMARY_INSTANCE_ID \
    --cluster=$CLUSTER_ID \
    --region=$REGION \
    --format="value(name)")

echo "
========================================
🎉 ALLOYDB CONFIGURADO COM SUCESSO!
========================================

INFORMAÇÕES DE CONEXÃO:
-----------------------
Cluster: $CLUSTER_ID
Região: $REGION
IP Primário: $PRIMARY_IP
Connection Name: $CONNECTION_NAME

CONEXÃO VIA BASTION:
--------------------
1. Conectar no bastion:
   gcloud compute ssh spt-bastion --zone=$ZONE

2. Conectar no AlloyDB:
   psql -h $PRIMARY_IP -U postgres -d postgres

CONEXÃO VIA CLOUD SQL PROXY:
-----------------------------
cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432

SENHA POSTGRES:
---------------
gcloud secrets versions access latest --secret=spt-postgres-password

========================================
"

# =====================================================
# 11. SCRIPT DE CONEXÃO E CRIAÇÃO DO BANCO
# =====================================================

echo "💾 Criando script de inicialização do banco..."

cat > init_spt_database.sql << 'EOF'
-- =====================================================
-- INICIALIZAÇÃO DO BANCO SPT NO ALLOYDB
-- =====================================================

-- Criar database dedicado
CREATE DATABASE spt_production
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    TEMPLATE = template0;

-- Conectar no novo banco
\c spt_production

-- Criar usuários específicos
CREATE USER spt_admin WITH PASSWORD 'CHANGE_ME_ADMIN_PWD';
CREATE USER spt_app WITH PASSWORD 'CHANGE_ME_APP_PWD';
CREATE USER spt_ai_service WITH PASSWORD 'CHANGE_ME_AI_PWD';
CREATE USER spt_readonly WITH PASSWORD 'CHANGE_ME_RO_PWD';

-- Conceder privilégios
ALTER USER spt_admin WITH CREATEDB CREATEROLE;
GRANT ALL PRIVILEGES ON DATABASE spt_production TO spt_admin;
GRANT CONNECT ON DATABASE spt_production TO spt_app;
GRANT CONNECT ON DATABASE spt_production TO spt_ai_service;
GRANT CONNECT ON DATABASE spt_production TO spt_readonly;

-- Configurar search_path padrão
ALTER DATABASE spt_production SET search_path TO spt, spt_ai, public;

-- Habilitar extensões
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pgaudit";

-- Configurações específicas do AlloyDB
ALTER SYSTEM SET google_columnar_engine.enabled = on;
ALTER SYSTEM SET google_columnar_engine.memory_size_in_mb = 8192;
ALTER SYSTEM SET google_columnar_engine.enabled_tables = 'spt.*,spt_ai.*';

-- Reload configurações
SELECT pg_reload_conf();

\echo 'Database SPT criado com sucesso!'
EOF

# =====================================================
# 12. SCRIPT DE MONITORAMENTO
# =====================================================

echo "📊 Criando script de monitoramento..."

cat > monitor_alloydb.sh << 'EOF'
#!/bin/bash
# Script de monitoramento AlloyDB

CLUSTER_ID="spt-alloydb-cluster"
REGION="southamerica-east1"

echo "=== ALLOYDB MONITORING DASHBOARD ==="
echo "Timestamp: $(date)"
echo ""

# Status do Cluster
echo "📊 CLUSTER STATUS:"
gcloud alloydb clusters describe $CLUSTER_ID \
    --region=$REGION \
    --format="table(name,state,createTime)"

# Status das Instâncias
echo ""
echo "💾 INSTANCES STATUS:"
gcloud alloydb instances list \
    --cluster=$CLUSTER_ID \
    --region=$REGION \
    --format="table(name,instanceType,state,cpuCount,memorySize)"

# Backups
echo ""
echo "💼 RECENT BACKUPS:"
gcloud alloydb backups list \
    --location=$REGION \
    --filter="clusterName:$CLUSTER_ID" \
    --limit=5 \
    --format="table(name,state,createTime,sizeBytes)"

# Métricas de CPU
echo ""
echo "🔥 CPU USAGE (Last 1 hour):"
gcloud monitoring read \
    "alloydb.googleapis.com/cluster/cpu/utilization" \
    --project=$PROJECT_ID \
    --filter='resource.labels.cluster_id="'$CLUSTER_ID'"' \
    --start-time="-1h" \
    --format="table(points[0].value.double_value:label=cpu_usage)"

# Métricas de Memória
echo ""
echo "💾 MEMORY USAGE (Last 1 hour):"
gcloud monitoring read \
    "alloydb.googleapis.com/cluster/memory/utilization" \
    --project=$PROJECT_ID \
    --filter='resource.labels.cluster_id="'$CLUSTER_ID'"' \
    --start-time="-1h" \
    --format="table(points[0].value.double_value:label=memory_usage)"
EOF

chmod +x monitor_alloydb.sh

# =====================================================
# 13. BACKUP INICIAL
# =====================================================

echo "💾 Criando backup inicial..."

gcloud alloydb backups create $BACKUP_ID \
    --cluster=$CLUSTER_ID \
    --location=$REGION \
    --type=ON_DEMAND \
    --description="Backup inicial após configuração do cluster SPT" \
    --labels=tipo=inicial,projeto=spt

# =====================================================
# 14. ALERTAS E NOTIFICAÇÕES
# =====================================================

echo "🔔 Configurando alertas..."

# Criar canal de notificação (email)
gcloud alpha monitoring channels create \
    --display-name="SPT AlloyDB Alerts" \
    --type=email \
    --channel-labels=email_address=spt-alerts@transpetro.com.br

# Criar política de alerta para CPU alta
gcloud alpha monitoring policies create \
    --display-name="SPT AlloyDB High CPU" \
    --condition-display-name="CPU > 80%" \
    --condition-expression='
        resource.type="alloydb.googleapis.com/Cluster" AND
        metric.type="alloydb.googleapis.com/cluster/cpu/utilization" AND
        metric.value > 0.8' \
    --duration=300s \
    --notification-channels="SPT AlloyDB Alerts"

# =====================================================
# 15. OTIMIZAÇÕES ESPECÍFICAS PARA IA/ML
# =====================================================

echo "🤖 Aplicando otimizações para IA/ML..."

# Script SQL para otimizações de IA
cat > optimize_for_ai.sql << 'EOF'
-- Conectar no banco
\c spt_production

-- Configurações otimizadas para operações vetoriais
ALTER SYSTEM SET max_parallel_workers = 16;
ALTER SYSTEM SET max_parallel_workers_per_gather = 8;
ALTER SYSTEM SET max_parallel_maintenance_workers = 4;
ALTER SYSTEM SET work_mem = '512MB';
ALTER SYSTEM SET maintenance_work_mem = '4GB';
ALTER SYSTEM SET effective_cache_size = '48GB';
ALTER SYSTEM SET random_page_cost = 1.0;
ALTER SYSTEM SET seq_page_cost = 1.0;

-- Otimizações para JSONB
ALTER SYSTEM SET gin_pending_list_limit = '4MB';
ALTER SYSTEM SET gin_fuzzy_search_limit = 1000;

-- Configurações de autovacuum para tabelas grandes
ALTER SYSTEM SET autovacuum_max_workers = 6;
ALTER SYSTEM SET autovacuum_naptime = '30s';
ALTER SYSTEM SET autovacuum_vacuum_threshold = 50;
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;
ALTER SYSTEM SET autovacuum_analyze_threshold = 50;
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;

-- Reload configurações
SELECT pg_reload_conf();

-- Criar índices específicos para ML
CREATE INDEX IF NOT EXISTS idx_vector_ops ON spt.analise_risco 
USING ivfflat (anri_tx_embedding vector_cosine_ops) 
WITH (lists = 1000);

ANALYZE;
EOF

# =====================================================
# FIM DO SCRIPT DE SETUP
# =====================================================

echo "
✅ SETUP COMPLETO!

PRÓXIMOS PASSOS:
1. Conecte no bastion e execute o DDL do banco
2. Configure as senhas dos usuários do aplicativo
3. Execute o script de otimização para IA
4. Configure o pipeline de CI/CD
5. Implemente o monitoramento contínuo

COMANDOS ÚTEIS:
--------------
# Conectar no bastion:
gcloud compute ssh spt-bastion --zone=$ZONE

# Ver logs do cluster:
gcloud alloydb operations list --cluster=$CLUSTER_ID --region=$REGION

# Fazer backup manual:
gcloud alloydb backups create manual-$(date +%Y%m%d-%H%M%S) \
    --cluster=$CLUSTER_ID \
    --location=$REGION

# Monitorar performance:
./monitor_alloydb.sh

DOCUMENTAÇÃO:
https://cloud.google.com/alloydb/docs
"
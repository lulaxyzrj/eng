#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONNECTIONS_DIR="$PROJECT_ROOT/connections"

echo "🔗 Creating ShadowTraffic Connection Templates"
echo "============================================="
echo ""

mkdir -p "$CONNECTIONS_DIR"
echo "📁 Created directory: $CONNECTIONS_DIR"
echo ""

cat > "$CONNECTIONS_DIR/azure-blob.json" << 'EOF'
{
    "kind": "azureBlobStorage",
    "description": "Production Azure Blob Storage for data lake scenarios",
    "config": {
        "kind": "azureBlobStorage",
        "connectionConfigs": {
            "connectionString": "DefaultEndpointsProtocol=https;AccountName=owshqblobstg;AccountKey=lmKoi0C1eXYJ/10fOqh+4im0CT8wyw/MWbUqmNooiH6yH2mmNS1HtiZNMXDUvCEc0TRtC/3i2eat+AStq3oURg==;EndpointSuffix=core.windows.net"
        },
        "batchConfigs": {
            "lingerMs": 2000,
            "batchElements": 10000,
            "batchBytes": 5242880
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/azure-blob-dev.json" << 'EOF'
{
    "kind": "azureBlobStorage",
    "description": "Development Azure Blob Storage",
    "config": {
        "kind": "azureBlobStorage",
        "connectionConfigs": {
            "connectionString": "${AZURE_STORAGE_CONNECTION_STRING_DEV}"
        },
        "batchConfigs": {
            "lingerMs": 1000,
            "batchElements": 5000,
            "batchBytes": 2621440
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/kafka-local.json" << 'EOF'
{
    "kind": "kafka",
    "description": "Local Kafka development environment",
    "config": {
        "kind": "kafka",
        "producerConfigs": {
            "bootstrap.servers": "localhost:9092",
            "key.serializer": "org.apache.kafka.common.serialization.StringSerializer",
            "value.serializer": "org.apache.kafka.common.serialization.StringSerializer",
            "acks": "all",
            "retries": 3,
            "batch.size": 16384,
            "linger.ms": 1,
            "buffer.memory": 33554432,
            "compression.type": "snappy"
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/kafka-prod.json" << 'EOF'
{
    "kind": "kafka",
    "description": "Production Kafka cluster with security and optimizations",
    "config": {
        "kind": "kafka",
        "producerConfigs": {
            "bootstrap.servers": "kafka-prod-1:9092,kafka-prod-2:9092,kafka-prod-3:9092",
            "key.serializer": "org.apache.kafka.common.serialization.StringSerializer",
            "value.serializer": "org.apache.kafka.common.serialization.StringSerializer",
            "security.protocol": "SASL_SSL",
            "sasl.mechanism": "PLAIN",
            "sasl.jaas.config": "org.apache.kafka.common.security.plain.PlainLoginModule required username='shadowtraffic' password='${KAFKA_PASSWORD}';",
            "acks": "all",
            "retries": 5,
            "batch.size": 32768,
            "linger.ms": 10,
            "buffer.memory": 67108864,
            "compression.type": "snappy",
            "max.in.flight.requests.per.connection": 5,
            "enable.idempotence": true,
            "request.timeout.ms": 30000,
            "delivery.timeout.ms": 120000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/kafka-confluent.json" << 'EOF'
{
    "kind": "kafka",
    "description": "Confluent Cloud managed Kafka service",
    "config": {
        "kind": "kafka",
        "producerConfigs": {
            "bootstrap.servers": "${CONFLUENT_BOOTSTRAP_SERVERS}",
            "key.serializer": "org.apache.kafka.common.serialization.StringSerializer",
            "value.serializer": "org.apache.kafka.common.serialization.StringSerializer",
            "security.protocol": "SASL_SSL",
            "sasl.mechanism": "PLAIN",
            "sasl.jaas.config": "org.apache.kafka.common.security.plain.PlainLoginModule required username='${CONFLUENT_API_KEY}' password='${CONFLUENT_API_SECRET}';",
            "acks": "all",
            "retries": 5,
            "batch.size": 32768,
            "linger.ms": 10,
            "buffer.memory": 67108864,
            "compression.type": "snappy",
            "enable.idempotence": true
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/minio-local.json" << 'EOF'
{
    "kind": "minio",
    "description": "Local MinIO S3-compatible storage for development",
    "config": {
        "kind": "s3",
        "connectionConfigs": {
            "region": "us-east-1",
            "bucket": "shadowtraffic-data",
            "endpoint": "http://localhost:9000",
            "accessKey": "minioadmin",
            "secretKey": "minioadmin",
            "pathStyleAccess": true
        },
        "batchConfigs": {
            "lingerMs": 2000,
            "batchElements": 10000,
            "batchBytes": 5242880
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/s3-dev.json" << 'EOF'
{
    "kind": "s3",
    "description": "Development Amazon S3 bucket",
    "config": {
        "kind": "s3",
        "connectionConfigs": {
            "region": "us-east-1",
            "bucket": "shadowtraffic-dev-bucket",
            "accessKey": "${AWS_ACCESS_KEY_ID}",
            "secretKey": "${AWS_SECRET_ACCESS_KEY}"
        },
        "batchConfigs": {
            "lingerMs": 2000,
            "batchElements": 10000,
            "batchBytes": 5242880
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/s3-prod.json" << 'EOF'
{
    "kind": "s3",
    "description": "Production Amazon S3 bucket with encryption",
    "config": {
        "kind": "s3",
        "connectionConfigs": {
            "region": "us-east-1",
            "bucket": "shadowtraffic-prod-bucket",
            "accessKey": "${AWS_ACCESS_KEY_ID}",
            "secretKey": "${AWS_SECRET_ACCESS_KEY}",
            "serverSideEncryption": "AES256"
        },
        "batchConfigs": {
            "lingerMs": 5000,
            "batchElements": 50000,
            "batchBytes": 10485760
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/postgres-dev.json" << 'EOF'
{
    "kind": "postgres",
    "description": "PostgreSQL development database",
    "config": {
        "kind": "jdbc",
        "connectionConfigs": {
            "jdbcUrl": "jdbc:postgresql://localhost:5432/shadowtraffic",
            "username": "postgres",
            "password": "password",
            "driverClassName": "org.postgresql.Driver"
        },
        "batchConfigs": {
            "batchSize": 1000,
            "flushIntervalMs": 5000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/postgres-prod.json" << 'EOF'
{
    "kind": "postgres",
    "description": "Production PostgreSQL with connection pooling and SSL",
    "config": {
        "kind": "jdbc",
        "connectionConfigs": {
            "jdbcUrl": "jdbc:postgresql://postgres-prod:5432/shadowtraffic_prod?ssl=true&sslmode=require",
            "username": "${DB_USERNAME}",
            "password": "${DB_PASSWORD}",
            "driverClassName": "org.postgresql.Driver",
            "maximumPoolSize": 10,
            "minimumIdle": 2,
            "connectionTimeout": 30000,
            "idleTimeout": 600000,
            "maxLifetime": 1800000,
            "leakDetectionThreshold": 60000
        },
        "batchConfigs": {
            "batchSize": 5000,
            "flushIntervalMs": 10000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/mysql-dev.json" << 'EOF'
{
    "kind": "mysql",
    "description": "MySQL development database",
    "config": {
        "kind": "jdbc",
        "connectionConfigs": {
            "jdbcUrl": "jdbc:mysql://localhost:3306/shadowtraffic?useSSL=false&serverTimezone=UTC",
            "username": "root",
            "password": "password",
            "driverClassName": "com.mysql.cj.jdbc.Driver"
        },
        "batchConfigs": {
            "batchSize": 1000,
            "flushIntervalMs": 5000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/mysql-prod.json" << 'EOF'
{
    "kind": "mysql",
    "description": "Production MySQL with SSL and connection pooling",
    "config": {
        "kind": "jdbc",
        "connectionConfigs": {
            "jdbcUrl": "jdbc:mysql://mysql-prod:3306/shadowtraffic_prod?useSSL=true&serverTimezone=UTC&requireSSL=true",
            "username": "${DB_USERNAME}",
            "password": "${DB_PASSWORD}",
            "driverClassName": "com.mysql.cj.jdbc.Driver",
            "maximumPoolSize": 10,
            "minimumIdle": 2,
            "connectionTimeout": 30000,
            "idleTimeout": 600000,
            "maxLifetime": 1800000
        },
        "batchConfigs": {
            "batchSize": 5000,
            "flushIntervalMs": 10000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/snowflake-dev.json" << 'EOF'
{
    "kind": "snowflake",
    "description": "Snowflake development warehouse",
    "config": {
        "kind": "jdbc",
        "connectionConfigs": {
            "jdbcUrl": "jdbc:snowflake://${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/?warehouse=${SNOWFLAKE_WAREHOUSE_DEV}&db=${SNOWFLAKE_DATABASE_DEV}&schema=${SNOWFLAKE_SCHEMA_DEV}",
            "username": "${SNOWFLAKE_USERNAME}",
            "password": "${SNOWFLAKE_PASSWORD}",
            "driverClassName": "net.snowflake.client.jdbc.SnowflakeDriver"
        },
        "batchConfigs": {
            "batchSize": 5000,
            "flushIntervalMs": 15000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/snowflake-prod.json" << 'EOF'
{
    "kind": "snowflake",
    "description": "Snowflake production data warehouse",
    "config": {
        "kind": "jdbc",
        "connectionConfigs": {
            "jdbcUrl": "jdbc:snowflake://${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/?warehouse=${SNOWFLAKE_WAREHOUSE}&db=${SNOWFLAKE_DATABASE}&schema=${SNOWFLAKE_SCHEMA}",
            "username": "${SNOWFLAKE_USERNAME}",
            "password": "${SNOWFLAKE_PASSWORD}",
            "driverClassName": "net.snowflake.client.jdbc.SnowflakeDriver"
        },
        "batchConfigs": {
            "batchSize": 10000,
            "flushIntervalMs": 30000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/bigquery-dev.json" << 'EOF'
{
    "kind": "bigquery",
    "description": "Google BigQuery development dataset",
    "config": {
        "kind": "bigquery",
        "connectionConfigs": {
            "projectId": "${GCP_PROJECT_ID}",
            "datasetId": "${BIGQUERY_DATASET_DEV}",
            "credentialsPath": "${GOOGLE_APPLICATION_CREDENTIALS}",
            "location": "US"
        },
        "batchConfigs": {
            "batchSize": 5000,
            "flushIntervalMs": 15000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/bigquery-prod.json" << 'EOF'
{
    "kind": "bigquery",
    "description": "Google BigQuery production data warehouse",
    "config": {
        "kind": "bigquery",
        "connectionConfigs": {
            "projectId": "${GCP_PROJECT_ID}",
            "datasetId": "${BIGQUERY_DATASET}",
            "credentialsPath": "${GOOGLE_APPLICATION_CREDENTIALS}",
            "location": "US"
        },
        "batchConfigs": {
            "batchSize": 10000,
            "flushIntervalMs": 30000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/redshift-prod.json" << 'EOF'
{
    "kind": "redshift",
    "description": "Amazon Redshift production data warehouse",
    "config": {
        "kind": "jdbc",
        "connectionConfigs": {
            "jdbcUrl": "jdbc:redshift://${REDSHIFT_CLUSTER}.${REDSHIFT_REGION}.redshift.amazonaws.com:5439/${REDSHIFT_DATABASE}?ssl=true",
            "username": "${REDSHIFT_USERNAME}",
            "password": "${REDSHIFT_PASSWORD}",
            "driverClassName": "com.amazon.redshift.jdbc.Driver"
        },
        "batchConfigs": {
            "batchSize": 25000,
            "flushIntervalMs": 60000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/databricks-prod.json" << 'EOF'
{
    "kind": "databricks",
    "description": "Databricks unified analytics platform",
    "config": {
        "kind": "jdbc",
        "connectionConfigs": {
            "jdbcUrl": "jdbc:databricks://${DATABRICKS_SERVER_HOSTNAME}:443/default;transportMode=http;ssl=1;httpPath=${DATABRICKS_HTTP_PATH}",
            "username": "token",
            "password": "${DATABRICKS_TOKEN}",
            "driverClassName": "com.databricks.client.jdbc.Driver"
        },
        "batchConfigs": {
            "batchSize": 10000,
            "flushIntervalMs": 30000
        }
    }
}
EOF

cat > "$CONNECTIONS_DIR/elasticsearch-prod.json" << 'EOF'
{
    "kind": "elasticsearch",
    "description": "Elasticsearch cluster for search and analytics",
    "config": {
        "kind": "elasticsearch",
        "connectionConfigs": {
            "hosts": ["${ELASTICSEARCH_HOST}:9200"],
            "username": "${ELASTICSEARCH_USERNAME}",
            "password": "${ELASTICSEARCH_PASSWORD}",
            "scheme": "https",
            "index": "shadowtraffic-data"
        },
        "batchConfigs": {
            "batchSize": 5000,
            "flushIntervalMs": 10000
        }
    }
}
EOF

echo "✅ Created connection files:"
echo ""

for file in "$CONNECTIONS_DIR"/*.json; do
    if [ -f "$file" ]; then
        local name=$(basename "$file" .json)
        local kind=$(jq -r '.kind // "unknown"' "$file" 2>/dev/null)
        local description=$(jq -r '.description // "No description"' "$file" 2>/dev/null)
        echo "  🔗 $name ($kind)"
        echo "     📝 $description"
        echo ""
    fi
done

echo "📊 Total connections created: $(ls -1 "$CONNECTIONS_DIR"/*.json | wc -l)"
echo ""
echo "🎯 Usage examples:"
echo "  ./dynamic-deploy.sh compose ubereats-full azure-blob"
echo "  ./dynamic-deploy.sh compose ubereats-core kafka-local"
echo "  ./dynamic-deploy.sh compose minimal-demo postgres-dev"
echo "  ./dynamic-deploy.sh compose analytics-subset snowflake-prod"
echo ""
echo "🔍 Management commands:"
echo "  ./utils.sh connections"
echo "  ./utils.sh matrix"
echo "  ./utils.sh recommend"
#!/bin/bash
set -e

echo "Creating ShadowTraffic configuration files from templates..."

if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file with your credentials first."
    exit 1
fi

# Lê a Connection String do .env
AZURE_STORAGE_CONNECTION_STRING=$(grep '^AZURE_STORAGE_CONNECTION_STRING=' .env | cut -d'=' -f2-)

# Lê o Nome do Container do .env (Novo passo)
AZURE_STORAGE_CONTAINER_NAME=$(grep '^AZURE_STORAGE_CONTAINER_NAME=' .env | cut -d'=' -f2-)

# Valida se o nome do container foi encontrado
if [ -z "$AZURE_STORAGE_CONTAINER_NAME" ]; then
    echo "Error: AZURE_STORAGE_CONTAINER_NAME not found in .env file."
    echo "Please add it to your .env file."
    exit 1
fi

echo "Copying template files..."
cp azure/uber-eats.json.template azure/uber-eats.json

echo "Configuring azure/uber-eats.json..."

# Substitui a Connection String (placeholder antigo)
sed -i.bak "s|REPLACE_WITH_AZURE_STORAGE_CONNECTION_STRING|${AZURE_STORAGE_CONNECTION_STRING}|g" azure/uber-eats.json

# Substitui o Container Name (novo placeholder)
sed -i.bak "s|REPLACE_WITH_CONTAINER_NAME|${AZURE_STORAGE_CONTAINER_NAME}|g" azure/uber-eats.json

# Remove o arquivo de backup criado pelo sed
rm azure/uber-eats.json.bak

echo ""
echo "✅ Configuration files created successfully!"
echo "   Target Container: ${AZURE_STORAGE_CONTAINER_NAME}"
echo ""
echo "Files created:"
echo "  - azure/uber-eats.json"
echo ""
echo "These files contain your credentials and are git-ignored."
echo "You can now run the ShadowTraffic generators."
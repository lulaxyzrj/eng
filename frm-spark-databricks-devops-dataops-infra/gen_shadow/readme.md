# ShadowTraffic Data Generation

This folder contains the setup to generate synthetic data for the UberEats project using [ShadowTraffic](https://shadowtraffic.io/).

For detailed documentation, please refer to the [Official ShadowTraffic Docs](https://shadowtraffic.io/docs/).

## 1. Prerequisites

Ensure you have the official ShadowTraffic Docker image installed:

```bash
docker pull shadowtraffic/shadowtraffic:latest
```

## 2. Azure Setup & Credentials

You need to retrieve your Azure Storage Connection String to allow ShadowTraffic to write data directly to your Data Lake (Landing Zone).

### 2.1. Login to Azure

```bash
# Refresh your login session
az logout
az login

# Confirm you are in the correct tenant
az account show --query tenantId -o tsv
```

### 2.2. Find your Storage Account

List the storage accounts in the dev resource group to find the correct name (e.g., `adlsubereatsdev...`):

```bash
az storage account list \
  --resource-group ubereats-dev-rg \
  --query "[].{Name:name, Location:location, Sku:sku.name}" \
  --output table
```

### 2.3. Get Connection String

Replace `{storage_account_name}` with the name found in the previous step:

```bash
az storage account show-connection-string \
  --name {storage_account_name} \
  --resource-group ubereats-dev-rg \
  --output tsv
```

*(Optional) Verify container name:*
```bash
az storage container list \
  --account-name {storage_account_name} \
  --auth-mode login \
  --output table
```

## 3. Configuration

### 3.1. Create Environment File

Create a `.env` file based on the template:

```bash
cp .env.template .env
```

Open `.env` and fill in:
1.  **ShadowTraffic License**: (If you have one, or use the free trial defaults if applicable).
2.  **AZURE_STORAGE_CONNECTION_STRING**: Paste the connection string retrieved in step 2.3.
3.  **AZURE_STORAGE_CONTAINER_NAME**: Default is `landing`.

### 3.2. Fix Permissions (Important!)

Docker mounts can sometimes create permission issues with the `azure` folder. Ensure the script can write to it:

```bash
# Ensure you are in the gen_shadow directory
cd gen_shadow

# Grant write permissions to the config folder
sudo chmod -R 777 azure
```

### 3.3. Generate Config File

Run the setup script to inject your credentials into the ShadowTraffic JSON configuration:

```bash
./setup-configs.sh
```

*This script creates `azure/uber-eats.json` with your actual connection string.*

## 4. Run Data Generator

Start the ShadowTraffic container. This command mounts your generated config and starts pumping data to Azure.

```bash
docker run --env-file .env \
  -v $(pwd)/azure/uber-eats.json:/home/config.json \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json
```

**Note:** You might see some "Unrecognized key format" warnings. These are usually harmless if the logs show "Now running" and "Generating streams".
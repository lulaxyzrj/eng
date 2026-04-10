# ==============================================================================
# Resource Group: Governance
# ==============================================================================
# Contains:
# - Access Connector (Managed Identity for Unity Catalog)
# - ADLS Gen2 for metastore storage (Root Storage)
# - The Unity Catalog Metastore itself (Account Level)
# ==============================================================================

resource "azurerm_resource_group" "governance" {
  name     = "${local.governance_name}-rg"
  location = var.location
  tags     = local.governance_tags
}

# ==============================================================================
# Access Connector for Azure Databricks
# ==============================================================================
# This is the key resource that allows Unity Catalog to access storage.
# The Managed Identity will be granted access to the root storage.

resource "azurerm_databricks_access_connector" "unity" {
  name                = "${local.governance_name}-access-connector"
  resource_group_name = azurerm_resource_group.governance.name
  location            = azurerm_resource_group.governance.location
  tags                = local.governance_tags

  identity {
    type = "SystemAssigned"
  }
}

# ==============================================================================
# Storage Account for Metastore (Root Storage)
# ==============================================================================

resource "azurerm_storage_account" "metastore" {
  name                     = "adls${var.prefix}meta${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.governance.name
  location                 = azurerm_resource_group.governance.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
  tags                     = local.governance_tags
}

resource "azurerm_storage_container" "metastore" {
  name                  = "metastore"
  storage_account_name  = azurerm_storage_account.metastore.name
  container_access_type = "private"
}

# ==============================================================================
# Role Assignment: Access Connector -> Metastore Storage
# ==============================================================================
# CRITICAL: This grants the Managed Identity permission to write to the bucket.

resource "azurerm_role_assignment" "unity_metastore" {
  scope                = azurerm_storage_account.metastore.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.unity.identity[0].principal_id
}

# ==============================================================================
# Metastore Creation (Global/Account Level)
# ==============================================================================

resource "databricks_metastore" "this" {
  provider = databricks.account

  name   = var.metastore_name
  region = var.location
  storage_root = format("abfss://%s@%s.dfs.core.windows.net/",
    azurerm_storage_container.metastore.name,
    azurerm_storage_account.metastore.name
  )
  force_destroy = true
}

# ==============================================================================
# Metastore Data Access (Root Credential)
# ==============================================================================
# This links the Metastore to the Access Connector.

resource "databricks_metastore_data_access" "this" {
  provider = databricks.account

  metastore_id = databricks_metastore.this.id
  name         = "${var.prefix}-access-connector"
  is_default   = true

  azure_managed_identity {
    access_connector_id = azurerm_databricks_access_connector.unity.id
  }

  # SAFETY LOCK:
  # We must wait for the Role Assignment to propagate in Azure AD before
  # Databricks tries to validate the storage access. Otherwise, it fails with 403.
  depends_on = [
    azurerm_role_assignment.unity_metastore
  ]
}
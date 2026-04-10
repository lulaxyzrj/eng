# ==============================================================================
# Resource Group: Governance
# ==============================================================================
# Contains:
# - Access Connector (Managed Identity for Unity Catalog)
# - ADLS Gen2 for metastore storage (optional, if using metastore root storage)
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
# The Managed Identity will be granted access to all storage accounts.

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
# Storage Account for Metastore (optional)
# ==============================================================================
# Only needed if you want metastore-level root storage.
# For strict catalog isolation, this can be omitted.

resource "azurerm_storage_account" "metastore" {
  name                     = "adls${var.prefix}meta${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.governance.name
  location                 = azurerm_resource_group.governance.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true # Required for ADLS Gen2
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

resource "azurerm_role_assignment" "unity_metastore" {
  scope                = azurerm_storage_account.metastore.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.unity.identity[0].principal_id
}

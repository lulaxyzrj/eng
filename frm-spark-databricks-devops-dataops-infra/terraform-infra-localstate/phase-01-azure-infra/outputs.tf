# ==============================================================================
# Outputs
# ==============================================================================
# These values will be used as inputs for Phase 02 (Unity Catalog)
# Phase 02 reads these automatically via terraform_remote_state.
# ==============================================================================

# ------------------------------------------------------------------------------
# Region
# ------------------------------------------------------------------------------

output "location" {
  description = "Azure region where resources were deployed"
  value       = var.location
}

# ------------------------------------------------------------------------------
# Access Connector
# ------------------------------------------------------------------------------

output "access_connector_id" {
  description = "Resource ID of the Access Connector (for Storage Credential)"
  value       = azurerm_databricks_access_connector.unity.id
}

output "access_connector_identity_id" {
  description = "Principal ID of the Access Connector Managed Identity"
  value       = azurerm_databricks_access_connector.unity.identity[0].principal_id
}

# ------------------------------------------------------------------------------
# Workspaces
# ------------------------------------------------------------------------------

output "dev_workspace_url" {
  description = "URL of the Dev Databricks workspace"
  value       = "https://${azurerm_databricks_workspace.dev.workspace_url}"
}

output "dev_workspace_id" {
  description = "Workspace ID of the Dev workspace (for metastore assignment)"
  value       = azurerm_databricks_workspace.dev.workspace_id
}

output "prod_workspace_url" {
  description = "URL of the Prod Databricks workspace"
  value       = "https://${azurerm_databricks_workspace.prod.workspace_url}"
}

output "prod_workspace_id" {
  description = "Workspace ID of the Prod workspace (for metastore assignment)"
  value       = azurerm_databricks_workspace.prod.workspace_id
}

# ------------------------------------------------------------------------------
# Storage Accounts
# ------------------------------------------------------------------------------

output "metastore_storage_path" {
  description = "ADLS path for metastore root storage"
  value       = "abfss://${azurerm_storage_container.metastore.name}@${azurerm_storage_account.metastore.name}.dfs.core.windows.net/"
}

output "dev_storage_path" {
  description = "ADLS base path for dev storage"
  value       = "abfss://bronze@${azurerm_storage_account.dev.name}.dfs.core.windows.net/"
}

output "prod_storage_path" {
  description = "ADLS base path for prod storage"
  value       = "abfss://bronze@${azurerm_storage_account.prod.name}.dfs.core.windows.net/"
}

output "dev_storage_account_name" {
  description = "Name of the dev storage account"
  value       = azurerm_storage_account.dev.name
}

output "prod_storage_account_name" {
  description = "Name of the prod storage account"
  value       = azurerm_storage_account.prod.name
}

# ------------------------------------------------------------------------------
# Resource Groups
# ------------------------------------------------------------------------------

output "resource_groups" {
  description = "Names of all resource groups created"
  value = {
    governance = azurerm_resource_group.governance.name
    dev        = azurerm_resource_group.dev.name
    prod       = azurerm_resource_group.prod.name
  }
}

# ------------------------------------------------------------------------------
# Summary for Phase 02
# ------------------------------------------------------------------------------

output "phase_02_inputs" {
  description = "Summary of values needed for Phase 02 Unity Catalog setup"
  value = <<-EOT

    =============================================================
    Phase 01 Complete!
    =============================================================

    Dev Workspace:  https://${azurerm_databricks_workspace.dev.workspace_url}
    Prod Workspace: https://${azurerm_databricks_workspace.prod.workspace_url}

    =============================================================
    Next Step: Run Phase 02
    =============================================================

    cd ../phase-02-unity-catalog
    ../scripts/02-deploy-unity-catalog.sh

    The script will:
    1. Read workspace URLs automatically from this state
    2. Prompt you for your Databricks Account ID
    3. Deploy Unity Catalog

    Get Account ID from: https://accounts.azuredatabricks.net
    (Click email top-right → Account Settings → Account ID)

    =============================================================

  EOT
}

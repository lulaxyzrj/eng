# ==============================================================================
# Data Sources - Remote State from Phase 01
# ==============================================================================
# Reads outputs from Phase 01 via Azure Storage backend.
# The backend configuration is passed via variables to allow dynamic
# configuration in CI/CD pipelines.
# ==============================================================================

data "terraform_remote_state" "phase_01" {
  backend = "azurerm"

  config = {
    resource_group_name  = var.backend_resource_group
    storage_account_name = var.backend_storage_account
    container_name       = var.backend_container
    key                  = "phase-01-azure-infra.tfstate"
  }
}

# ==============================================================================
# Local Values - Mapped from Remote State
# ==============================================================================
# We use locals to map remote outputs to internal names.
#
# CRITICAL: We use the try() function to provide fallback "placeholder" values.
# This ensures that 'terraform plan' runs successfully in CI/CD (e.g., inside a PR)
# even if Phase 01 has not been deployed yet (and the remote state is empty).
# These placeholders will be replaced by real values during the actual 'apply'
# after Phase 01 is deployed.
# ==============================================================================

locals {
  # Helper to access outputs safely
  phase1_outputs = data.terraform_remote_state.phase_01.outputs

  # Region
  # Default to "eastus2" if state is missing
  location = try(local.phase1_outputs.location, "eastus2")

  # Access Connector ID
  # Fallback to a dummy Azure Resource ID structure
  access_connector_id = try(
    local.phase1_outputs.access_connector_id,
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-placeholder/providers/Microsoft.Databricks/accessConnectors/placeholder"
  )

  # Workspace IDs (for metastore assignment)
  # Fallback to dummy 16-digit IDs
  dev_workspace_id  = try(local.phase1_outputs.dev_workspace_id, "0000000000000000")
  prod_workspace_id = try(local.phase1_outputs.prod_workspace_id, "0000000000000000")

  # Storage Paths (Metastore Root)
  metastore_storage_path = try(
    local.phase1_outputs.metastore_storage_path,
    "abfss://metastore@placeholder.dfs.core.windows.net/"
  )

  # Storage Account Names (for External Locations)
  dev_storage_account = try(
    local.phase1_outputs.dev_storage_account_name,
    "devstorageplaceholder"
  )

  prod_storage_account = try(
    local.phase1_outputs.prod_storage_account_name,
    "prodstorageplaceholder"
  )

  # Metastore ID (NEW)
  # Reads the ID created in Phase 01. Defaults to empty string to avoid plan errors.
  metastore_id = try(
    local.phase1_outputs.metastore_id,
    ""
  )
}
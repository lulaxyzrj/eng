# ==============================================================================
# Data Sources - Remote State from Phase 01
# ==============================================================================
# This reads outputs from Phase 01 automatically, eliminating manual copy/paste.
#
# NOTE: Workspace URLs cannot be read here because providers are configured
# before data sources. They must be passed as variables.
# ==============================================================================

data "terraform_remote_state" "phase_01" {
  backend = "local"

  config = {
    # Relative path from phase-02-unity-catalog to phase-01-azure-infra
    path = "${path.module}/../phase-01-azure-infra/terraform.tfstate"
  }
}

# ==============================================================================
# Local Values - Mapped from Remote State
# ==============================================================================
# Using locals makes the code cleaner and provides a single place to change
# if we switch to a different backend (e.g., Azure Storage, Terraform Cloud).

locals {
  # Region
  location = data.terraform_remote_state.phase_01.outputs.location

  # Access Connector
  access_connector_id = data.terraform_remote_state.phase_01.outputs.access_connector_id

  # Workspace IDs (for metastore assignment)
  dev_workspace_id  = data.terraform_remote_state.phase_01.outputs.dev_workspace_id
  prod_workspace_id = data.terraform_remote_state.phase_01.outputs.prod_workspace_id

  # Storage
  metastore_storage_path = data.terraform_remote_state.phase_01.outputs.metastore_storage_path
  dev_storage_account    = data.terraform_remote_state.phase_01.outputs.dev_storage_account_name
  prod_storage_account   = data.terraform_remote_state.phase_01.outputs.prod_storage_account_name
}

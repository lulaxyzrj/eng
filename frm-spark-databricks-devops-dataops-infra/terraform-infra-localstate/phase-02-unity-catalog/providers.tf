terraform {
  required_version = ">= 1.5.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
  }
}

# ==============================================================================
# Databricks Account-Level Provider
# ==============================================================================
# Used for: Metastore, Metastore Assignment, Account-level users/groups
# Authentication: Uses Azure CLI (az login)

provider "databricks" {
  alias      = "account"
  host       = "https://accounts.azuredatabricks.net"
  account_id = var.databricks_account_id
  auth_type  = "azure-cli"
}

# ==============================================================================
# Databricks Workspace-Level Provider (Dev)
# ==============================================================================
# Used for: Storage Credentials, External Locations, Catalogs, Schemas
# Authentication: Uses Azure CLI (az login)

provider "databricks" {
  alias     = "dev"
  host      = var.dev_workspace_url
  auth_type = "azure-cli"
}

# ==============================================================================
# Databricks Workspace-Level Provider (Prod)
# ==============================================================================

provider "databricks" {
  alias     = "prod"
  host      = var.prod_workspace_url
  auth_type = "azure-cli"
}
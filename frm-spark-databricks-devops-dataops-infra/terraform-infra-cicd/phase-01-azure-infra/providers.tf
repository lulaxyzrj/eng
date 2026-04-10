# ==============================================================================
# Terraform and Provider Configuration
# ==============================================================================
# This phase manages the physical infrastructure:
# - Azure Resources (RG, VNet, Storage, Access Connector)
# - Databricks Workspaces
# - Unity Catalog Metastore (Global/Account Level)
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.116"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    # Required for creating the Metastore at the account level
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
  }
}

# ==============================================================================
# Azure Provider
# ==============================================================================
# Uses Azure CLI credentials (local) or Service Principal via ARM_* env vars (CI/CD)

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
  skip_provider_registration = true
}

# ==============================================================================
# Databricks Account-Level Provider
# ==============================================================================
# Used exclusively to create the Global Metastore.
#
# NOTE: We do NOT define "dev" or "prod" providers here because the workspaces
# do not exist yet (they are being created in this phase).

provider "databricks" {
  alias      = "account"
  host       = "https://accounts.azuredatabricks.net"
  account_id = var.databricks_account_id
  auth_type  = "azure-client-secret"
}
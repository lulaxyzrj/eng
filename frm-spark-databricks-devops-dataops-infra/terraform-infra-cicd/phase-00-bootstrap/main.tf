# ==============================================================================
# Bootstrap - Terraform State Storage and Service Principal
# ==============================================================================
# This configuration creates the foundational resources for CI/CD:
# - Storage Account for Terraform remote state
# - Service Principal for GitHub Actions authentication
# - Required role assignments
# ==============================================================================

# ------------------------------------------------------------------------------
# Data Sources
# ------------------------------------------------------------------------------

data "azurerm_subscription" "current" {}

data "azurerm_client_config" "current" {}

# ------------------------------------------------------------------------------
# Random Suffix for Unique Names
# ------------------------------------------------------------------------------

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# ------------------------------------------------------------------------------
# Locals
# ------------------------------------------------------------------------------

locals {
  sp_name              = coalesce(var.service_principal_name, "${var.prefix}-terraform-sp")
  storage_account_name = "${var.prefix}tfstate${random_string.suffix.result}"
  resource_group_name  = "${var.prefix}-tfstate-rg"
}

# ------------------------------------------------------------------------------
# Resource Group for Terraform State
# ------------------------------------------------------------------------------

resource "azurerm_resource_group" "tfstate" {
  name     = local.resource_group_name
  location = var.location
  tags     = var.tags
}

# ------------------------------------------------------------------------------
# Storage Account for Terraform State
# ------------------------------------------------------------------------------

resource "azurerm_storage_account" "tfstate" {
  name                     = local.storage_account_name
  resource_group_name      = azurerm_resource_group.tfstate.name
  location                 = azurerm_resource_group.tfstate.location
  account_tier             = "Standard"
  account_replication_type = "GRS" # Geo-redundant for state safety
  account_kind             = "StorageV2"
  min_tls_version          = "TLS1_2"

  # Enable blob versioning for state recovery
  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }
  }

  tags = var.tags
}

# ------------------------------------------------------------------------------
# Storage Container for Terraform State
# ------------------------------------------------------------------------------

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.tfstate.name
  container_access_type = "private"
}

# ------------------------------------------------------------------------------
# Service Principal (App Registration)
# ------------------------------------------------------------------------------

resource "azuread_application" "terraform" {
  display_name = local.sp_name

  owners = [data.azurerm_client_config.current.object_id]

  tags = ["terraform", "ci-cd", var.prefix]
}

resource "azuread_service_principal" "terraform" {
  client_id = azuread_application.terraform.client_id

  owners = [data.azurerm_client_config.current.object_id]

  tags = ["terraform", "ci-cd", var.prefix]
}

# ------------------------------------------------------------------------------
# Service Principal Password (Client Secret)
# ------------------------------------------------------------------------------

resource "azuread_application_password" "terraform" {
  application_id = azuread_application.terraform.id
  display_name   = "Terraform CI/CD"

  end_date_relative = "${var.sp_password_rotation_days * 24}h"
}

# ------------------------------------------------------------------------------
# Role Assignment: Contributor on Subscription
# ------------------------------------------------------------------------------
# Allows the SP to create/manage all Azure resources

resource "azurerm_role_assignment" "sp_contributor" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.terraform.object_id
}

# ------------------------------------------------------------------------------
# Role Assignment: Storage Blob Data Contributor on State Storage
# ------------------------------------------------------------------------------
# Allows the SP to read/write Terraform state files

resource "azurerm_role_assignment" "sp_storage_blob" {
  scope                = azurerm_storage_account.tfstate.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azuread_service_principal.terraform.object_id
}

# ------------------------------------------------------------------------------
# Role Assignment: User Access Administrator (Optional)
# ------------------------------------------------------------------------------
# Allows the SP to create role assignments (needed for Access Connector → Storage)
# Comment out if you prefer to handle this separately

resource "azurerm_role_assignment" "sp_user_access_admin" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "User Access Administrator"
  principal_id         = azuread_service_principal.terraform.object_id
}

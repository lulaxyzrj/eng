# ==============================================================================
# Outputs
# ==============================================================================
# These values are needed to configure GitHub Secrets and backend configuration
# ==============================================================================

# ------------------------------------------------------------------------------
# Storage Account (for backend configuration)
# ------------------------------------------------------------------------------

output "resource_group_name" {
  description = "Name of the resource group containing tfstate storage"
  value       = azurerm_resource_group.tfstate.name
}

output "storage_account_name" {
  description = "Name of the storage account for Terraform state"
  value       = azurerm_storage_account.tfstate.name
}

output "container_name" {
  description = "Name of the blob container for Terraform state"
  value       = azurerm_storage_container.tfstate.name
}

# ------------------------------------------------------------------------------
# Service Principal Credentials (for GitHub Secrets)
# ------------------------------------------------------------------------------

output "client_id" {
  description = "Service Principal Application (Client) ID - use as ARM_CLIENT_ID"
  value       = azuread_application.terraform.client_id
}

output "client_secret" {
  description = "Service Principal Password - use as ARM_CLIENT_SECRET"
  value       = azuread_application_password.terraform.value
  sensitive   = true
}

output "tenant_id" {
  description = "Azure Tenant ID - use as ARM_TENANT_ID"
  value       = data.azurerm_client_config.current.tenant_id
}

output "subscription_id" {
  description = "Azure Subscription ID - use as ARM_SUBSCRIPTION_ID"
  value       = data.azurerm_subscription.current.subscription_id
}

# ------------------------------------------------------------------------------
# Service Principal Object ID (for Databricks)
# ------------------------------------------------------------------------------

output "service_principal_object_id" {
  description = "Service Principal Object ID - needed for Databricks Account Admin assignment"
  value       = azuread_service_principal.terraform.object_id
}

# ------------------------------------------------------------------------------
# Backend Configuration Block (copy to other phases)
# ------------------------------------------------------------------------------

output "backend_config" {
  description = "Backend configuration block to copy into phase-01 and phase-02"
  value       = <<-EOT
    
    # Add this to your providers.tf or create a new backend.tf file:
    
    terraform {
      backend "azurerm" {
        resource_group_name  = "${azurerm_resource_group.tfstate.name}"
        storage_account_name = "${azurerm_storage_account.tfstate.name}"
        container_name       = "${azurerm_storage_container.tfstate.name}"
        key                  = "CHANGE_ME.tfstate"  # Use unique key per phase
        use_oidc             = true                 # For GitHub Actions with OIDC
      }
    }
    
  EOT
}

# ------------------------------------------------------------------------------
# GitHub Secrets Summary
# ------------------------------------------------------------------------------

output "github_secrets_summary" {
  description = "Summary of secrets to configure in GitHub"
  value       = <<-EOT
    
    ============================================================
    GitHub Repository Secrets to Configure
    ============================================================
    
    Go to: GitHub Repo → Settings → Secrets and variables → Actions
    
    Copy these values exactly:
    
    Secret Name             Value
    -----------             -----
    ARM_CLIENT_ID           ${azuread_application.terraform.client_id}
    ARM_TENANT_ID           ${data.azurerm_client_config.current.tenant_id}
    ARM_SUBSCRIPTION_ID     ${data.azurerm_subscription.current.subscription_id}
    TF_BACKEND_SA           ${azurerm_storage_account.tfstate.name}
    
    For ARM_CLIENT_SECRET, run:
      terraform output -raw client_secret
    
    ============================================================
    DATABRICKS_ACCOUNT_ID (Manual Step)
    ============================================================
    
    This value comes from Databricks, not Azure:
    
    1. Go to: https://accounts.azuredatabricks.net
    2. Click your email (top right) → Account Settings
    3. Copy the "Account ID" (UUID format)
    4. Add to GitHub Secrets as: DATABRICKS_ACCOUNT_ID
    
    ============================================================
    Databricks Account Admin (Manual Step)
    ============================================================
    
    1. Go to: https://accounts.azuredatabricks.net
    2. Navigate to: User Management → Service Principals
    3. Click: Add service principal
    4. Enter Application ID: ${azuread_application.terraform.client_id}
    5. Assign role: Account Admin
    
    ============================================================
    
  EOT
}

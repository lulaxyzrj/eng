# ==============================================================================
# Phase 01 - Azure Infrastructure Variables
# ==============================================================================

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "eastus2"
}

variable "prefix" {
  description = "Prefix for all resource names"
  type        = string
  default     = "ubereats"

  validation {
    condition     = length(var.prefix) <= 10
    error_message = "Prefix must be 10 characters or less for storage account naming."
  }
}

variable "databricks_sku" {
  description = "Databricks workspace SKU (premium required for Unity Catalog)"
  type        = string
  default     = "premium"

  validation {
    condition     = contains(["premium", "trial"], var.databricks_sku)
    error_message = "Unity Catalog requires premium or trial SKU."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project   = "UberEats"
    ManagedBy = "Terraform"
  }
}

# ==============================================================================
# Unity Catalog Variables (Added for Metastore Creation)
# ==============================================================================

variable "databricks_account_id" {
  description = "Databricks Account ID (Required for creating account-level Metastore)"
  type        = string
  sensitive   = true
}

variable "metastore_name" {
  description = "Name for the Unity Catalog metastore"
  type        = string
  default     = "ubereats-metastore"
}
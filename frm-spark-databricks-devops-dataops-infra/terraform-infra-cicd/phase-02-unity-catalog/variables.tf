# ==============================================================================
# Phase 02 - Unity Catalog Variables
# ==============================================================================

# ------------------------------------------------------------------------------
# Backend Variables (Remote State Configuration)
# ------------------------------------------------------------------------------
# These are used in data-sources.tf to locate Phase 01 state

variable "backend_resource_group" {
  description = "Resource group containing the tfstate storage account"
  type        = string
}

variable "backend_storage_account" {
  description = "Storage account name for tfstate"
  type        = string
}

variable "backend_container" {
  description = "Container name for tfstate"
  type        = string
  default     = "tfstate"
}

# ------------------------------------------------------------------------------
# Databricks Connection Variables
# ------------------------------------------------------------------------------

variable "databricks_account_id" {
  description = "Databricks Account ID (Required for Account-level operations)"
  type        = string
  sensitive   = true
}

variable "dev_workspace_url" {
  description = "Dev Databricks workspace URL (e.g., https://adb-xxx.xx.azuredatabricks.net)"
  type        = string
}

variable "prod_workspace_url" {
  description = "Prod Databricks workspace URL (e.g., https://adb-xxx.xx.azuredatabricks.net)"
  type        = string
}

# ------------------------------------------------------------------------------
# Naming & Resources
# ------------------------------------------------------------------------------

variable "prefix" {
  description = "Prefix for resource names (e.g., storage credentials, catalogs)"
  type        = string
  default     = "ubereats"
}

# NOTE: "metastore_name" was removed because Phase 02 now reads the Metastore ID
# directly from Phase 01 remote state, avoiding lookup conflicts.

# ------------------------------------------------------------------------------
# Security Variables
# ------------------------------------------------------------------------------

variable "data_engineers_members" {
  description = "List of user emails to add to the data-engineers group"
  type        = list(string)
  default     = []
}
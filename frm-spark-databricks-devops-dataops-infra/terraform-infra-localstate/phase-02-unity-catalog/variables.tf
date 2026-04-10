# ==============================================================================
# Phase 02 Variables
# ==============================================================================

variable "databricks_account_id" {
  description = "Databricks Account ID (from accounts.azuredatabricks.net)"
  type        = string
}

variable "dev_workspace_url" {
  description = "Dev Databricks workspace URL (e.g., https://adb-xxx.xx.azuredatabricks.net)"
  type        = string
}

variable "prod_workspace_url" {
  description = "Prod Databricks workspace URL (e.g., https://adb-xxx.xx.azuredatabricks.net)"
  type        = string
}

variable "prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "ubereats"
}

variable "metastore_name" {
  description = "Name for the Unity Catalog metastore"
  type        = string
  default     = "ubereats-metastore"
}

# ==============================================================================
# Security Variables
# ==============================================================================

variable "data_engineers_members" {
  description = "List of user emails to add to data-engineers group"
  type        = list(string)
  default     = []
}
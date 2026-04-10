# ==============================================================================
# Variables
# ==============================================================================

variable "location" {
  description = "Azure region for the tfstate resources"
  type        = string
  default     = "eastus2"
}

variable "prefix" {
  description = "Prefix for resource names (should match your main infrastructure)"
  type        = string
  default     = "ubereats"

  validation {
    condition     = length(var.prefix) <= 10
    error_message = "Prefix must be 10 characters or less for storage account naming."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project   = "UberEats"
    ManagedBy = "Terraform"
    Purpose   = "CI/CD Bootstrap"
  }
}

variable "service_principal_name" {
  description = "Display name for the Service Principal"
  type        = string
  default     = null # Will default to {prefix}-terraform-sp
}

variable "sp_password_rotation_days" {
  description = "Number of days before the Service Principal password expires"
  type        = number
  default     = 365
}

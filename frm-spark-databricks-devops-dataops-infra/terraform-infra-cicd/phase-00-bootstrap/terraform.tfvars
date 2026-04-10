# ==============================================================================
# Phase 00 - Bootstrap Variables
# ==============================================================================
# Copy this file to terraform.tfvars and adjust values as needed
# ==============================================================================

location = "eastus2"
prefix   = "ubereats"

tags = {
  Project   = "UberEats"
  ManagedBy = "Terraform"
  Purpose   = "CI/CD Bootstrap"
}

# Service Principal settings
# service_principal_name    = "ubereats-terraform-sp"  # Optional, defaults to {prefix}-terraform-sp
# sp_password_rotation_days = 365                       # Days until password expires

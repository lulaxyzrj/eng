# ==============================================================================
# Phase 01 - Azure Infrastructure
# ==============================================================================
# Copy this file to terraform.tfvars and fill in your values
# ==============================================================================

location       = "eastus2"
prefix         = "ubereats"
databricks_sku = "premium"

tags = {
  Project   = "UberEats"
  ManagedBy = "Terraform"
  Owner     = "Data Platform Team"
}

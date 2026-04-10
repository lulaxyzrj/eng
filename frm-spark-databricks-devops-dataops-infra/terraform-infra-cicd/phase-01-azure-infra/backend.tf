# ==============================================================================
# Backend Configuration - Remote State in Azure Storage
# ==============================================================================
# State is stored in the storage account created by phase-00-bootstrap.
# Backend config values are passed via -backend-config in CI/CD.
# ==============================================================================
# Test triger

terraform {
  backend "azurerm" {
    key = "phase-01-azure-infra.tfstate"
  }
}
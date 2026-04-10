# ==============================================================================
# Backend Configuration - Remote State in Azure Storage
# ==============================================================================
# State is stored in the storage account created by phase-00-bootstrap.
# Backend config values are passed via -backend-config in CI/CD.
# ==============================================================================

terraform {
  backend "azurerm" {
    key = "phase-02-unity-catalog.tfstate"
  }
}

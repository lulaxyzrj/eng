terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.116"
    }
  }

  backend "azurerm" {
    key = "smoke-test.tfstate"
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true
}

resource "azurerm_resource_group" "smoke_test" {
  name     = "ubereats-smoke-test-rg"
  location = "eastus2"

  tags = {
    Purpose     = "CI/CD Smoke Test"
    DeleteAfter = "Immediately"
  }
}

output "result" {
  value = "Smoke test passed! RG: ${azurerm_resource_group.smoke_test.name}"
}
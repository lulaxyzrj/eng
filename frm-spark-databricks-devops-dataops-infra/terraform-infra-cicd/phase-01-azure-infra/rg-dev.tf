# ==============================================================================
# Resource Group: Development
# ==============================================================================
# Contains:
# - Databricks Workspace
# - VNet, Subnets, NSG (required for VNet injection)
# - ADLS Gen2 with medallion containers
# ==============================================================================

resource "azurerm_resource_group" "dev" {
  name     = "${local.dev_name}-rg"
  location = var.location
  tags     = local.dev_tags
}

# ==============================================================================
# Networking (required for Databricks VNet injection)
# ==============================================================================

resource "azurerm_virtual_network" "dev" {
  name                = "${local.dev_name}-vnet"
  location            = azurerm_resource_group.dev.location
  resource_group_name = azurerm_resource_group.dev.name
  address_space       = ["10.1.0.0/16"]
  tags                = local.dev_tags
}

resource "azurerm_network_security_group" "dev" {
  name                = "${local.dev_name}-nsg"
  location            = azurerm_resource_group.dev.location
  resource_group_name = azurerm_resource_group.dev.name
  tags                = local.dev_tags
}

resource "azurerm_subnet" "dev_public" {
  name                 = "${local.dev_name}-public-subnet"
  resource_group_name  = azurerm_resource_group.dev.name
  virtual_network_name = azurerm_virtual_network.dev.name
  address_prefixes     = ["10.1.1.0/24"]

  delegation {
    name = "databricks-delegation"
    service_delegation {
      name = "Microsoft.Databricks/workspaces"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action",
        "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action"
      ]
    }
  }
}

resource "azurerm_subnet" "dev_private" {
  name                 = "${local.dev_name}-private-subnet"
  resource_group_name  = azurerm_resource_group.dev.name
  virtual_network_name = azurerm_virtual_network.dev.name
  address_prefixes     = ["10.1.2.0/24"]

  delegation {
    name = "databricks-delegation"
    service_delegation {
      name = "Microsoft.Databricks/workspaces"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action",
        "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action"
      ]
    }
  }
}

resource "azurerm_subnet_network_security_group_association" "dev_public" {
  subnet_id                 = azurerm_subnet.dev_public.id
  network_security_group_id = azurerm_network_security_group.dev.id
}

resource "azurerm_subnet_network_security_group_association" "dev_private" {
  subnet_id                 = azurerm_subnet.dev_private.id
  network_security_group_id = azurerm_network_security_group.dev.id
}

# ==============================================================================
# Databricks Workspace
# ==============================================================================

resource "azurerm_databricks_workspace" "dev" {
  name                        = "${local.dev_name}-workspace"
  resource_group_name         = azurerm_resource_group.dev.name
  location                    = azurerm_resource_group.dev.location
  sku                         = var.databricks_sku
  managed_resource_group_name = "${local.dev_name}-databricks-managed-rg"
  tags                        = local.dev_tags

  custom_parameters {
    no_public_ip                                         = true
    virtual_network_id                                   = azurerm_virtual_network.dev.id
    public_subnet_name                                   = azurerm_subnet.dev_public.name
    private_subnet_name                                  = azurerm_subnet.dev_private.name
    public_subnet_network_security_group_association_id  = azurerm_subnet_network_security_group_association.dev_public.id
    private_subnet_network_security_group_association_id = azurerm_subnet_network_security_group_association.dev_private.id
  }

  # SAFETY LOCK:
  # Wait for the Account-Level Metastore to be created first.
  # This prevents Databricks from automatically provisioning a system-managed
  # metastore, which would cause "Metastore already exists" conflicts later.
  depends_on = [
    databricks_metastore.this,
    databricks_metastore_data_access.this
  ]
}

# ==============================================================================
# ADLS Gen2 Storage (Data Lake)
# ==============================================================================

resource "azurerm_storage_account" "dev" {
  name                     = "adls${var.prefix}dev${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.dev.name
  location                 = azurerm_resource_group.dev.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
  tags                     = local.dev_tags
}

# Medallion architecture containers
resource "azurerm_storage_container" "dev" {
  for_each              = toset(local.medallion_containers)
  name                  = each.value
  storage_account_name  = azurerm_storage_account.dev.name
  container_access_type = "private"
}

# ==============================================================================
# Role Assignment: Access Connector -> Dev Storage
# ==============================================================================

resource "azurerm_role_assignment" "unity_dev" {
  scope                = azurerm_storage_account.dev.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.unity.identity[0].principal_id
}

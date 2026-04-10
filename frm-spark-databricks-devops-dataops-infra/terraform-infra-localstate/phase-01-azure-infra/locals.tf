locals {
  # Naming convention
  governance_name = "${var.prefix}-governance"
  dev_name        = "${var.prefix}-dev"
  prod_name       = "${var.prefix}-prod"

  # Tags por ambiente
  governance_tags = merge(var.tags, {
    Environment = "Governance"
    Purpose     = "Unity Catalog Metastore"
  })

  dev_tags = merge(var.tags, {
    Environment = "Development"
  })

  prod_tags = merge(var.tags, {
    Environment = "Production"
  })

  # Containers para medallion architecture
  medallion_containers = ["landing", "bronze", "silver", "gold"]
}

# Sufixo aleatório para nomes únicos de storage account
resource "random_string" "suffix" {
  length  = 4
  special = false
  upper   = false
}

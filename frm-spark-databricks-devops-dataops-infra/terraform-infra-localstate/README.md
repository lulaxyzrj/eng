# Terraform Infrastructure - Databricks Unity Catalog on Azure

Infrastructure as Code for deploying Databricks with Unity Catalog on Azure.

## Architecture

### Phase 01: Azure Infrastructure

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RG: ubereats-governance                          │
│  ┌────────────────────┐  ┌─────────────────────────────────────┐   │
│  │ Access Connector   │  │ ADLS Gen2 (metastore)               │   │
│  │ (Managed Identity) │  │ Container: metastore                │   │
│  └────────────────────┘  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌───────────────────────────────────┐  ┌───────────────────────────────────┐
│        RG: ubereats-dev           │  │        RG: ubereats-prod          │
│  ┌─────────────────────────────┐  │  │  ┌─────────────────────────────┐  │
│  │ Databricks Workspace (Dev)  │  │  │  │ Databricks Workspace (Prod) │  │
│  └─────────────────────────────┘  │  │  └─────────────────────────────┘  │
│  ┌─────────────────────────────┐  │  │  ┌─────────────────────────────┐  │
│  │ ADLS Gen2                   │  │  │  │ ADLS Gen2                   │  │
│  │ Containers:                 │  │  │  │ Containers:                 │  │
│  │  - landing                  │  │  │  │  - landing                  │  │
│  │  - bronze                   │  │  │  │  - bronze                   │  │
│  │  - silver                   │  │  │  │  - silver                   │  │
│  │  - gold                     │  │  │  │  - gold                     │  │
│  └─────────────────────────────┘  │  │  └─────────────────────────────┘  │
│  ┌─────────────────────────────┐  │  │  ┌─────────────────────────────┐  │
│  │ VNet + Subnets + NSG        │  │  │  │ VNet + Subnets + NSG        │  │
│  └─────────────────────────────┘  │  │  └─────────────────────────────┘  │
└───────────────────────────────────┘  └───────────────────────────────────┘
```

### Phase 02: Unity Catalog Configuration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Unity Catalog Metastore                          │
│                                                                         │
│   ┌──────────────────────┐        ┌─────────────────────────────────┐   │
│   │  Storage Credential  │───────▶│  Access Connector (Managed ID)  │   │
│   └──────────┬───────────┘        └─────────────────────────────────┘   │
│              │                                                          │
│              ▼                                                          │
│   ┌──────────────────────┐        ┌─────────────────────────────────┐   │
│   │  External Locations  │───────▶│  ADLS Gen2 Containers           │   │
│   │                      │        │                                 │   │
│   │  • landing           │        │  • landing                      │   │
│   │  • bronze            │        │  • bronze                       │   │
│   │  • silver            │        │  • silver                       │   │
│   │  • gold              │        │  • gold                         │   │
│   └──────────────────────┘        └─────────────────────────────────┘   │
│                                                                         │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
                ┌─────────────────────────────┐
                │    Workspace Assignments    │
                │                             │
                │  • ubereats-dev             │
                │  • ubereats-prod            │
                └─────────────────────────────┘
```

## Folder Structure

```
terraform-infra/
├── phase-01-azure-infra/     # Azure: RGs, Workspaces, Storage, Networking
├── phase-02-unity-catalog/   # Databricks: Metastore, Credentials, Locations
├── scripts/                  # Deploy scripts
└── README.md
```

## Quick Start

### 1. Deploy Phase 01 (Azure Infrastructure)

```bash
# check if azure is logged in
az account list

# aways good to refresh the logging
az logout
az login

# check the tenant id
az account show --query tenantId -o tsv
```


```bash
cd terraform-infra-localstate/phase-01-azure-infra
cp terraform.tfvars.example terraform.tfvars
cd ..
# Edit terraform.tfvars if necessary

../scripts/01-deploy-azure-infra.sh
```

**Created Resources:**
- 3 Resource Groups (governance, dev, prod)
- 1 Access Connector (for Unity Catalog)
- 3 Storage Accounts (ADLS Gen2)
- 2 Databricks Workspaces (dev, prod)
- 2 VNets with subnets and NSGs

### 2. Deploy Phase 02 (Unity Catalog)

```bash
# The script automatically reads values from Phase 01!
# You only need to provide the Databricks Account ID

./scripts/02-deploy-unity-catalog.sh
```

The script will:
1. Automatically read workspace URLs from Phase 01 state
2. Ask for `databricks_account_id` (get it from https://accounts.azuredatabricks.net)
3. Automatically generate `terraform.tfvars`
4. Execute `terraform apply`

**Created Resources:**
- 1 Metastore (regional)
- 1 Storage Credential
- 6 External Locations (dev/prod x bronze/silver/gold)
- Metastore assignments for the workspaces

> **Troubleshooting:** If you encounter errors during deployment (e.g., state inconsistencies, authentication issues), please refer to the [Common Errors & Troubleshooting Guide](../documents_utils/troubleshooting/troubleshooting-localstate.md).

### 3. Destroy everything (when no longer needed)

```bash
./scripts/99-destroy-all.sh
```

> **Note:** If you have generated data (tables) inside your schemas, Terraform might complain that it "cannot delete schema ... is not empty".
>
> Example: `Error: cannot delete schema: Schema 'ubereats_dev.bronze' is not empty.`
>
> **This is expected.** Terraform tries to protect you from deleting data. However, since the underlying Storage Accounts and Workspaces (Phase 01) are destroyed immediately after, the data is effectively gone anyway. You can ignore this error in this POC context.

## Variables

### Phase 01

| Variable | Description | Default |
|----------|-------------|---------|
| `location` | Azure region | `eastus2` |
| `prefix` | Resource prefix | `ubereats` |
| `databricks_sku` | Workspace SKU | `premium` |

### Phase 02

| Variable | Description | How to get |
|----------|-------------|------------|
| `databricks_account_id` | Account ID | Account Console (only manual value!) |
| `dev_workspace_url` | Dev workspace URL | Read from Phase 01 state by the script |
| `prod_workspace_url` | Prod workspace URL | Read from Phase 01 state by the script |

> **Note:** Most Phase 02 values are automatically read from Phase 01 state via `terraform_remote_state`. The deploy script generates `terraform.tfvars` automatically - you only need to provide the `databricks_account_id` and `Data-engineering user` if u want to assign permissions to it!

## How Access Works

For a detailed theoretical explanation of the security model, Managed Identities, and the flow from User to Storage, please refer to the **[Unity Catalog Access Architecture](../documents_utils/infra_knowlodge/unity_catalog_access_explained.md)** document.

In summary:
1.  **User** asks for data.
2.  **Unity Catalog** checks permissions.
3.  **Access Connector** (Managed Identity) authorizes the request against Azure Storage.
4.  **No direct keys** are ever exposed to the user.

## Secure Networking

Our infrastructure uses **VNet Injection** and **Secure Cluster Connectivity (No Public IP)** to ensure that compute nodes are not exposed to the internet.

However, you will notice that `pip install` still works! This is due to Azure's **Default Outbound Access**.

For a deep dive into why this works, why it's safe, and why it saves us money (vs. using a NAT Gateway), read the **[Secure Networking & Outbound Access](../documents_utils/infra_knowlodge/secure_networking_explained.md)** guide.

## Estimated Costs: POC vs Production

The following table compares the estimated costs for a Proof of Concept (POC) environment (like this one) versus a typical Production environment.

| Component | POC (Current Setup) | Production (Enterprise Scale) |
|-----------|---------------------|-------------------------------|
| **Databricks Compute** | **Low** (Covered by Free Credits*) | **$$$** (Pay-as-you-go / DBU usage) |
| **Storage (ADLS Gen2)** | **<$1/month** (minimal data, LRS) | **$$** (TB/PB scale, GRS/RA-GRS) |
| **Networking** | **~$0** (Basic VNet, no NAT Gateway) | **~$30+/month** (NAT Gateway, Firewall, Private Link) |
| **Public IPs** | **~$0** (Secure Cluster Connectivity) | **~$4/IP/month** (Load Balancers, Gateways) |
| **Total Estimated** | **<$10/month** (or Free w/ Credits) | **Starts at ~$100/month + Compute** |

> ***Note on Costs:** While not exactly zero, the costs for this POC are very low (typically under $10/month for active learning). If you are using a new Azure account, the **$200 Free Credit** is more than enough to run this entire lab for weeks. Just remember to **terminate your clusters** when not in use to avoid draining your credits!

## Conclusion

This infrastructure provides a solid foundation for a modern Data & AI platform on Azure. By separating resources into phases, we ensure a clean distinction between the underlying cloud infrastructure (Phase 01) and the logical data governance layer (Phase 02).

Enjoy building your Data Lakehouse!

## Detailed Resource Documentation

Want to understand exactly what resources are being created?
*   👉 **[Phase 01 Resources Explained](../documents_utils/used_resources/local-state-phase01.md)**
*   👉 **[Phase 02 Resources Explained](../documents_utils/used_resources/local-state-phase02.md)**
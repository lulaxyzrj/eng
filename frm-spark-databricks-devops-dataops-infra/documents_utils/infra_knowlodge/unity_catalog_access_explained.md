# Unity Catalog Access Architecture on Azure

This document details the theoretical and practical implementation of access control in our Databricks Unity Catalog setup on Azure.

## The Core Problem: Decoupling Access from Credentials

In legacy Databricks deployments (Hive Metastore), access to data in Azure Data Lake Storage (ADLS) often relied on:
1.  **Mount Points:** Mounting storage containers to the workspace using Access Keys or SAS tokens.
2.  **Direct Access:** Users needing direct read/write permissions on the underlying storage account.

This created security risks:
- **Credential Leaks:** Keys and tokens could be exposed in notebooks.
- **Lack of Granularity:** Once a container was mounted, it was often "all or nothing" access.
- **Identity Confusion:** It was hard to audit *who* accessed a file, as access often looked like it came from a generic service principal.

## The Unity Catalog Solution

Unity Catalog solves this by introducing an **Identity Federation** layer. The end user **never** interacts directly with Azure Storage credentials.

### The Access Flow

```text
+-----------------+        +-------------------------+
| Databricks User |------->| Unity Catalog Metastore |
+-----------------+        +-----------+-------------+
                                       |
                                       v
                               +-------+-------+
                               | Check GRANTS  |
                               +-------+-------+
                                       |
                       (Authorized?)   v
                    +------------------+------------------+
                    |          External Location          |
                    +------------------+------------------+
                                       |
                                       v
                    +------------------+------------------+
                    |        Storage Credential           |
                    +------------------+------------------+
                                       |
                                       v
                    +------------------+------------------+
                    | Access Connector (Managed Identity) |
                    +------------------+------------------+
                                       |
                  (RBAC: Storage Blob Data Contributor)
                                       |
                                       v
                    +------------------+------------------+
                    |      Azure Data Lake Gen2 (ADLS)    |
                    +-------------------------------------+
```

### Key Components

#### 1. The Access Connector for Azure Databricks
This is an Azure resource that wraps a **Managed Identity**.
- It is the *only* entity that actually holds permissions on the Storage Account.
- We assign the `Storage Blob Data Contributor` role to this Managed Identity on the ADLS Gen2 account.

#### 2. Storage Credential (Unity Catalog Object)
This is a logical object inside Databricks that represents the Azure Managed Identity.
- It says: "I know how to talk to this specific Azure Identity."
- Users do *not* have access to use this credential directly to read arbitrary data.

#### 3. External Location (Unity Catalog Object)
This combines a **Storage Path** (e.g., `abfss://silver@storage.dfs.core.windows.net/`) with a **Storage Credential**.
- It acts as a bridge.
- It defines *where* data lives and *how* to get there.

#### 4. Unity Catalog Permissions (Grants)
Permissions are applied at the logical level (Catalog, Schema, Table).
- When a user runs `SELECT * FROM silver.sales.orders`, Unity Catalog verifies if the user has `SELECT` permission on that table.
- If yes, Unity Catalog generates a temporary, short-lived token scoped *only* for that specific file access operation, using the underlying Managed Identity.

### The Strategic Role of the Access Connector

The **Access Connector for Azure Databricks** is not just a "dumb pipe"; it is the linchpin of the modern security architecture.

1.  **Synergy with Azure Managed Identities:**
    - It eliminates the need for Service Principals with client secrets that expire.
    - Azure handles the identity lifecycle automatically. There are no passwords to rotate or leak.

2.  **Decoupling Compute from Storage:**
    - The Databricks clusters (compute) do not have inherent permissions. They "borrow" the identity of the Access Connector only when authorized by Unity Catalog.
    - This creates a **Zero Trust** environment where the compute plane is untrusted by default.

3.  **Simplified Network Security:**
    - Because the Access Connector is a first-party Azure resource, it integrates natively with **Azure Private Link** and **Storage Firewalls**.
    - You can lock down your ADLS Gen2 storage to *only* accept traffic from trusted Azure services (like this connector) and specific VNets, completely blocking public internet access.

4.  **Cross-Workspace Governance:**
    - A single Unity Catalog Metastore can govern multiple workspaces (Dev, Staging, Prod).
    - The Access Connector allows the Metastore to broker access across these environments without replicating credentials or data.

## Why this is Secure

1.  **No Long-Lived Secrets:** No Access Keys or SAS tokens are stored in Databricks.
2.  **Principle of Least Privilege:** The user only needs permission on the *Table*. They don't need to know the storage account name, container, or have any Azure IAM role.
3.  **Centralized Governance:** Auditing happens at the Unity Catalog level. You can see exactly which user queried which table, regardless of where the data physically sits.

## Terraform Implementation

In our `phase-02-unity-catalog` Terraform code, we automate this linkage:

1.  **Azure Side (Phase 01):**
    - Create `azurerm_databricks_access_connector`.
    - Grant it `Storage Blob Data Contributor` on the Storage Account.

2.  **Databricks Side (Phase 02):**
    - Create `databricks_storage_credential` pointing to the Access Connector's ID.
    - Create `databricks_external_location` for each container (bronze, silver, gold) using that credential.
    - Assign `databricks_grants` to users/groups on these locations or the catalogs derived from them.

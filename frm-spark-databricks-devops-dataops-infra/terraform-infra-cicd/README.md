# Terraform Infrastructure - CI/CD Ready (Remote State)

This directory contains the production-grade Infrastructure as Code (IaC) setup for the UberEats Data Platform. Unlike the local state version, this setup uses **Azure Remote Backend** to store Terraform state, enabling collaboration and CI/CD pipeline integration.

**Reference:** This architecture follows best practices from the [Databricks Terraform Examples](https://github.com/databricks/terraform-databricks-examples/tree/main).

## Architecture Overview

The deployment is split into three distinct phases to handle dependencies and the "Chicken and Egg" problem of remote state.

### Phase 00: Bootstrap (The Foundation)
*   **Goal:** Create the "home" for our Terraform State.
*   **Resources:** Resource Group, Storage Account, Container (`tfstate`).
*   **State:** Local (migrated to remote immediately after creation).

```text
+------------------------------------------+
|  RG: ubereats-terraform-backend-rg       |
|                                          |
|  +------------------------------------+  |
|  | Storage Account (tfstate)          |  |
|  |                                    |  |
|  |  +------------------------------+  |  |
|  |  | Container: tfstate           |  |  |
|  |  |  - phase-01.tfstate          |  |  |
|  |  |  - phase-02.tfstate          |  |  |
|  |  +------------------------------+  |  |
|  +------------------------------------+  |
+------------------------------------------+
```

### Phase 01: Azure Infrastructure & Metastore
*   **Goal:** Deploy the physical cloud resources and the Global Metastore.
*   **State:** Stored remotely in Phase 00 storage.
*   **Resources:** Resource Groups, VNets, Databricks Workspaces, ADLS Gen2 Accounts, **Unity Catalog Metastore**.

### Phase 02: Unity Catalog Configuration
*   **Goal:** Configure the logical data governance layer.
*   **State:** Stored remotely in Phase 00 storage.
*   **Resources:** Metastore Assignment (Binding), Storage Credentials, External Locations, Grants.

> **Important:** The core architecture (VNets, Workspaces, Unity Catalog) is **99% identical** to the Local State version. We are deploying the exact same resources. The only difference is **HOW** they are deployed (via Service Principal instead of User) and **WHERE** the state is stored.
>
> **Note on Security:** The CI/CD version (`phase-02/security.tf`) includes extra configurations for **Entitlements** and **Token Permissions** that are often manual in local setups. This ensures the `data-engineers` group has the correct rights (Cluster Create, SQL Access, PAT generation) automatically provisioned.

## Key Differences: Local vs. CI/CD

Why do we need this complexity? Why not just use local state?

> **Read the detailed comparison here:**
> **[Local State vs. CI/CD Approach](../documents_utils/infra_knowlodge/local_vs_cicd_infra.md)**

In summary: **Pipelines cannot store local files.** To automate this with GitHub Actions or Azure DevOps, we **must** use a remote backend.

## CI/CD Pipelines (GitHub Actions)

We have pre-built workflows to automate the deployment of these phases.

> **Read the detailed guide here:**
> **[GitHub Actions Workflows Explained](../documents_utils/github_utils/github_workflows_explained.md)**

## Deployment Guides

We have prepared detailed step-by-step guides for deploying this infrastructure.

### 1. First Time Setup (Bootstrap)
If you are running this for the very first time, you must initialize the backend.
*   👉 **[Read the Bootstrap Guide](../documents_utils/deploy_utils/BOOTSTRAP-GUIDE.md)**

### 2. Standard Deployment (Phases 01 & 02)
Once the bootstrap is done, follow the standard deployment flow for the application infrastructure.
*   👉 **[Read the Deployment Guide](../documents_utils/deploy_utils/PHASE-01-02-GUIDE.md)**

## Folder Structure

```

├── .github/workflows/
│   ├── terraform-phase-01.yml    # Deploys Azure Infra
│   ├── terraform-phase-02.yml    # Deploys Unity Catalog
│   ├── terraform-destroy-99.yaml # Destroys All (Manual)
│   └── smoke-test.yml            # Validates Deployment
└── terraform-infra-cicd/
    ├── phase-00-bootstrap/   # Creates the TF Backend Storage
    ├── phase-01-azure-infra/ # Azure Resources (Remote State)
    ├── phase-02-unity-catalog/ # Databricks Config (Remote State)
    ├── smoke-test/           # Validation scripts
    └── README.md
```

## Prerequisites

*   All prerequisites from the root README apply.
*   **Critical:** You must have `Owner` rights on the subscription to create the initial Bootstrap resources and assign roles.

## Troubleshooting

Encountering state locks or "ghost resources" in CI/CD?
*   👉 **[Read the CI/CD Troubleshooting Guide](../documents_utils/troubleshooting/troubleshooting-cicd.md)**
    *   Learn how to use the `debug-phase02-state.yaml` pipeline to fix remote state issues.

## Detailed Resource Documentation

Want to understand exactly what resources are being created and how they differ from the local version?
*   👉 **[CI/CD Phase 01 Resources Explained](../documents_utils/used_resources/cicd-phase01.md)**
*   👉 **[CI/CD Phase 02 Resources Explained](../documents_utils/used_resources/cicd-phase02.md)**
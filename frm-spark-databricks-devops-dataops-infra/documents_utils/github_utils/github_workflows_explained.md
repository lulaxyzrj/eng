# GitHub Actions Workflows for Infrastructure

This folder contains the CI/CD pipelines (GitHub Actions) that automate the deployment of our infrastructure.

## Workflow Strategy

We use a **Phased Approach** to deployment, mirroring our Terraform structure. This ensures dependencies are respected (e.g., Azure Infra must exist before Unity Catalog can be configured).

### 1. `terraform-phase-01.yml` (Azure Infrastructure)
*   **Trigger:**
    *   **Pull Request:** Triggers `terraform plan` only (Validation).
    *   **Push to `main` (Merge):** Triggers `terraform apply` (Deployment).
    *   **Manual Dispatch:** Triggers full deployment.
*   **Action:** Deploys the physical Azure resources (Resource Groups, VNets, Databricks Workspaces, Storage).
*   **State:** Reads/Writes to `phase-01-azure-infra.tfstate` in the remote backend.

### 2. `terraform-phase-02.yml` (Unity Catalog)
*   **Trigger:**
    *   **Pull Request:** Triggers `terraform plan` only (Validation).
    *   **Workflow Run:** Automatically triggers `terraform apply` after Phase 01 completes successfully on `main`.
    *   **Manual Dispatch:** Triggers full deployment.
*   **Action:** Configures the logical data layer (Metastore, Catalogs, Grants).
*   **Dependency:** Reads outputs from Phase 01 state (Workspace URLs) to configure the provider.
*   **State:** Reads/Writes to `phase-02-unity-catalog.tfstate` in the remote backend.

### 3. `terraform-destroy-99.yml` (Cleanup)
*   **Trigger:** Manual Dispatch ONLY.
*   **Safety:** Requires typing "DESTROY" as a confirmation input.
*   **Action:** Destroys Phase 02 first, then Phase 01.
*   **Note:** Does **NOT** destroy Phase 00 (Bootstrap). The Terraform state storage is preserved to allow future deployments.

### 4. `smoke-test.yml` (Validation)
*   **Trigger:** After successful deployment of Phase 02.
*   **Action:** Runs a Python script to verify connectivity to the Databricks workspace and basic Unity Catalog functionality.

## Deployment Lifecycle

To ensure safety and stability, the deployment follows a strict lifecycle:

1.  **Pull Request (PR):**
    *   When code is pushed to a feature branch and a PR is opened against `main`, the workflow runs `terraform plan`.
    *   This validates the code and shows what changes *would* be applied.
    *   **No changes are applied** to the actual infrastructure at this stage.

2.  **Merge to Main:**
    *   Once the PR is approved and merged into `main`, the workflow runs `terraform apply`.
    *   This is the step that actually creates or updates the resources in Azure/Databricks.

## Secrets Required

These workflows rely on the following GitHub Secrets:

| Secret Name | Description |
| :--- | :--- |
| `ARM_CLIENT_ID` | Service Principal App ID |
| `ARM_CLIENT_SECRET` | Service Principal Password |
| `ARM_TENANT_ID` | Azure Tenant ID |
| `ARM_SUBSCRIPTION_ID` | Azure Subscription ID |
| `TF_BACKEND_SA` | Name of the Storage Account created in Phase 00 |
| `DATABRICKS_ACCOUNT_ID` | Databricks Account ID (for Unity Catalog) |



6.  **Manual:** Go to the "Actions" tab in GitHub -> Select the workflow -> Click "Run workflow".

## Manual / Fast-Track Workflows

> **ℹ️ Quality of Life (Optional):** This section describes **extra** workflows designed to improve the quality of life for students or solo developers. They are completely optional and intended to speed up the learning process by bypassing the strict PR/Merge requirements.

For students or developers working solo who want to iterate quickly without the full Pull Request lifecycle, we have provided alternative "Manual" workflows. These allow you to trigger Plans, Applies, and Destroys directly from the GitHub Actions UI.

These workflows are located in `documents_utils/github_utils/` and can be moved to `.github/workflows/` if you wish to use them.

### 1. `terraform-phase-01-manual.yml`
*   **Trigger:** Manual Dispatch.
*   **Input:** `confirmation` (Type 'APPLY' to deploy, otherwise it only runs Plan).
*   **Action:** Runs Terraform Plan and optionally Apply for Phase 01 (Azure Infra) in a single run.

### 2. `terraform-phase-02-manual.yml`
*   **Trigger:** Manual Dispatch.
*   **Input:** `confirmation` (Type 'APPLY' to deploy, otherwise it only runs Plan).
*   **Action:** Runs Terraform Plan and optionally Apply for Phase 02 (Unity Catalog). Automatically fetches Phase 01 outputs.

### 3. `destroy-phase-01-manual.yaml`
*   **Trigger:** Manual Dispatch.
*   **Input:** `confirmation` (Must type 'DESTROY').
*   **Action:** Destroys Phase 01 resources. Includes a workaround to unlock Metastore deletion if needed.

### 4. `destroy-pahse-02-manual.yaml`
*   **Trigger:** Manual Dispatch.
*   **Input:** `confirmation` (Must type 'DESTROY').
*   **Action:** Destroys Phase 02 resources. Fetches Phase 01 state to ensure the provider can connect to Databricks for cleanup.

---

## 💡 Recommendation

**We strongly recommend following the standard `terraform-phase-xx.yml` workflows (PR -> Plan, Merge -> Apply)** as this mirrors a real-world production environment with proper checks and balances.

However, if you are working alone and want to speed up your development loop (avoiding the need to create PRs and merge them for every change), you can use the **Manual Workflows** listed above. They provide a direct "ClickOps" way to control your infrastructure deployment from GitHub Actions.

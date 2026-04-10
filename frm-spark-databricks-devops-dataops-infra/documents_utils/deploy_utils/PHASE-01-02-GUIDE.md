# 🚀 Deployment Guide: Phases 01 & 02 (CI/CD)

This guide outlines the steps to configure the repository and execute the CI/CD pipelines for the Azure Infrastructure (Phase 01) and Unity Catalog (Phase 02).

**Prerequisite:** You must have already completed the **[Bootstrap Guide](BOOTSTRAP-GUIDE.md)** to create the remote state storage and Service Principal.

---

## 📋 Table of Contents
1. [Databricks Account Admin Setup](#1-databricks-account-admin-setup)
2. [GitHub Repository Configuration](#2-github-repository-configuration)
3. [Execution Flow (CI/CD)](#3-execution-flow-cicd)

---



## 1. Databricks Account Admin Setup

**Goal:** Authorize the CI/CD Service Principal to create the Unity Catalog Metastore.

1. Copy the `client_id` from the Phase 00 outputs.
2. Log in to the **Databricks Account Console**.
3. Navigate to **User Management → Service Principals**.
4. Click **Add service principal**.
5. Name: `ubereats-terraform-sp` (or similar).
6. UUID: Paste the `client_id` (Application ID).
7. **Grant the Account Admin role** to this Service Principal.

---

## 2. GitHub Repository Configuration

### A. Secrets (Credentials)
Add the terraform outputs as GitHub Actions secrets:

| Secret Name          | Value Source              | Purpose                    |
| -------------------- | ------------------------- | -------------------------- |
| `ARM_CLIENT_ID`      | Output `client_id`        | SPN Login                  |
| `ARM_CLIENT_SECRET`  | Output `client_secret`    | SPN Password               |
| `ARM_TENANT_ID`      | Output `tenant_id`        | Azure Tenant               |
| `ARM_SUBSCRIPTION_ID`| Output `subscription_id`  | Target Subscription        |
| `TF_BACKEND_SA`      | Output `storage_account_name` | Required for `smoke-test.yml` & SP|
| `DATABRICKS_ACCOUNT_ID` | Your Databricks Account ID | Unity Catalog Deployment   |

*Note: When copying `client_secret` from the terminal, ignore any trailing `%` (shell prompt).*

### B. Environments (Approval Gate)
1. Go to **Settings → Environments**.
2. Click **New environment** and name it `production` (must match the YAML).
3. Click **Configure environment** → enable **Required reviewers**.
4. Add yourself (or platform team) as reviewer.
5. Effect: pipeline pauses after Terraform Plan and waits for manual approval before Apply.

---

## 3. Execution Flow (CI/CD)

**Step 1: Smoke Test**
- GitHub Actions → run “Smoke Test - Validate CI/CD” on `main` or your branch.
- Success: Terraform Init ✅, Apply ✅, Destroy ✅.

**Step 2: Deploy Phase 01 (Azure Infra)**
- Create branch `feature/deploy-infra` and open PR to `main`.
- CI runs Terraform Plan in PR; review output.
- Merge PR; main pipeline runs Plan then pauses 🟡.
- Click **Review deployments → Approve**; Apply creates RGs, networking, workspaces.

**Step 3: Deploy Phase 02 (Unity Catalog)**
- Same flow as Phase 01; ensure Phase 01 is deployed so remote state exists.
- Open PR for Phase 02 code, merge, approve deployment.
- This phase reads `workspace_url` and `access_connector_id` from Phase 01 and creates the Metastore.

> **⚠️ Important Configuration:**
> Before running Phase 02, you **MUST** update the data engineering user email.
> 1. Open `terraform-infra-cicd/phase-02-unity-catalog/terraform.tfvars`.
> 2. Replace the placeholder email (`ubereats_data_engineer@...`) with **your own email address** (the one you use to log in to Databricks).
> 3. Commit and push this change.
>
> If you don't do this, you won't have access to the catalogs created!

Deployment Complete! 🚀

---

## 📚 Detailed Workflow Documentation

For a deep dive into how the GitHub Actions pipelines are structured, including triggers, secrets, and the deployment lifecycle (Plan vs Apply), please consult:

👉 **[GitHub Workflows Explained](../github_utils/github_workflows_explained.md)**

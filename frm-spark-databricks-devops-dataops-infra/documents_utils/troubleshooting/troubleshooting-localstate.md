# Common Errors and Troubleshooting

This guide covers common issues encountered during the deployment of the Terraform infrastructure, particularly due to state inconsistencies, network glitches, or authentication timeouts.

## 0. Prerequisites

Before starting, always ensure you have met the prerequisites listed in the **root project README**. Missing tools or permissions are the most common source of deployment failures.

## 1. Terraform State Inconsistencies

Sometimes, the Terraform state might get out of sync with the actual Azure resources, or a deployment might fail due to a connection bug, requiring a manual re-import of resources.

**Symptom:** Terraform complains that a resource already exists or fails to connect to the Databricks workspace during the apply phase.

**Fix:** Remove the problematic resource from the state (without deleting it from Azure) and re-import it.

### Example: Re-importing Databricks Workspace

```bash
# 1. Remove from state (does not delete from Azure)
terraform state rm azurerm_databricks_workspace.dev

# 2. Import again (Replace with your actual Resource ID)
# You can get the Resource ID from the Azure Portal -> Properties
terraform import azurerm_databricks_workspace.dev "/subscriptions/<YOUR_SUBSCRIPTION_ID>/resourceGroups/ubereats-dev-rg/providers/Microsoft.Databricks/workspaces/ubereats-dev-workspace"

# 3. Apply changes
terraform apply -auto-approve
```

## 2. Azure Authentication Issues

Tokens can expire, or the CLI might get confused between tenants. If you see "Unauthorized" or weird authentication errors:

**Fix:** Force a re-login.

```bash
# 1. Logout
az logout

# 2. Login again (Interactive)
az login

# 3. Verify current tenant
az account show --query tenantId -o tsv
```

## 3. Hard Reset (Local Infrastructure)

Local state files and caches can sometimes become corrupted or hold onto old configurations. If you are facing persistent inexplicable errors, it is often best to clean everything and start fresh.

**WARNING:** This will delete your local Terraform state. Ensure you are okay with losing your local state tracking (or that you can re-import/re-init).

```bash
# 1. Clean Databricks config
rm -f ~/.databrickscfg

# 2. Clean Terraform initialization and state files
rm -rf phase-01-azure-infra/.terraform
rm -rf phase-02-unity-catalog/.terraform

# 3. Remove generated variable files
rm -f phase-02-unity-catalog/terraform.tfvars

# 4. Remove state files
rm -f phase-01-azure-infra/terraform.tfstate*
rm -f phase-02-unity-catalog/terraform.tfstate*

# 5. Remove HCL lock files
rm -f phase-01-azure-infra/*.hcl
rm -f phase-02-unity-catalog/*.hcl
```

## 5. Error: "Reached the limit for metastores in region"

**Symptom:**
You see an error like: `Error: cannot create metastore: This account ... has reached the limit for metastores in region eastus2.`

**Cause:**
When you create a new Databricks Workspace, Databricks sometimes automatically creates a "Default Metastore" for you in the background. Since there can only be **one** Unity Catalog Metastore per region per account, our Terraform script fails when it tries to create a new one.

**Fix (For this Local/POC setup):**
1.  Go to the [Databricks Account Console](https://accounts.azuredatabricks.net/).
2.  Click on **Data** (or Catalog).
3.  Find the existing metastore in the target region (e.g., `eastus2`).
4.  **Delete it.** (Don't worry, this is a didactic step. In a real CI/CD production pipeline, we would import the existing one or handle this check automatically).
5.  Run `terraform apply` again.

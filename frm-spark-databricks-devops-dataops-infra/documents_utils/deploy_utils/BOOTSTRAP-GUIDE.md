# Phase 00: Bootstrap

## Why Does This Phase Exist?

This phase solves the **"chicken-egg" problem** of Terraform remote state:
```
┌─────────────────────────────────────────────────────────────┐
│  To use remote backend → Need Storage Account               │
│  To create Storage Account → Need Terraform                 │
│  To run Terraform with remote state → Need Storage Account  │
│                                                             │
│  🐔 → 🥚 → 🐔 → 🥚 → ???                                    │
└─────────────────────────────────────────────────────────────┘
```

**Solution:** Bootstrap runs with LOCAL state and creates the infrastructure 
that all other phases will use for REMOTE state.
```
┌─────────────────────────┐     ┌─────────────────────────┐
│  phase-00-bootstrap     │     │  phase-01, phase-02...  │
│  ───────────────────    │     │  ───────────────────    │
│  State: LOCAL           │────▶│  State: REMOTE          │
│  Creates: Storage + SP  │     │  Uses: Storage from     │
│                         │     │        bootstrap        │
└─────────────────────────┘     └─────────────────────────┘
```

## What This Phase Creates

| Resource | Name | Purpose |
|----------|------|---------|
| Resource Group | `{prefix}-tfstate-rg` | Container for state resources |
| Storage Account | `{prefix}tfstate{suffix}` | Terraform state storage |
| Storage Container | `tfstate` | Blob container for state files |
| App Registration | `{prefix}-terraform-sp` | Service Principal for CI/CD |
| Role Assignment | Contributor | SP access to subscription |
| Role Assignment | Storage Blob Data Contributor | SP access to state storage |
| Role Assignment | User Access Administrator | SP can create role assignments |

## Prerequisites

- Azure CLI installed and logged in (`az login`)
- Contributor role on the Azure subscription
- Permissions to create App Registrations in Entra ID

## Usage

### 1. Initialize and Apply
```bash
cd terraform-infra-cicd/phase-00-bootstrap
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars if needed

terraform init
terraform plan
terraform apply -auto-approve
```

### 2. Critical Access Fix: Control Plane vs. Data Plane

**Goal:** Enable your **Infra User** (Human) to validate the storage using `test-bootstrap.sh`.

#### ⚠️ The "Owner" Trap
Even if you are an **Owner** of the Subscription, you might get a `403 Forbidden` when trying to list/upload blobs via CLI using your login.

* **Control Plane:** As Owner, you can manage the *Storage Account* resource (create, delete, rotate keys).
* **Data Plane:** To read/write the *actual data files* (tfstate) via Azure AD login, you explicitly need the **"Storage Blob Data Contributor"** role.

#### Action Required
1.  Go to the **Azure Portal** -> Resource Group (`ubereats-tfstate-rg`).
2.  Select the Storage Account (`ubereatstfstate...`).
3.  Go to **Access Control (IAM)** -> **Add Role Assignment**.
4.  Role: **Storage Blob Data Contributor**.
5.  Assignee: **Your Infra User** (the email you used for `az login`).
6.  *Wait 1-2 minutes for propagation.*

> **Note:** Assigning this role to a human user is primarily for **didactic purposes** in this course. It allows you to run the validation script and confirm everything is working, ensuring your "sanity" before moving to CI/CD. In a strict production environment, only the Service Principal (Pipeline) would typically hold this data-plane permission.

### 3. Validate the Resources
```bash
chmod +x test-bootstrap.sh
./test-bootstrap.sh
```

### 4. Save Outputs for GitHub Secrets
```bash
# View summary of what to configure
terraform output github_secrets_summary

# Get the sensitive client_secret
terraform output -raw client_secret
```

### 5. Manual Steps Required

After Terraform creates the resources:

**A) Add Service Principal as Databricks Account Admin:**
   - Go to https://accounts.azuredatabricks.net
   - User Management → Service Principals → Add
   - Use the `client_id` from outputs
   - Grant "Account Admin" role

**B) Configure GitHub Secrets:**

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

| Secret Name | Value (from outputs) |
|-------------|---------------------|
| `ARM_CLIENT_ID` | `client_id` |
| `ARM_CLIENT_SECRET` | `client_secret` |
| `ARM_TENANT_ID` | `tenant_id` |
| `ARM_SUBSCRIPTION_ID` | `subscription_id` |
| `DATABRICKS_ACCOUNT_ID` | Your Databricks Account ID |

**C) Configure Federated Credentials (Optional - for OIDC):**
   - Go to Entra ID → App Registrations → Select the SP
   - Certificates & secrets → Federated credentials → Add
   - Select "GitHub Actions deploying Azure resources"
   - Configure with your repo details

## State Management

### Why Local State for Bootstrap?

The bootstrap uses **local state intentionally** because it creates the very 
Storage Account that will store remote state for other phases. There's no way 
around this - something has to create the backend storage first.

### How to Protect the Local State

The `terraform.tfstate` file contains **sensitive information** including the 
Service Principal client_secret. You MUST:

| Do | Don't |
|----|-------|
| ✅ Store in encrypted location | ❌ Commit to git |
| ✅ Restrict access (only admins) | ❌ Share via email/Slack |
| ✅ Backup securely | ❌ Leave on shared drives |
| ✅ Consider Azure Key Vault | ❌ Delete without backup |

**Recommended:** After bootstrap is complete, store `terraform.tfstate` in a 
secure location (encrypted drive, vault) and keep only for disaster recovery.

### What If I Lose the Bootstrap State?

If you lose the state file but resources still exist in Azure:

1. **Import resources** back into Terraform state
2. Or **manage manually** via Azure Portal/CLI
3. The other phases (01, 02) are NOT affected - they have their own remote state

## Outputs Reference

| Output | Description | Sensitive |
|--------|-------------|-----------|
| `resource_group_name` | Name of the tfstate resource group | No |
| `storage_account_name` | Name of the storage account | No |
| `container_name` | Name of the blob container | No |
| `client_id` | Service Principal Application ID | No |
| `client_secret` | Service Principal Secret | **Yes** |
| `tenant_id` | Azure Tenant ID | No |
| `subscription_id` | Azure Subscription ID | No |
| `backend_config` | Ready-to-copy backend block | No |
| `github_secrets_summary` | Instructions for GitHub setup | No |

## ⚠️ DANGER: Destroying Bootstrap
```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  DESTROYING BOOTSTRAP = DESTROYING EVERYTHING  ⚠️       │
└─────────────────────────────────────────────────────────────┘
```

If you run `terraform destroy` on bootstrap:

- ❌ **Storage Account deleted** → All Terraform states from phase-01 and phase-02 are GONE
- ❌ **Service Principal deleted** → CI/CD pipelines stop working
- ❌ **No rollback** → Azure resources still exist but Terraform can't manage them
- 💀 **Result:** Complete loss of infrastructure control

### When Would You Destroy Bootstrap?

Only in these scenarios:

1. **Decommissioning entire project** - You're deleting ALL infrastructure
2. **Starting completely fresh** - New subscription, new everything
3. **Never** during normal operations

### Safe Destruction Order (if truly needed)
```bash
# 1. FIRST: Destroy phases that depend on bootstrap
cd ../phase-02-unity-catalog
terraform destroy

cd ../phase-01-azure-infra
terraform destroy

# 2. LAST: Only after everything else is gone
cd ../phase-00-bootstrap
terraform destroy
```

## Remove state files

```bash
rm -rf phase-00-bootstrap/.terraform
rm -f phase-00-bootstrap/terraform.tfstate*
rm -f phase-00-bootstrap/.terraform.lock.hcl
```


## Troubleshooting

### "Storage account name already exists"

Storage account names are globally unique. Change the `prefix` or wait for 
the random suffix to generate a different name.

### "Insufficient privileges to complete the operation"

Your Azure account needs:
- Contributor role on subscription
- Permissions to create App Registrations in Entra ID

### "Cannot create service principal"

Make sure you're logged in with an account that can create App Registrations:
```bash
az login
az account show
```
#!/bin/bash
# ==============================================================================
# 02-deploy-unity-catalog.sh - Deploy Phase 02 (Unity Catalog)
# ==============================================================================
# This script:
# 1. Reads workspace URLs automatically from Phase 01 state
# 2. Prompts for Databricks Account ID
# 3. Prompts for group members (optional)
# 4. Generates terraform.tfvars automatically
# 5. Deploys Unity Catalog
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PHASE_01_DIR="$ROOT_DIR/phase-01-azure-infra"
PHASE_02_DIR="$ROOT_DIR/phase-02-unity-catalog"

echo "============================================================="
echo "  Phase 02: Deploying Unity Catalog"
echo "============================================================="
echo ""

# ------------------------------------------------------------------------------
# Check Phase 01 was completed
# ------------------------------------------------------------------------------
if [ ! -f "$PHASE_01_DIR/terraform.tfstate" ]; then
    echo "❌ Error: Phase 01 does not appear to be completed."
    echo "   Please run 01-deploy-azure-infra.sh first."
    exit 1
fi

echo "✅ Phase 01 state found. Reading outputs..."
echo ""

# ------------------------------------------------------------------------------
# Extract values from Phase 01 state
# ------------------------------------------------------------------------------
cd "$PHASE_01_DIR"

DEV_WORKSPACE_URL=$(terraform output -raw dev_workspace_url 2>/dev/null || echo "")
PROD_WORKSPACE_URL=$(terraform output -raw prod_workspace_url 2>/dev/null || echo "")

if [ -z "$DEV_WORKSPACE_URL" ] || [ -z "$PROD_WORKSPACE_URL" ]; then
    echo "❌ Error: Could not read workspace URLs from Phase 01."
    echo "   Make sure Phase 01 completed successfully."
    exit 1
fi

echo "🔗 Dev Workspace:  $DEV_WORKSPACE_URL"
echo "🔗 Prod Workspace: $PROD_WORKSPACE_URL"
echo ""

# ------------------------------------------------------------------------------
# Check/Create terraform.tfvars
# ------------------------------------------------------------------------------
cd "$PHASE_02_DIR"

if [ -f "terraform.tfvars" ]; then
    echo "✅ terraform.tfvars exists."
    
    # Check if it has databricks_account_id
    if grep -q "databricks_account_id" terraform.tfvars; then
        ACCOUNT_ID=$(grep "databricks_account_id" terraform.tfvars | sed 's/.*"\(.*\)".*/\1/')
        echo "   Using Databricks Account ID: $ACCOUNT_ID"
    else
        echo "⚠️  databricks_account_id not found in terraform.tfvars"
        read -p "Enter your Databricks Account ID: " ACCOUNT_ID
        echo "" >> terraform.tfvars
        echo "databricks_account_id = \"$ACCOUNT_ID\"" >> terraform.tfvars
    fi
else
    echo "📝 Creating terraform.tfvars..."
    echo ""
    echo "============================================================="
    echo "  DATABRICKS ACCOUNT ID"
    echo "============================================================="
    echo ""
    echo "Get this from: https://accounts.azuredatabricks.net"
    echo "Click your email (top right) → Account Settings → Account ID"
    echo ""
    echo "Example: 00000000-0000-0000-0000-000000000000"
    echo ""
    read -p "Enter your Databricks Account ID: " ACCOUNT_ID
    
    # Validate format
    if ! [[ "$ACCOUNT_ID" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
        echo "❌ Invalid format. Must be a UUID like: 00000000-0000-0000-0000-000000000000"
        exit 1
    fi
    
    # ------------------------------------------------------------------------------
    # Ask for group members (optional)
    # ------------------------------------------------------------------------------
    echo ""
    echo "============================================================="
    echo "  GROUP MEMBERS (Optional)"
    echo "============================================================="
    echo ""
    echo "Add user emails to data-engineers group."
    echo "These users get:"
    echo "  • Full access to dev catalog (ubereats_dev)"
    echo "  • Read-only access to prod catalog (ubereats_prod)"
    echo ""
    echo "For multiple users, separate with commas."
    echo "Press Enter to skip (you can add later via terraform.tfvars)"
    echo ""
    echo "Example: user1@domain.com,user2@domain.com"
    echo ""
    read -p "Enter emails (or press Enter to skip): " MEMBERS_INPUT
    
    # Format members for terraform
    if [ -n "$MEMBERS_INPUT" ]; then
        # Remove spaces around commas, then format as terraform list
        MEMBERS_CLEAN=$(echo "$MEMBERS_INPUT" | sed 's/ *, */,/g')
        MEMBERS_FORMATTED=$(echo "$MEMBERS_CLEAN" | sed 's/,/",\n  "/g')
        MEMBERS_BLOCK="data_engineers_members = [
  \"$MEMBERS_FORMATTED\"
]"
    else
        MEMBERS_BLOCK="data_engineers_members = []"
    fi
    
    # Generate terraform.tfvars
    cat > terraform.tfvars <<EOF
# ==============================================================================
# Phase 02 - Unity Catalog Variables
# ==============================================================================
# Generated automatically by 02-deploy-unity-catalog.sh
# ==============================================================================

databricks_account_id = "$ACCOUNT_ID"

dev_workspace_url  = "$DEV_WORKSPACE_URL"
prod_workspace_url = "$PROD_WORKSPACE_URL"

# ==============================================================================
# Group Members
# ==============================================================================
# Users in data-engineers group get:
#   - Full access to ubereats_dev catalog
#   - Read-only access to ubereats_prod catalog
#
# To add more users later, edit this file and run: terraform apply
# ==============================================================================

$MEMBERS_BLOCK
EOF

    echo ""
    echo "✅ terraform.tfvars created successfully!"
fi

echo ""

# ------------------------------------------------------------------------------
# Terraform Init
# ------------------------------------------------------------------------------
echo ">>> Initializing Terraform..."
terraform init

# ------------------------------------------------------------------------------
# Terraform Plan
# ------------------------------------------------------------------------------
echo ""
echo ">>> Planning Unity Catalog setup..."
terraform plan -out=tfplan

# ------------------------------------------------------------------------------
# Confirm
# ------------------------------------------------------------------------------
echo ""
echo "============================================================="
echo "Review the plan above."
echo "============================================================="
read -p "Do you want to apply this plan? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    rm -f tfplan
    exit 0
fi

# ------------------------------------------------------------------------------
# Terraform Apply
# ------------------------------------------------------------------------------
echo ""
echo ">>> Applying Unity Catalog configuration..."
terraform apply tfplan
rm -f tfplan

# ------------------------------------------------------------------------------
# Show Outputs
# ------------------------------------------------------------------------------
echo ""
echo "============================================================="
echo "  ✅ Phase 02 Complete!"
echo "============================================================="
echo ""
terraform output

echo ""
echo "============================================================="
echo "Unity Catalog configured successfully!"
echo ""
echo "Created:"
echo "  • Metastore (shared across workspaces)"
echo "  • Storage Credential (via Access Connector)"
echo "  • External Locations (landing/bronze/silver/gold x dev/prod)"
echo "  • Catalogs: ubereats_dev, ubereats_prod"
echo "  • Schemas: bronze, silver, gold (in each catalog)"
echo "  • Group: data-engineers"
echo ""
echo "Next steps:"
echo "  1. Open Dev workspace: $DEV_WORKSPACE_URL"
echo "  2. Go to Catalog Explorer - verify catalogs and schemas"
echo "  3. To add/remove group members:"
echo "     Edit phase-02-unity-catalog/terraform.tfvars"
echo "     Run: cd phase-02-unity-catalog && terraform apply"
echo "  4. Test access:"
echo "     SELECT current_user();"
echo "     SHOW CATALOGS;"
echo "============================================================="
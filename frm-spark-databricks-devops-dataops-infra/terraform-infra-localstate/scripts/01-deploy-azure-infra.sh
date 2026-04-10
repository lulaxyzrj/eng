#!/bin/bash
# ==============================================================================
# 01-deploy-azure-infra.sh - Deploy Phase 01 (Azure Infrastructure)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PHASE_01_DIR="$ROOT_DIR/phase-01-azure-infra"

echo "============================================================="
echo "  Phase 01: Deploying Azure Infrastructure"
echo "============================================================="
echo ""

# ------------------------------------------------------------------------------
# Check terraform.tfvars exists
# ------------------------------------------------------------------------------
if [ ! -f "$PHASE_01_DIR/terraform.tfvars" ]; then
    echo "Error: terraform.tfvars not found in phase-01-azure-infra/"
    echo ""
    echo "Please create it:"
    echo "  cd $PHASE_01_DIR"
    echo "  cp terraform.tfvars.example terraform.tfvars"
    echo "  # Edit if needed"
    exit 1
fi

cd "$PHASE_01_DIR"

# ------------------------------------------------------------------------------
# Terraform Init
# ------------------------------------------------------------------------------
echo ">>> Initializing Terraform..."
terraform init

# ------------------------------------------------------------------------------
# Terraform Plan
# ------------------------------------------------------------------------------
echo ""
echo ">>> Planning infrastructure..."
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
echo ">>> Applying infrastructure..."
terraform apply tfplan
rm -f tfplan

# ------------------------------------------------------------------------------
# Show Outputs
# ------------------------------------------------------------------------------
echo ""
echo "============================================================="
echo "  Phase 01 Complete!"
echo "============================================================="
echo ""
terraform output

# ------------------------------------------------------------------------------
# Export outputs for Phase 02
# ------------------------------------------------------------------------------
echo ""
echo ">>> Exporting outputs for Phase 02..."

OUTPUT_FILE="$ROOT_DIR/phase-02-unity-catalog/phase01-outputs.json"
terraform output -json > "$OUTPUT_FILE"

echo "Outputs saved to: $OUTPUT_FILE"
echo ""
echo "============================================================="
echo "Next steps:"
echo "  1. Run: ../scripts/02-deploy-unity-catalog.sh"
echo "     (The script will automatically generate terraform.tfvars for you)"
echo ""
echo "  [OPTIONAL] If you want to customize settings manually:"
echo "  1. cd ../phase-02-unity-catalog"
echo "  2. cp terraform.tfvars.example terraform.tfvars"
echo "  3. Edit terraform.tfvars"
echo "  4. Run: ../scripts/02-deploy-unity-catalog.sh"
echo "============================================================="

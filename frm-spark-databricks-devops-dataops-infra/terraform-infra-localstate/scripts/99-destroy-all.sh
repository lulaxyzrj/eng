#!/bin/bash
# ==============================================================================
# 99-destroy-all.sh - Destroy all resources (DANGEROUS!)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}=============================================================${NC}"
echo -e "${RED}  WARNING: This will DESTROY all infrastructure!${NC}"
echo -e "${RED}=============================================================${NC}"
echo ""
echo "This will destroy:"
echo "  - Unity Catalog (metastore, credentials, locations)"
echo "  - All Databricks Workspaces"
echo "  - All Storage Accounts (DATA WILL BE LOST)"
echo "  - All Resource Groups"
echo ""
echo -e "${YELLOW}This action is IRREVERSIBLE!${NC}"
echo ""

read -p "Type 'DESTROY' to confirm: " CONFIRM

if [ "$CONFIRM" != "DESTROY" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo ">>> Starting destruction..."

# ------------------------------------------------------------------------------
# Destroy Phase 02 first (Unity Catalog)
# ------------------------------------------------------------------------------
if [ -f "$ROOT_DIR/phase-02-unity-catalog/terraform.tfstate" ]; then
    echo ""
    echo ">>> Destroying Phase 02 (Unity Catalog)..."
    cd "$ROOT_DIR/phase-02-unity-catalog"
    terraform destroy -auto-approve || true
fi

# ------------------------------------------------------------------------------
# Destroy Phase 01 (Azure Infrastructure)
# ------------------------------------------------------------------------------
if [ -f "$ROOT_DIR/phase-01-azure-infra/terraform.tfstate" ]; then
    echo ""
    echo ">>> Destroying Phase 01 (Azure Infrastructure)..."
    cd "$ROOT_DIR/phase-01-azure-infra"
    terraform destroy -auto-approve
fi

# ------------------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------------------
echo ""
echo ">>> Cleaning up state files..."
rm -f "$ROOT_DIR/phase-01-azure-infra/terraform.tfstate"*
rm -f "$ROOT_DIR/phase-01-azure-infra/tfplan"
rm -f "$ROOT_DIR/phase-01-azure-infra/.terraform.lock.hcl"
rm -rf "$ROOT_DIR/phase-01-azure-infra/.terraform"

rm -f "$ROOT_DIR/phase-02-unity-catalog/terraform.tfstate"*
rm -f "$ROOT_DIR/phase-02-unity-catalog/tfplan"
rm -f "$ROOT_DIR/phase-02-unity-catalog/phase01-outputs.json"
rm -f "$ROOT_DIR/phase-02-unity-catalog/.terraform.lock.hcl"
rm -rf "$ROOT_DIR/phase-02-unity-catalog/.terraform"

echo ""
echo "============================================================="
echo "  All resources destroyed."
echo "============================================================="

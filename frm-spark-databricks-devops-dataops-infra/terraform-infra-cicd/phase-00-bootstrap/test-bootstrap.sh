#!/bin/bash
# ==============================================================================
# test-bootstrap.sh - Validate bootstrap resources
# ==============================================================================
# Run this after terraform apply to verify everything is working
# ==============================================================================

set -e

echo "============================================================="
echo "  Testing Bootstrap Resources"
echo "============================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# ------------------------------------------------------------------------------
# Get values from Terraform outputs
# ------------------------------------------------------------------------------
echo ">>> Reading Terraform outputs..."

RG_NAME=$(terraform output -raw resource_group_name 2>/dev/null || echo "")
SA_NAME=$(terraform output -raw storage_account_name 2>/dev/null || echo "")
CONTAINER_NAME=$(terraform output -raw container_name 2>/dev/null || echo "")
CLIENT_ID=$(terraform output -raw client_id 2>/dev/null || echo "")
TENANT_ID=$(terraform output -raw tenant_id 2>/dev/null || echo "")
SUBSCRIPTION_ID=$(terraform output -raw subscription_id 2>/dev/null || echo "")

if [ -z "$RG_NAME" ] || [ -z "$SA_NAME" ]; then
    echo -e "${RED}Error: Could not read Terraform outputs.${NC}"
    echo "Make sure you've run 'terraform apply' first."
    exit 1
fi

echo "  Resource Group:    $RG_NAME"
echo "  Storage Account:   $SA_NAME"
echo "  Container:         $CONTAINER_NAME"
echo "  Client ID:         $CLIENT_ID"
echo ""

# ------------------------------------------------------------------------------
# Test 1: Resource Group exists
# ------------------------------------------------------------------------------
echo -n "Testing Resource Group exists... "
if az group show --name "$RG_NAME" &>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    ERRORS=$((ERRORS + 1))
fi

# ------------------------------------------------------------------------------
# Test 2: Storage Account exists
# ------------------------------------------------------------------------------
echo -n "Testing Storage Account exists... "
if az storage account show --name "$SA_NAME" --resource-group "$RG_NAME" &>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    ERRORS=$((ERRORS + 1))
fi

# ------------------------------------------------------------------------------
# Test 3: Container exists
# ------------------------------------------------------------------------------
echo -n "Testing Container exists... "
if az storage container show --name "$CONTAINER_NAME" --account-name "$SA_NAME" --auth-mode login &>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    ERRORS=$((ERRORS + 1))
fi

# ------------------------------------------------------------------------------
# Test 4: Service Principal exists
# ------------------------------------------------------------------------------
echo -n "Testing Service Principal exists... "
if az ad sp show --id "$CLIENT_ID" &>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    ERRORS=$((ERRORS + 1))
fi

# ------------------------------------------------------------------------------
# Test 5: Write test blob to container
# ------------------------------------------------------------------------------
echo -n "Testing write access to container... "
TEST_FILE=$(mktemp)
echo "bootstrap-test-$(date +%s)" > "$TEST_FILE"

if az storage blob upload \
    --account-name "$SA_NAME" \
    --container-name "$CONTAINER_NAME" \
    --name "test-bootstrap.txt" \
    --file "$TEST_FILE" \
    --auth-mode login \
    --overwrite &>/dev/null; then
    echo -e "${GREEN}OK${NC}"
    
    # Cleanup test blob
    az storage blob delete \
        --account-name "$SA_NAME" \
        --container-name "$CONTAINER_NAME" \
        --name "test-bootstrap.txt" \
        --auth-mode login &>/dev/null || true
else
    echo -e "${RED}FAILED${NC}"
    ERRORS=$((ERRORS + 1))
fi

rm -f "$TEST_FILE"

# ------------------------------------------------------------------------------
# Test 6: Service Principal can authenticate (optional)
# ------------------------------------------------------------------------------
echo -n "Testing SP role assignments... "
ROLE_COUNT=$(az role assignment list --assignee "$CLIENT_ID" --query "length(@)" -o tsv 2>/dev/null || echo "0")
if [ "$ROLE_COUNT" -ge 2 ]; then
    echo -e "${GREEN}OK${NC} ($ROLE_COUNT roles assigned)"
else
    echo -e "${YELLOW}WARNING${NC} (only $ROLE_COUNT roles found, expected >= 2)"
fi

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo ""
echo "============================================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Add Service Principal as Databricks Account Admin"
    echo "     - Go to https://accounts.azuredatabricks.net"
    echo "     - User Management → Service Principals → Add"
    echo "     - Application ID: $CLIENT_ID"
    echo ""
    echo "  2. Configure GitHub Secrets"
    echo "     Run: terraform output github_secrets_summary"
    echo ""
    echo "  3. Get the client_secret for GitHub"
    echo "     Run: terraform output -raw client_secret"
else
    echo -e "${RED}$ERRORS test(s) failed.${NC}"
    echo "Please check the errors above and fix before proceeding."
    exit 1
fi
echo "============================================================="

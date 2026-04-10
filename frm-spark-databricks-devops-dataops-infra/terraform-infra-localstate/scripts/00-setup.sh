#!/bin/bash
# ==============================================================================
# 00-setup.sh - Verify prerequisites before deployment
# ==============================================================================

set -e

echo "============================================================="
echo "  Verifying Prerequisites"
echo "============================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# ------------------------------------------------------------------------------
# Check Terraform
# ------------------------------------------------------------------------------
echo -n "Checking Terraform... "
if command -v terraform &> /dev/null; then
    TF_VERSION=$(terraform --version | head -n1)
    echo -e "${GREEN}OK${NC} ($TF_VERSION)"
else
    echo -e "${RED}NOT FOUND${NC}"
    echo "  Install from: https://www.terraform.io/downloads"
    ERRORS=$((ERRORS + 1))
fi

# ------------------------------------------------------------------------------
# Check Azure CLI
# ------------------------------------------------------------------------------
echo -n "Checking Azure CLI... "
if command -v az &> /dev/null; then
    AZ_VERSION=$(az --version | head -n1)
    echo -e "${GREEN}OK${NC} ($AZ_VERSION)"
else
    echo -e "${RED}NOT FOUND${NC}"
    echo "  Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    ERRORS=$((ERRORS + 1))
fi

# ------------------------------------------------------------------------------
# Check Azure Login
# ------------------------------------------------------------------------------
echo -n "Checking Azure login status... "
if az account show &> /dev/null; then
    ACCOUNT=$(az account show --query name -o tsv)
    echo -e "${GREEN}OK${NC} (Logged in)"
else
    echo -e "${RED}NOT LOGGED IN${NC}"
    echo "  Run: az login"
    ERRORS=$((ERRORS + 1))
fi

# ------------------------------------------------------------------------------
# Check Subscription
# ------------------------------------------------------------------------------
echo -n "Checking Azure subscription... "
if az account show &> /dev/null; then
    SUB_NAME=$(az account show --query name -o tsv)
    SUB_ID=$(az account show --query id -o tsv)
    echo -e "${GREEN}OK${NC}"
    echo "  Subscription: $SUB_NAME"
    echo "  ID: $SUB_ID"
else
    echo -e "${RED}NO SUBSCRIPTION${NC}"
    ERRORS=$((ERRORS + 1))
fi

# ------------------------------------------------------------------------------
# Check User Permissions (basic check)
# ------------------------------------------------------------------------------
echo -n "Checking user permissions... "
USER_TYPE=$(az account show --query user.type -o tsv)
USER_NAME=$(az account show --query user.name -o tsv)
echo -e "${GREEN}OK${NC}"
echo "  User: $USER_NAME"
echo "  Type: $USER_TYPE"
echo -e "  ${YELLOW}Note: Ensure you have Contributor role on the subscription${NC}"

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo ""
echo "============================================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All prerequisites met!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. cd phase-01-azure-infra"
    echo "  2. cp terraform.tfvars.example terraform.tfvars"
    echo "  3. Edit terraform.tfvars if needed"
    echo "  4. Run: ../scripts/01-deploy-azure-infra.sh"
else
    echo -e "${RED}Found $ERRORS error(s). Please fix before proceeding.${NC}"
    exit 1
fi
echo "============================================================="

# ==============================================================================
# Phase 02 - Unity Catalog Variables
# ==============================================================================
# Most variables are passed via TF_VAR_* environment variables in the workflow.
# Only non-sensitive configuration that doesn't come from phase-01 goes here.
# ==============================================================================

# ------------------------------------------------------------------------------
# Security - Group Members
# ------------------------------------------------------------------------------
# Users in data-engineers group get:
#   - Full access to ubereats_dev catalog
#   - Read-only access to ubereats_prod catalog
#
# To add more users, edit this list and push to trigger the pipeline.
# ------------------------------------------------------------------------------

data_engineers_members = [
  "ubereats_data_engineer@gabrielpoc2025outlook.onmicrosoft.com"
]

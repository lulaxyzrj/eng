# Bootstrap Guide: Local IDE and Databricks CLI Setup

This guide walks you through setting up your local development environment for working with Databricks Asset Bundles.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Access to an Azure Databricks workspace (Admin or User role)
- [ ] Ability to create Personal Access Tokens (PAT)
- [ ] Python 3.11 (serverless) or 3.12 (classic clusters) installed
- [ ] VS Code installed

---

## 1. Access and Token Configuration

### Step 1.1: Workspace Access

Ensure your user (or infra user) has been added to the Databricks workspace. For CI/CD, you'll also need a Service Principal.

### Step 1.2: Generate Personal Access Token

1. Log into your Databricks workspace
2. Click your username (top-right) → **Settings**
3. Go to **Developer** → **Access Tokens**
4. Click **Generate New Token**
5. Set expiration (recommend 90 days for development)
6. **Copy and save the token immediately** - it won't be shown again

> **Note:** If using Service Principals for CI/CD, the `data-engineers` group must have token usage permissions (configured via Terraform in the infrastructure project).

---

## 2. Databricks CLI Installation

### Quick Health Check

```bash
# Check if CLI is installed
databricks --version

# List existing profiles
databricks auth profiles

# Check Python version
python3 --version
```

### Install/Update CLI

```bash
# Remove old binary if needed
sudo rm -f '/usr/local/bin/databricks'

# Install latest CLI
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sudo sh

# Verify installation
databricks --version  # Should show v0.218.0 or higher
```

### Configure CLI Profile

```bash
databricks configure --token
```

You'll be prompted for:
- **Host:** Your workspace URL (e.g., `https://adb-123456789.azuredatabricks.net`)
- **Token:** The PAT you generated earlier

> **Important:** Do not include a trailing slash in the host URL.

### Validate Configuration

```bash
# List workspace root - should return folder names
databricks workspace list /
```

---

## 3. VS Code Extension Setup

### Step 3.1: Install Extension

1. Open VS Code
2. Go to Extensions (`Ctrl+Shift+X`)
3. Search for "Databricks"
4. Install the official **Databricks** extension

### Step 3.2: Connect to Workspace

1. **Reload VS Code:** `F1` → `Developer: Reload Window`
2. Click the **Databricks icon** in the sidebar (red/black logo)
3. If it doesn't auto-connect:
   - Click the **gear icon** (Configure Databricks)
   - Select **Select a Databricks configuration profile**
   - Choose **DEFAULT** (or your named profile)
4. Enter your Personal Access Token when prompted

### Step 3.3: Select Python Interpreter

When prompted, select your Python version:

| Cluster Type | Python Version |
|--------------|----------------|
| Serverless | Python 3.11 |
| Classic (e.g., 16.4 LTS) | Python 3.12 |

The extension will automatically install required dependencies.

### Step 3.4: Verify Connection

- The **Workspace** tree should load in the sidebar
- Under **Compute**, select a cluster and set access mode to **Manual**
- A **green dot** indicates successful connection

---

## 4. Classic Cluster Configuration (Optional)

If using classic (non-serverless) clusters, additional configuration is required:

### Enable Spark Connect

In the Databricks UI, when creating or editing your cluster:

1. Go to **Advanced Options** → **Spark** tab
2. Add this Spark configuration:

```
spark.databricks.service.server.enabled true
```

### Local Virtual Environment If not using the Databricks extension's built-in environment:

```bash
# Create venv with Python 3.12
python3.12 -m venv .venv

# Activate
source .venv/bin/activate

# Install databricks-connect
pip install databricks-connect
```

---

## 5. Install UV Package Manager (Recommended)

UV is a fast Python package manager useful for bundle development:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

This is used by bundle templates for building wheel artifacts.

---

## 6. Reset Configuration (Troubleshooting)

If your configuration becomes corrupted:

```bash
# Remove CLI config
rm -f ~/.databrickscfg

# Re-run configuration
databricks configure --token
```

> **Warning:** This permanently deletes all CLI profiles and tokens. Only run if you need to reset completely.

---

## 7. Verify Everything Works

After completing setup, run this validation:

```bash
# 1. CLI can list workspace
databricks workspace list /

# 2. CLI version is current
databricks --version

# 3. Bundle validation works (from any bundle directory)
cd 01-bundle-databricks-exemple
databricks bundle validate -t dev
```

---

## Next Steps

Once your environment is set up:

1. 👉 **[Test your connection](../00-scripts-test-conn/README.md)** - Run connection test scripts
2. 👉 **[Create your first bundle](../01-bundle-databricks-exemple/README.md)** - Use `bundle init`

---

## Common Issues

### "Unauthorized" or "Invalid token"

- Token may have expired - generate a new one
- Wrong profile selected - check `databricks auth profiles`

### Extension doesn't connect

- Reload VS Code window
- Check that `~/.databrickscfg` exists and has correct host/token

### Python version mismatch

- Serverless requires Python 3.11 exactly
- Classic clusters work with Python 3.12
- VS Code may need restart after changing interpreter

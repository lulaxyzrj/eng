# Lesson 00: Connection Testing

This folder contains scripts to test and validate your Databricks connectivity through different methods.

---

## 🎯 Learning Objectives

- Understand different ways to connect to Databricks
- Test VS Code Extension connectivity
- Test Databricks CLI connectivity
- Test programmatic access via Python (Databricks Connect)

---

## Prerequisites

Before running these tests, complete the setup in:
👉 **[Bootstrap Guide](../doc_utils/BOOTSTRAP-GUIDE.md)**


> ⚠️ **Shadow Traffic (Data Availability):** Before running connection tests (especially those verifying data access), execute the gen_shadow generator for only a few seconds (5 to 10s is sufficient). This ensures that valid data exists in the landing zone when you attempt to query tables via VS Code or CLI to verify your connection.
---

## Connection Methods Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CONNECTION METHODS                                     │
│                                                                             │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│   │  VS Code         │  │  Databricks      │  │  Python Module   │          │
│   │  Extension       │  │  CLI             │  │  (Connect)       │          │
│   ├──────────────────┤  ├──────────────────┤  ├──────────────────┤          │
│   │ Interactive      │  │ Terminal         │  │ Programmatic     │          │
│   │ Development      │  │ Commands         │  │ Access           │          │
│   │ Notebook sync    │  │ Bundle deploy    │  │ LLM Integration  │          │
│   └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Available Test Scripts

### 1. `test_connection.ipynb`

Interactive Jupyter notebook for testing connection via VS Code Extension.

**How to use:**
1. Open in VS Code with Databricks extension configured
2. Select your cluster in the Databricks sidebar
3. Run cells to verify connectivity

---

### 2. `test_connection.py` / `test_connection_2.py`

Python scripts for testing programmatic connectivity.

**How to use:**
```bash
# Activate your virtual environment first
source .venv/bin/activate

# Run the test
python test_connection.py
```

---

### 3. `src/teste_connection_terminal.py`

Test connectivity from terminal/CLI context.

```bash
python src/teste_connection_terminal.py
```

---

### 4. `src/utils/spark_session_config.py`

Reusable module for creating Spark sessions with Databricks Connect.

**Key Feature:** This module can be used by LLMs or other automated tools that need to interact with Databricks via the `.venv` created by the VS Code extension.

---

## Testing via VS Code Extension

1. Click the Databricks icon in the sidebar
2. Ensure you see a **green dot** next to your cluster
3. Open `test_connection.ipynb`
4. Run: `spark.sql("SELECT 1").show()`
5. If successful, you're connected!

---

## Testing via CLI

```bash
# List workspace root
databricks workspace list /

# Get cluster info
databricks clusters list

# Check current user
databricks current-user me
```

---

## Testing Programmatically

Create a simple test:

```python
from databricks.connect import DatabricksSession

spark = DatabricksSession.builder.getOrCreate()
spark.sql("SELECT 'Connection successful!' as status").show()
```

---

## Common Issues

### Extension shows "Disconnected"

- Reload VS Code: `F1` → `Developer: Reload Window`
- Check cluster is running
- Verify token is valid

### CLI returns "Unauthorized"

- Token may have expired
- Run `databricks configure --token` to refresh

### Python module import fails

- Ensure virtual environment is activated
- Install databricks-connect: `pip install databricks-connect`

---

## ⚠️ Important Note

The `databricks.yml` file in the **project root** exists **only** for VS Code Extension connectivity. It allows the extension to discover your workspace configuration.

**This root `databricks.yml` is NOT used for bundle deployments.** Each lesson folder (01, 02, 03) contains its own `databricks.yml` for bundle operations.

---

## Next Steps

Once you've verified connectivity:
👉 **[Go to Lesson 01: Your First Bundle](../01-bundle-databricks-exemple/README.md)**

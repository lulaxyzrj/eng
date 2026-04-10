
# 🔎 Understanding `bkcc` vs `multi_tenant_id` in Data Vault 2.1

In a modern, scalable Data Vault model, it's critical to manage business keys carefully — especially when ingesting data from multiple systems or tenants. This guide explains the difference between `bkcc` and `multi_tenant_id`, and when to use each.

---

## 🧠 What Is `bkcc`?

**`bkcc` = Business Key Collision Code**

It is used to prevent **collisions** when the **same business key value** is used across multiple systems or domains but **refers to different real-world entities**.

### ✅ When to Use `bkcc`:
- **Same key, different meaning** across systems
- **Same field name (`id`, `user_id`)** used inconsistently
- You cannot guarantee that keys are globally unique

### 📘 Example:

| System     | id  | Meaning         | bkcc                |
|------------|-----|------------------|---------------------|
| CRM        | 123 | Customer ID      | `crm-customer`      |
| ERP        | 123 | Product ID       | `erp-product`       |

```sql
hash_hub = hash(id + bkcc)
```

---

## 🌍 What Is `multi_tenant_id`?

**`multi_tenant_id`** identifies **which tenant, region, or client** the data belongs to. It allows you to **logically separate** records while using the **same model schema** across clients or regions.

### ✅ When to Use `multi_tenant_id`:
- You're building a **multi-tenant** data platform
- Same real-world entities exist in different business contexts
- You want to **partition**, **filter**, or **govern** by tenant

### 📘 Example:

| tenant        | cpf             | person         | multi_tenant_id |
|---------------|------------------|----------------|-----------------|
| Brazil        | 000.000.000-00   | João           | `tenant-br`     |
| USA           | 000.000.000-00   | John           | `tenant-us`     |

```sql
hash_hub = hash(cpf + multi_tenant_id)
```

---

## 🆚 Summary: bkcc vs multi_tenant_id

| Category           | `bkcc`                                 | `multi_tenant_id`                          |
|--------------------|-----------------------------------------|---------------------------------------------|
| Purpose            | Disambiguate **meaning** of same key   | Segregate **ownership** or **scope**       |
| Hash Involvement   | ✅ Yes, when needed                    | ✅ Often included in hash for multi-tenancy |
| Affects Join Logic | ✅ Yes                                  | ✅ Yes                                      |
| Use in Filtering   | ❌ Not typically                       | ✅ Frequently                               |
| Examples           | `crm-customer`, `erp-product`           | `tenant-br`, `tenant-us`, `client-acme`     |

---

## 🎓 Teaching Tip

> 🔁 **Use `bkcc` when two records look the same but mean different things.**  
> 🌐 **Use `multi_tenant_id` when two records mean the same thing but belong to different tenants.**

---

## ✅ Practical in dbt

```sql
-- Do include bkcc in metadata
SELECT
  hash_hub_user_id,
  user_id,
  'crm-customer' AS bkcc,
  'tenant-br' AS multi_tenant_id,
  ...
```

But **only include `bkcc` in the surrogate key** when a collision risk exists.

---

## 💡 Examples in the UberEats Transactions Domain

| Entity     | BK (Business Key) | Source       | Include in hash? | Why?                                     |
|------------|-------------------|--------------|------------------|------------------------------------------|
| Order      | `order_id`        | Kafka        | ❌               | Single real-world order, global ID       |
| User       | `cpf`             | Mongo, MSSQL | ❌               | Same person across systems               |
| Restaurant | `cnpj`            | MySQL        | ❌               | Unique identifier in Brazil              |
| Driver     | `license_number`  | Postgres     | ❌               | Real-world unique ID                     |
| Product ID | `id`              | ERP + CRM    | ✅ Yes           | Same key used differently → use `bkcc`   |

---

## ✅ Recommended Naming Conventions

| Field             | Example Value         | Notes                                  |
|------------------|------------------------|----------------------------------------|
| `bkcc`           | `trn-user-kafka`       | Domain + entity + source system        |
| `multi_tenant_id`| `tenant-br`            | Region or client slug (e.g., ifood-us) |

---

Let me know if you'd like macros to standardize this logic or validations to test uniqueness in dbt!

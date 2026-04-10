# Azure & Databricks Initial Configuration

> **⚠️ Mandatory:** Completing these steps is **required** to successfully run the automation in this repository.

## 1. Azure Free Trial (Educational Context)

This project is designed to be fully executable within the **Azure Free Trial** ($200 credits).

*   **Cost Efficiency:** The architecture allows for aggressive destruction of resources when not in use.
*   **Real-World Test:** During the development of this course, creating and destroying the entire stack multiple times did not come close to exhausting the free credits. You can proceed with confidence.

> **⚠️ Important Note on Quotas:**
> The Azure Free Trial has strict vCPU quotas (typically 4 vCPUs per region).
> *   **Single Node Clusters:** To stay within these limits, our Terraform code is configured to deploy **Single Node** clusters (Driver only, 0 Workers). This is sufficient for educational purposes.
> *   **Serverless:** We leverage Databricks Serverless SQL where applicable to bypass some of these VM quotas.
> *   **Upgrading:** If you upgrade to a Pay-As-You-Go subscription, you can easily modify the Terraform variables to deploy standard multi-node clusters, but be aware that this will incur higher costs and is done at your own risk.

## 2. Account Setup

1.  **Create Azure Account:** 👉 **[Start Azure Free Trial](https://azure.microsoft.com/en-us/free/)**
2.  **Verify Subscription:** Ensure you have an active subscription (e.g., "Free Trial" or "Pay-As-You-Go") visible in the Portal.

## 3. User Segmentation (Entra ID)

To mimic a real-world enterprise environment, we will create distinct users for Infrastructure and Engineering. This teaches the importance of Separation of Duties.

1.  Go to **[Microsoft Entra ID](https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/Overview)** (formerly Azure AD) in the Azure Portal.
2.  Select **Users** -> **New User** -> **Create new user**.
3.  Create the following two users:
    *   **Infra User:** (e.g., `infra-deploy@yourdomain.onmicrosoft.com`)
        *   *Role:* Responsible for deploying cloud resources.
    *   **Engineering User:** (e.g., `data-engineer@yourdomain.onmicrosoft.com`)
        *   *Role:* Responsible for building data pipelines (ETL).

### Role Assignments (Subscription Level)

For this educational POC, we will simplify permissions to ensure speed of delivery while maintaining the logical separation.

*   **Infra User:**
    *   Go to **Subscriptions** -> Select your Subscription -> **Access control (IAM)** -> **Add role assignment**.
    *   **Role:** `Owner`.
    *   **Why?** The Infra user needs to create Resource Groups, Storage Accounts, and crucially, **assign roles** to Service Principals and Managed Identities. Only `Owner` (or User Access Administrator) can assign roles.
*   **Engineering User:**
    *   **No Azure Roles needed.**
    *   **Why?** This user should **not** have direct access to the Azure Portal infrastructure. Their access will be strictly governed by **Unity Catalog** inside Databricks, which we will configure in Phase 02.

## 4. Databricks Account Console Setup

You need to initialize your Databricks Account to manage Unity Catalog centrally.

1.  **Login:** Go to 👉 **[Databricks Account Console](https://accounts.azuredatabricks.net/)**.
    *   *Note:* You must log in with the **Root Email** (the one you used to create the Azure account) for the first access.
2.  **User Management:**
    *   Go to **User management** (sidebar).
    *   Click **Add user**.
    *   Add both the **Infra User** and **Engineering User** you created in Entra ID.
3.  **Admin Privileges:**
    *   Click on the **Infra User**.
    *   Go to the **Roles** tab.
    *   Toggle on **Account Admin**.
    *   *Note:* The Engineering User should **NOT** be an admin.

## 5. Tool Installation (Ubuntu 24.04 LTS / WSL)

This project was developed and tested on **Ubuntu 24.04 LTS**. It works perfectly on WSL (Windows Subsystem for Linux) for Windows users.
> *   If you are on **macOS**, the commands are similar (use `brew` instead of `apt`), but the scripts are Bash-based and should run natively.

### Install Azure CLI
Used for authentication (`az login`) and managing Azure resources.

```bash
# Update and install prerequisites
sudo apt-get update
sudo apt-get install ca-certificates curl apt-transport-https lsb-release gnupg

# Download and install the Microsoft signing key
mkdir -p /etc/apt/keyrings
curl -sLS https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /etc/apt/keyrings/microsoft.gpg > /dev/null
sudo chmod go+r /etc/apt/keyrings/microsoft.gpg

# Add the Azure CLI software repository
echo "deb [arch=`dpkg --print-architecture` signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/azure-cli.list

# Update repository information and install the azure-cli package
sudo apt-get update
sudo apt-get install azure-cli
```

### Install Terraform
Used to deploy the Infrastructure as Code.

```bash
# Install HashiCorp GPG Key
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Add HashiCorp Repo
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

# Install Terraform
sudo apt update && sudo apt install terraform
```

### Verify Installation
```bash
az version
terraform -version
```

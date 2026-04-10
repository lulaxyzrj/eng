# Secure Networking: VNet Injection & No Public IP

This document explains the networking architecture used in our Databricks deployment, specifically focusing on **VNet Injection**, **Secure Cluster Connectivity (No Public IP)**, and how outbound internet access works in this setup.

## 1. The Architecture: VNet Injection

By default, Databricks creates a managed Virtual Network (VNet) that is locked down. However, for enterprise control, we use **VNet Injection**.

-   **We bring the VNet:** We create an Azure VNet (`ubereats-dev-vnet`) with two specific subnets:
    -   `public-subnet`: For host communication (control plane).
    -   `private-subnet`: For the actual compute clusters (data plane).
-   **Databricks lives inside:** The workspace is "injected" into these subnets.

### Why is this better?
-   **Network Isolation:** We can apply Network Security Groups (NSGs) to control traffic.
-   **Connectivity:** It allows us to connect to other Azure resources (like SQL Databases or On-Premise via VPN/ExpressRoute) using private IPs.

## 2. Secure Cluster Connectivity (No Public IP)

We have enabled the `no_public_ip = true` flag in our Terraform configuration.

-   **What it means:** The Virtual Machines (VMs) that make up your Databricks clusters **do not have public IP addresses**.
-   **Security Benefit:** Attackers cannot directly address or scan your cluster nodes from the internet. There is no open door.
-   **Control Plane Connection:** Databricks uses a "Secure Tunnel" (Relay) to talk to the control plane, so no inbound ports need to be opened.

## 3. The "Magic" of Outbound Access (PIP vs NAT)

A common question is: *"If my cluster has no public IP, how can I install libraries like `pip install streamlit`?"*

You might have noticed that commands like `%pip install` work perfectly fine, even without a NAT Gateway.

### The Phenomenon: Azure Default Outbound Access

Azure provides a "magic" default behavior for VMs without public IPs or Load Balancers:
-   **Mechanism:** Azure routes outbound traffic through a shared, dynamic pool of public IPs managed by Microsoft.
-   **Result:** Your private cluster **can** reach the internet (PyPI, Maven, etc.) to download packages.

### Why this is a "Security Feature" for POCs
-   **Cost Savings:** You save ~$30-45/month by NOT deploying a NAT Gateway.
-   **Convenience:** You get the security of "No Inbound Access" while still having "Outbound Access" for development tasks.

### When to upgrade to a NAT Gateway (Production)
In a strict production environment, we would disable this default access and force traffic through a NAT Gateway for three reasons:
1.  **Static IP:** You need a fixed IP to whitelist on external firewalls (e.g., connecting to a partner's API).
2.  **SNAT Exhaustion:** Heavy concurrent jobs might exhaust the shared ports provided by Azure's default access.
3.  **Compliance:** "Zero Trust" policies often require explicit, logged outbound paths.

**Conclusion:** For this POC/Dev environment, relying on Azure's default outbound access is the **smart, cost-effective choice**. It balances high security (no inbound access) with developer productivity (working `pip install`).

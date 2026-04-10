## ✅ Setup Guide for Your Local Kubernetes Environment

Here’s a guide to install the main tools needed to work with Kubernetes on your local machine. Each tool plays an important role in the development and debugging process.

💡 Note: Each official website includes an installation guide tailored to different operating systems (Linux, macOS, Windows). Follow the instructions on the linked pages for your system.
---

### 🐳 Step 1: Install Docker Desktop

Docker lets you create and manage containers. It’s required for running Minikube, which uses Docker to simulate Kubernetes locally.

👉 [Download Docker Desktop](https://www.docker.com/)

---

### ⚙️ Step 2: Install Helm

Helm is a package manager for Kubernetes. It helps you install and manage applications on your cluster with simple commands.

👉 [Install Helm](https://helm.sh/docs/intro/install/)

---

### 📦 Step 3: Install Minikube

Minikube allows you to run a local Kubernetes cluster. It’s great for development and testing before deploying to a real environment.

👉 [Install Minikube](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download)

---

### 📡 Step 4: Install kubectl

`kubectl` is the command-line tool to interact with your Kubernetes cluster. You’ll use it to deploy apps, inspect resources, and more.

👉 [Install kubectl](https://pwittrock.github.io/docs/tasks/tools/install-kubectl/)

---

### 📺 Step 5: Install stern

Stern is a tool that helps you view logs from multiple pods in real time. It’s very useful for debugging apps running in Kubernetes.

👉 [Install stern](https://github.com/stern/stern)

---

### 🧭 Step 6: Install k9s

K9s is a terminal-based UI to manage your Kubernetes cluster. It’s a quick and easy way to explore resources and see what’s happening.

👉 [Install k9s](https://k9scli.io/topics/install/)


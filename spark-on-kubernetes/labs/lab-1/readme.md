# Environment Installation Guide

This document provides instructions for setting up the lab environment used by SPOK (Smart Platform for Orchestrated Knowledge). The installation use Helm charts.

## Installation with Helm Charts

Some components are installed using Helm charts. These include both official charts and charts derived from open-source documentation.

### Step 1: Add Helm repository

```sh
# Install the repository
helm repo add spark-operator https://kubeflow.github.io/spark-operator

# Update the repository
helm repo update
```

### Step 2: Download Charts

```sh
# Download and extract Helm charts to source directory
helm pull spark-operator/spark-operator --version 2.1.1 --untar --untardir ./src/helm-charts

```

### Step 3: Create Kubernetes Environment

```sh
# Start the minikube
minikube start --cpus=4 --memory=8G

# Create the namespace to be used
kubectl create namespace processing
```

### Step 4: Install Applications Using Helm

Replace paths and values according to the application you are installing.

```sh
helm install spark-operator ./src/helm-charts/spark-operator -f ./src/helm-charts/spark-operator/values.yaml -n processing
```









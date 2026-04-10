# Environment Installation Guide

This document provides instructions for setting up the lab environment used by SPOK (Smart Platform for Orchestrated Knowledge). The installation use Helm charts.

## Installation with Helm Charts

Some components are installed using Helm charts. These include both official charts and charts derived from open-source documentation.

### Step 1: Add Helm repositorys

```sh
# Install the repository
helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo add minio-operator https://operator.min.io
helm repo add prometheus https://prometheus-community.github.io/helm-charts

# Update the repository
helm repo update
```

### Step 2: Download Charts

```sh
# Download and extract Helm charts to source directory
helm pull spark-operator/spark-operator --version 2.1.1 --untar --untardir ./src/helm-charts
helm pull minio-operator/operator --version 7.0.0 --untar --untardir ./src/helm-charts
helm pull minio-operator/tenant --version 7.0.0 --untar --untardir ./src/helm-charts
helm pull prometheus/kube-prometheus-stack --version 69.3.2 --untar --untardir ./src/helm-charts
```

### Step 3: Create Kubernetes Environment

```sh
# Start the minikube
minikube start --cpus=4 --memory=8G

# Enable the metrics server
minikube addons enable metrics-server


# Create the namespace to be used
kubectl create namespace processing
kubectl create namespace deepstore
kubectl create namespace monitoring
```

### Step 4: Install Applications Using Helm

Replace paths and values according to the application you are installing.

```sh
# Running Spark Operator
helm install spark-operator ./src/helm-charts/spark-operator -f ./src/helm-charts/spark-operator/values.yaml -n processing

# Running MinIO Operator
helm install minio-operator ./src/helm-charts/operator -f ./src/helm-charts/operator/values.yaml -n deepstore

# Running MinIO Tenant
helm install minio-tenant ./src/helm-charts/tenant -f ./src/helm-charts/tenant/values.yaml -n deepstore

# Running Prometheus Operator
helm install prometheus-operator ./src/helm-charts/kube-prometheus-stack -f ./src/helm-charts/kube-prometheus-stack/values.yaml -n monitoring

```

### Step 5: Build the Docker image with the spark app

```sh
# Navigate to the images folder src/images/spark and build the image
docker build -t grudtnerv/spok:1.0.0 .

# Push the image to the registry
docker push grudtnerv/spok:1.0.0 
```


### Step 6: Generate the datasets

```sh
# Apply the shadowtraffic manifest
kubectl apply -f src/datagen/shadowtraffic-ubereats.yaml -n default
```


### Step 7: Run the example

```sh
kubectl apply -f labs/lab-6/scripts/secret-credential.yaml -n processing

kubectl apply -f labs/lab-6/scripts/service-metrics.yaml -n processing

kubectl apply -f labs/lab-6/scripts/spark-application.yaml -n processing
```





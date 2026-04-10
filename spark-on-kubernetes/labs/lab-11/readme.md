# Environment Installation Guide

This document provides instructions for setting up the lab environment used by SPOK (Smart Platform for Orchestrated Knowledge). The installation use Helm charts.



# Terraform Scripts to Deploy SPOK Environment

## Commands to Set Up the Lab Environment



The labs can be deployed on your **local machine** (using Minikube) or in the **cloud** (using EKS). Choose only **one** environment before starting. Be aware that using cloud infrastructure may incur costs.

```sh
# Initialize the infrastructure - run this inside the src/terraform/platform folder
# Uncomment the variables to choose between Minikube or EKS
# Select the Kubernetes environment where you want to run BDK

cd src/terraform/platform

terraform init

terraform plan

terraform apply --auto-approve

# If you chose EKS
aws eks update-kubeconfig --region us-east-1 --name k8s-aws
```

**Important:** Only one Kubernetes environment should be active. Comment out any modules or variables related to environments you are not using.

---



## Installing ArgoCD

The applications are deployed using ArgoCD manifests. Make sure you have a running ArgoCD instance. This project includes a Terraform script that sets it up.

```sh
# Go to the ArgoCD Terraform folder
cd src/terraform/gitops/argocd

terraform init

terraform plan

terraform apply --auto-approve

# JUST IN CASE: If your repository doesn’t connect properly, apply the config manually
kubectl apply -f ./git-repo-conf.yaml -n gitops
```

After ArgoCD is installed, you need to apply the app manifests.
**Important:** Make sure to adjust the `storageClass` settings depending on the environment. By default, the labs are set up to run on Minikube.



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



### Step 4: Install Applications Using ArgoCD

Replace paths and values according to the application you are installing.

```sh
# Installing Spark Operator
kubectl apply -f src/app-manifests/processing/spark.yaml -n gitops

# Installing Prometheus Stack
kubectl apply -f src/app-manifests/monitoring/kube-prometheus.yaml -n gitops

# Installing MinIO
kubectl apply -f src/app-manifests/deepstore/minio-operator.yaml -n gitops
kubectl apply -f src/app-manifests/deepstore/minio-tenant.yaml -n gitops

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
kubectl apply -f labs/lab-11/scripts/secret-credential.yaml -n processing

kubectl apply -f labs/lab-11/scripts/service-metrics.yaml -n processing

kubectl apply -f labs/lab-11/scripts/spark-application.yaml -n processing
```





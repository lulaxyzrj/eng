# Migrating MinIO from Minikube to Docker

This document covers moving MinIO from a Minikube-hosted environment to Docker, running alongside a Spark cluster on Docker.

## Prerequisites

- Docker running with Spark cluster (`spark-master`, `spark-worker-1/2/3`, `spark-history-server`)
- Minikube running with MinIO deployed in the `deepstore` namespace

---

## Step 1: Inspect the Spark Docker Network

```sh
docker inspect spark-worker-1 --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}'
```

---

## Step 2: Find the MinIO Data Path in Minikube

```sh
kubectl get pv -o yaml | grep path
```

Expected output:
```
path: /tmp/hostpath-provisioner/deepstore/data0-datalake-pool-0-0
```

---

## Step 3: Check Data Size

```sh
minikube ssh "sudo du -sh /tmp/hostpath-provisioner/deepstore/data0-datalake-pool-0-0"
```

---

## Step 4: Scale Down MinIO in Minikube

```sh
kubectl scale statefulset datalake-pool-0 -n deepstore --replicas=0
```

Verify the pod is down:

```sh
kubectl get pods -n deepstore
```

---

## Step 5: Archive the MinIO Data Inside the Minikube VM

```sh
minikube ssh "sudo tar -czf /tmp/minio-data.tar.gz -C /tmp/hostpath-provisioner/deepstore data0-datalake-pool-0-0"
```

---

## Step 6: Copy the Archive to the Local Machine

```sh
minikube cp minikube:/tmp/minio-data.tar.gz ~/minio-data.tar.gz
```

---

## Step 7: Extract the Archive

```sh
mkdir -p ~/minio-data
tar -xzf ~/minio-data.tar.gz -C ~/minio-data
```

---

## Step 8: Start MinIO on Docker

Replace `build_default` with the actual Spark Docker network name found in Step 1.

```sh
docker run -d \
  --name minio \
  --network build_default \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -v ~/minio-data/data0-datalake-pool-0-0:/data \
  quay.io/minio/minio server /data --console-address ":9001"
```

---

## Step 9: Verify MinIO is Running

```sh
docker logs minio
```

---

## Endpoints

| Service       | URL                      |
|---------------|--------------------------|
| MinIO API     | http://localhost:9000    |
| MinIO Console | http://localhost:9001    |
| MinIO (from Spark containers) | http://minio:9000 |

Credentials: `minioadmin` / `minioadmin`

---

## Spark S3A Configuration

To connect Spark jobs to MinIO, add the following to your Spark configuration:

```
spark.hadoop.fs.s3a.endpoint=http://minio:9000
spark.hadoop.fs.s3a.access.key=minioadmin
spark.hadoop.fs.s3a.secret.key=minioadmin
spark.hadoop.fs.s3a.path.style.access=true
spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem
```
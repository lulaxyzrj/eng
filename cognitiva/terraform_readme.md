# Terraform Infrastructure Setup

This directory contains Terraform configurations for the Cognitive SaaS platform on Google Cloud Platform.

## Prerequisites

1. **Install Terraform**
   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. **Install Google Cloud SDK**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or follow: https://cloud.google.com/sdk/docs/install
   ```

3. **Authenticate with GCP**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

4. **Set your GCP project**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

## Initial Setup (Do this ONCE)

### 1. Create GCS bucket for Terraform state

```bash
# Change this to a globally unique name
export PROJECT_ID="your-gcp-project-id"
export BUCKET_NAME="${PROJECT_ID}-terraform-state"

# Create the bucket
gcloud storage buckets create gs://${BUCKET_NAME} \
  --location=southamerica-east1 \
  --uniform-bucket-level-access

# Enable versioning (important for state recovery)
gcloud storage buckets update gs://${BUCKET_NAME} --versioning
```

### 2. Update terraform.tfvars

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars  # If you created an example file
# Edit terraform.tfvars with your project_id
```

Update the `project_id` in `terraform.tfvars`:
```hcl
project_id = "your-actual-gcp-project-id"
```

Also update the backend bucket name in `main.tf`:
```hcl
backend "gcs" {
  bucket = "your-actual-bucket-name"  # Match what you created above
  prefix = "env/dev"
}
```

## Usage

### Initialize Terraform

```bash
cd terraform/environments/dev
terraform init
```

This downloads required providers and configures the GCS backend.

### Plan changes

```bash
terraform plan
```

Review what Terraform will create. This is safe and doesn't make any changes.

### Apply changes

```bash
terraform apply
```

Type `yes` when prompted. This will create all infrastructure.

**First apply takes ~10-15 minutes** (Cloud SQL is slow to provision).

### View outputs

```bash
terraform output
```

Shows important values like:
- Cloud Run URL
- Database connection name
- Storage bucket names

### Destroy everything (DANGEROUS)

```bash
terraform destroy
```

**Only use this in dev!** Never run in production without backups.

## Project Structure

```
terraform/
├── environments/
│   ├── dev/           # Development environment
│   │   ├── main.tf    # Main configuration
│   │   └── terraform.tfvars
│   ├── staging/       # Staging (copy dev and adjust)
│   └── prod/          # Production (copy dev with prod settings)
└── modules/           # Reusable modules (future)
    ├── cloud-run/
    ├── cloud-sql/
    └── networking/
```

## What Gets Created

- **VPC Network** with private subnet
- **Cloud SQL (PostgreSQL)** - private IP only, automated backups
- **Cloud Storage bucket** - encrypted, lifecycle policies for cost savings
- **Cloud Run service** - autoscaling API backend
- **VPC Connector** - allows Cloud Run to access Cloud SQL privately
- **Pub/Sub topic** - for game events
- **Artifact Registry** - for Docker images
- **Secret Manager** - stores database password
- **KMS keys** - for encryption
- **Service accounts** with least-privilege IAM roles

## Important Notes

### Security
- Database has **no public IP** (private only)
- TLS/SSL required for all connections
- Secrets stored in Secret Manager
- Encryption at rest with Cloud KMS

### Costs (Development)
- Cloud SQL (db-f1-micro): ~$15-25/month
- Cloud Run: Pay per use (generous free tier)
- Cloud Storage: ~$0.50-2/month (depends on usage)
- VPC Connector: ~$8/month
- **Total: ~$25-35/month for dev**

### Production Changes Needed
1. Change Cloud SQL to `db-custom-2-7680` or larger
2. Set `availability_type = "REGIONAL"` for HA
3. Change Cloud Run to **require authentication** (remove `allUsers` invoker)
4. Enable Cloud Armor for DDoS protection
5. Set up proper monitoring and alerting
6. Configure custom domain with Cloud Load Balancer

## Common Commands

```bash
# Format Terraform files
terraform fmt -recursive

# Validate configuration
terraform validate

# Show current state
terraform show

# List all resources
terraform state list

# Refresh state (sync with actual infrastructure)
terraform refresh

# Target specific resource
terraform apply -target=google_cloud_run_service.api
```

## Troubleshooting

### "Error creating Network: googleapi: Error 403"
- Make sure billing is enabled on your GCP project
- Check you have Owner or Editor role

### "Error creating Instance: Private service connection not found"
- The VPC peering for Cloud SQL takes time
- Wait 2-3 minutes and run `terraform apply` again

### "Backend initialization required"
- Run `terraform init` first
- Make sure the GCS bucket exists

### Cloud Run deployment fails
- Initially the service won't work because there's no Docker image
- Deploy your first image using Cloud Build, then Terraform will manage updates

## Next Steps

After Terraform creates the infrastructure:

1. **Deploy your FastAPI backend**
   ```bash
   cd backend/
   gcloud run deploy cognitive-saas-api-dev \
     --source . \
     --region southamerica-east1
   ```

2. **Connect to Cloud SQL locally**
   ```bash
   gcloud sql connect cognitive-saas-db-dev --user=app_user
   ```

3. **Run database migrations**
   ```bash
   # Get DB password from Secret Manager
   gcloud secrets versions access latest --secret=db-password-dev
   
   # Run Alembic migrations
   cd backend/
   alembic upgrade head
   ```

## References

- [Terraform GCP Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
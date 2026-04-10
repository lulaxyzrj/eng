# 1. Habilite a API do KMS
gcloud services enable cloudkms.googleapis.com --project=cognitiva-310369

# 2. Obtenha o service account do Cloud Storage
export PROJECT_NUMBER=$(gcloud projects describe cognitiva-310369 \
  --format="value(projectNumber)")

export GCS_SERVICE_ACCOUNT="service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com"

echo "Cloud Storage Service Account: $GCS_SERVICE_ACCOUNT"

# 3. Primeiro, crie o keyring e a key manualmente (antes do Terraform)
gcloud kms keyrings create cognitive-saas-keyring-dev \
  --location=southamerica-east1 \
  --project=cognitiva-310369

gcloud kms keys create storage-key \
  --keyring=cognitive-saas-keyring-dev \
  --location=southamerica-east1 \
  --purpose=encryption \
  --project=cognitiva-310369

# 4. Dê permissão ao Cloud Storage
gcloud kms keys add-iam-policy-binding storage-key \
  --keyring=cognitive-saas-keyring-dev \
  --location=southamerica-east1 \
  --member="serviceAccount:${GCS_SERVICE_ACCOUNT}" \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter \
  --project=cognitiva-310369

echo "KMS setup completed."
# Quick Start Guide - Get Running in 2 Hours

Follow these steps to go from zero to a deployed API on GCP.

## Step 1: GCP Project Setup (15 minutes)

### 1.1 Create GCP Project
```bash
# Go to https://console.cloud.google.com/
# Click "Create Project"
# Name: "cognitive-saas-dev" (or your choice)
# Note your PROJECT_ID (it might be different from project name)

export PROJECT_ID="your-project-id-here"
gcloud config set project $PROJECT_ID
```

### 1.2 Enable Billing
- Go to https://console.cloud.google.com/billing
- Link a billing account to your project
- **Important:** You'll get $300 free credits for 90 days

### 1.3 Install Tools
```bash
# Install gcloud CLI
# macOS:
brew install google-cloud-sdk

# Ubuntu/Debian:
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate with your personal account
gcloud auth login

# Set your project
gcloud config set project cognitiva-310369

# Install Terraform
brew install terraform  # macOS
# Or download from: https://www.terraform.io/downloads
```

### 1.4 Create Service Account for Terraform
```bash
# Set project ID
export PROJECT_ID="cognitiva-310369"

# Create service account
gcloud iam service-accounts create terraform-sa \
  --display-name="Terraform Service Account" \
  --project=$PROJECT_ID

# Grant necessary roles for infrastructure management
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:terraform-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:terraform-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:terraform-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/resourcemanager.projectIamAdmin"

# Create and download service account key
mkdir -p ~/.gcp-keys
gcloud iam service-accounts keys create ~/.gcp-keys/terraform-key.json \
  --iam-account=terraform-sa@${PROJECT_ID}.iam.gserviceaccount.com

# Set environment variable for Terraform to use
export GOOGLE_APPLICATION_CREDENTIALS=~/.gcp-keys/terraform-key.json

echo "✅ Service account created and key saved to ~/.gcp-keys/terraform-key.json"
echo "✅ GOOGLE_APPLICATION_CREDENTIALS set"
```

**IMPORTANT:** Add this to your shell profile so it persists:
```bash
# Add to ~/.zshrc (macOS) or ~/.bashrc (Linux)
echo 'export GOOGLE_APPLICATION_CREDENTIALS=~/.gcp-keys/terraform-key.json' >> ~/.zshrc
# Or for bash:
echo 'export GOOGLE_APPLICATION_CREDENTIALS=~/.gcp-keys/terraform-key.json' >> ~/.bashrc

# Reload your shell
source ~/.zshrc  # or source ~/.bashrc
```

## Step 2: Create Terraform State Bucket (5 minutes)

```bash
export PROJECT_ID="cognitiva-310369"
export BUCKET_NAME="${PROJECT_ID}-terraform-state"

# Verify service account credentials are set
echo $GOOGLE_APPLICATION_CREDENTIALS
# Should output: /Users/yourname/.gcp-keys/terraform-key.json (or similar)

# Create bucket using service account
gcloud storage buckets create gs://${BUCKET_NAME} \
  --project=$PROJECT_ID \
  --location=southamerica-east1 \
  --uniform-bucket-level-access

# Enable versioning
gcloud storage buckets update gs://${BUCKET_NAME} --versioning

# Grant service account access to the bucket
gsutil iam ch serviceAccount:terraform-sa@${PROJECT_ID}.iam.gserviceaccount.com:objectAdmin gs://${BUCKET_NAME}

echo "✅ Bucket created: gs://${BUCKET_NAME}"
echo "✅ Service account granted access to bucket"
```

## Step 3: Set Up Terraform (10 minutes)

### 3.1 Clone/Create Your Repo
```bash
# If you're starting fresh:
mkdir cognitive-saas
cd cognitive-saas
git init
mkdir -p terraform/environments/dev
mkdir -p .github/workflows
```

### 3.2 Copy Terraform Files
Copy the Terraform files I provided into:
- `terraform/environments/dev/main.tf`
- `terraform/environments/dev/terraform.tfvars`
- `.gitignore`

### 3.3 Edit Configuration
```bash
cd terraform/environments/dev

# Edit terraform.tfvars
nano terraform.tfvars
```

Change this line:
```hcl
project_id = "cognitiva-310369"
```

Also update the backend bucket in `main.tf`:
```hcl
backend "gcs" {
  bucket = "cognitiva-310369-terraform-state"
  prefix = "env/dev"
}
```

### 3.4 Verify Service Account Credentials
```bash
# Make sure the environment variable is set
echo $GOOGLE_APPLICATION_CREDENTIALS
# Should show: /Users/yourname/.gcp-keys/terraform-key.json

# If not set, run:
export GOOGLE_APPLICATION_CREDENTIALS=~/.gcp-keys/terraform-key.json

# Verify the service account works
gcloud auth list
# You should see both your personal account and the service account
```

## Step 4: Deploy Infrastructure (20-30 minutes)

```bash
cd terraform/environments/dev

# Verify service account credentials are set
echo $GOOGLE_APPLICATION_CREDENTIALS

# Initialize Terraform (uses service account automatically)
terraform init

# See what will be created
terraform plan

# Create everything (this takes 10-15 minutes)
terraform apply
# Type 'yes' when prompted
```

**☕ Coffee break - Cloud SQL takes ~10 minutes to provision**

**Note:** Terraform will use the service account credentials from `GOOGLE_APPLICATION_CREDENTIALS` automatically. You don't need to run `gcloud auth application-default login` anymore.

### 4.1 Save Important Outputs
```bash
# After apply completes, save these:
terraform output

# You'll see:
# - cloud_run_url
# - db_instance_name
# - db_connection_name
# - media_bucket_name
```
terraform output
artifact_registry = "southamerica-east1-docker.pkg.dev/cognitiva-310369/cognitiva-saas-dev"
db_connection_name = "cognitiva-310369:southamerica-east1:cognitiva-saas-db-dev"
db_instance_name = "cognitiva-saas-db-dev"
media_bucket_name = "cognitiva-310369-media-dev"

## Step 5: Set Up Local Development (15 minutes)

### 5.1 Install Cloud SQL Proxy
```bash
# macOS
brew install cloud-sql-proxy

# Linux
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy
sudo mv cloud_sql_proxy /usr/local/bin/
```

### 5.2 Get Database Password
```bash
# Using service account credentials to access secrets
export DB_PASSWORD=$(gcloud secrets versions access latest \
  --secret=db-password-dev \
  --project=cognitiva-310369)
  
echo $DB_PASSWORD  # Save this - you'll need it
echo $DB_PASSWORD  # Save this - you'll need it
]?vWPngJLBF:}a{sC6#S>436%u5iu{Fx
```

### 5.3 Connect to Database Locally
```bash
# Get connection name from Terraform output
cd terraform/environments/dev
export CONNECTION_NAME=$(terraform output -raw db_connection_name)

# Go back to project root
cd ../../..

# Start proxy in background
# The proxy will use your personal gcloud credentials, not the service account
cloud-sql-proxy $CONNECTION_NAME &

# Now you can connect on localhost:5432
# Username: app_user
# Password: (the one from step 5.2)
# Database: cognitive_saas
```

**Note:** Cloud SQL Proxy uses your personal `gcloud auth login` credentials, not the service account. This is normal and expected.

### 5.4 Test Connection
```bash
# Install PostgreSQL client
brew install postgresql  # macOS
sudo apt install postgresql-client  # Ubuntu

# Connect
psql "host=127.0.0.1 port=5432 dbname=cognitive_saas user=app_user password=$DB_PASSWORD"

# You should see:
# cognitive_saas=>
```

## Step 6: Create Simple FastAPI Backend (30 minutes)

### 6.1 Create Backend Directory
```bash
cd ../../../  # Back to project root
mkdir backend
cd backend
```

### 6.2 Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pydantic[email]
pip freeze > requirements.txt
```

### 6.3 Create Simple API
Create `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

app = FastAPI(
    title="Cognitive SaaS API",
    description="API for cognitive stimulation platform",
    version="0.1.0"
)

# CORS - allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Cognitive SaaS API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "local")
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/patients")
def list_patients():
    # Placeholder - will connect to database later
    return {
        "patients": [],
        "count": 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 6.4 Test Locally
```bash
# Run the API
python main.py

# In another terminal, test it:
curl http://localhost:8080/
curl http://localhost:8080/health
```

You should see JSON responses! 🎉

## Step 7: Deploy to Cloud Run (20 minutes)

### 7.1 Create Dockerfile
Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Cloud Run expects port 8080
ENV PORT=8080

# Run the application
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
```

### 7.2 Create .dockerignore
Create `backend/.dockerignore`:
```
venv/
__pycache__/
*.pyc
.env
.git/
.pytest_cache/
*.egg-info/
```

### 7.3 Deploy to Cloud Run
```bash
# Make sure you're in the backend directory
cd backend

# Deploy (Cloud Build will containerize automatically)
gcloud run deploy cognitive-saas-api-dev \
  --source . \
  --region southamerica-east1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=dev

# This takes 2-3 minutes
```

### 7.4 Test Deployed API
```bash
# Get the URL
export API_URL=$(gcloud run services describe cognitive-saas-api-dev \
  --region southamerica-east1 \
  --format 'value(status.url)')

echo "API URL: $API_URL"

# Test it
curl $API_URL/
curl $API_URL/health
```

**🎉 SUCCESS! You now have a live API on GCP!**

## Step 8: Add Database Models (30 minutes)

### 8.1 Create Database Models
Create `backend/models.py`:
```python
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class Clinic(Base):
    __tablename__ = "clinics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False)
    name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime)
    gender = Column(String(50))
    contact_info = Column(JSON)
    consent_signed = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Anamnesis(Base):
    __tablename__ = "anamnesis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    sports = Column(JSON)
    interests = Column(JSON)
    photo_refs = Column(JSON)  # References to Cloud Storage
    notes = Column(String)
    completed_by = Column(String(255))  # Clinician ID/name
    created_at = Column(DateTime, default=datetime.utcnow)

class GameSession(Base):
    __tablename__ = "game_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    game_type = Column(String(100), nullable=False)
    difficulty = Column(Integer, default=1)
    score = Column(Integer)
    duration_seconds = Column(Integer)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    session_data = Column(JSON)  # Game-specific data
```

### 8.2 Create Database Connection
Create `backend/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database connection
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "cognitive_saas")
DB_USER = os.getenv("DB_USER", "app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 8.3 Set Up Alembic
```bash
# Initialize Alembic
alembic init alembic

# Edit alembic.ini - find this line:
# sqlalchemy.url = driver://user:pass@localhost/dbname

# Comment it out and we'll use env.py instead
```

Edit `alembic/env.py`:
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add your models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Base
from database import DATABASE_URL

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 8.4 Create First Migration
```bash
# Make sure Cloud SQL Proxy is running and DB_PASSWORD is set
export DB_PASSWORD=$(gcloud secrets versions access latest --secret=db-password-dev)

# Generate migration
alembic revision --autogenerate -m "create initial tables"

# Apply migration
alembic upgrade head
```

### 8.5 Verify Tables Were Created
```bash
psql "host=127.0.0.1 port=5432 dbname=cognitive_saas user=app_user password=$DB_PASSWORD" \
  -c "\dt"

# You should see:
#  clinics
#  patients
#  anamnesis
#  game_sessions
#  alembic_version
```

## Step 9: Add Real API Endpoints (30 minutes)

### 9.1 Create Pydantic Schemas
Create `backend/schemas.py`:
```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

class ClinicCreate(BaseModel):
    name: str
    contact_email: Optional[EmailStr] = None

class ClinicResponse(BaseModel):
    id: UUID
    name: str
    contact_email: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PatientCreate(BaseModel):
    name: str
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None

class PatientResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    name: str
    date_of_birth: Optional[datetime]
    gender: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class GameSessionCreate(BaseModel):
    game_type: str
    difficulty: int = 1

class GameSessionEnd(BaseModel):
    score: int
    duration_seconds: int
    session_data: Optional[Dict[str, Any]] = None

class GameSessionResponse(BaseModel):
    id: UUID
    patient_id: UUID
    game_type: str
    score: Optional[int]
    started_at: datetime
    ended_at: Optional[datetime]
    
    class Config:
        from_attributes = True
```

### 9.2 Update main.py with Real Endpoints
Replace `backend/main.py` with:
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import os

from database import get_db
from models import Clinic, Patient, GameSession
from schemas import (
    ClinicCreate, ClinicResponse,
    PatientCreate, PatientResponse,
    GameSessionCreate, GameSessionEnd, GameSessionResponse
)

app = FastAPI(
    title="Cognitive SaaS API",
    description="API for cognitive stimulation platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Cognitive SaaS API",
        "status": "running",
        "environment": os.getenv("ENVIRONMENT", "local")
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# Clinic endpoints
@app.post("/api/v1/clinics", response_model=ClinicResponse)
def create_clinic(clinic: ClinicCreate, db: Session = Depends(get_db)):
    db_clinic = Clinic(**clinic.dict())
    db.add(db_clinic)
    db.commit()
    db.refresh(db_clinic)
    return db_clinic

@app.get("/api/v1/clinics", response_model=List[ClinicResponse])
def list_clinics(db: Session = Depends(get_db)):
    return db.query(Clinic).all()

# Patient endpoints
@app.post("/api/v1/clinics/{clinic_id}/patients", response_model=PatientResponse)
def create_patient(
    clinic_id: str,
    patient: PatientCreate,
    db: Session = Depends(get_db)
):
    # Verify clinic exists
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    db_patient = Patient(clinic_id=clinic_id, **patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.get("/api/v1/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.get("/api/v1/clinics/{clinic_id}/patients", response_model=List[PatientResponse])
def list_patients(clinic_id: str, db: Session = Depends(get_db)):
    return db.query(Patient).filter(Patient.clinic_id == clinic_id).all()

# Game session endpoints
@app.post("/api/v1/patients/{patient_id}/sessions", response_model=GameSessionResponse)
def start_session(
    patient_id: str,
    session: GameSessionCreate,
    db: Session = Depends(get_db)
):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    db_session = GameSession(patient_id=patient_id, **session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.put("/api/v1/sessions/{session_id}/end", response_model=GameSessionResponse)
def end_session(
    session_id: str,
    session_data: GameSessionEnd,
    db: Session = Depends(get_db)
):
    db_session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_session.score = session_data.score
    db_session.duration_seconds = session_data.duration_seconds
    db_session.session_data = session_data.session_data
    db_session.ended_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_session)
    return db_session

@app.get("/api/v1/patients/{patient_id}/sessions", response_model=List[GameSessionResponse])
def list_sessions(patient_id: str, db: Session = Depends(get_db)):
    return db.query(GameSession).filter(GameSession.patient_id == patient_id).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 9.3 Test API Locally
```bash
# Make sure Cloud SQL Proxy is running
# Start API
export DB_PASSWORD=$(gcloud secrets versions access latest --secret=db-password-dev)
python main.py

# In another terminal, test:
# Create a clinic
curl -X POST http://localhost:8080/api/v1/clinics \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Clinic", "contact_email": "test@clinic.com"}'

# Save the clinic_id from response, then create a patient
curl -X POST http://localhost:8080/api/v1/clinics/YOUR_CLINIC_ID/patients \
  -H "Content-Type: application/json" \
  -d '{"name": "Maria Silva", "gender": "female"}'

# List patients
curl http://localhost:8080/api/v1/clinics/YOUR_CLINIC_ID/patients
```

## Step 10: Redeploy to Cloud Run (10 minutes)

### 10.1 Update requirements.txt
```bash
pip freeze > requirements.txt
```

### 10.2 Deploy
```bash
gcloud run deploy cognitive-saas-api-dev \
  --source . \
  --region southamerica-east1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=dev,DB_HOST=YOUR_DB_PRIVATE_IP,DB_NAME=cognitive_saas,DB_USER=app_user \
  --set-secrets DB_PASSWORD=db-password-dev:latest \
  --vpc-connector vpc-connector-dev \
  --vpc-egress private-ranges-only

# Get DB private IP from Terraform
cd ../../terraform/environments/dev
terraform output
```

### 10.3 Test Production API
```bash
export API_URL=$(gcloud run services describe cognitive-saas-api-dev \
  --region southamerica-east1 \
  --format 'value(status.url)')

curl $API_URL/health
```

## 🎉 Done! You now have:

✅ Full GCP infrastructure (Terraform-managed)
✅ PostgreSQL database with migrations
✅ FastAPI backend deployed on Cloud Run
✅ Working REST API endpoints
✅ Private networking (Cloud Run → Cloud SQL)
✅ Secrets in Secret Manager

## Next Steps

1. **Add authentication** (Identity Platform / Firebase Auth)
2. **Build React frontend** for clinicians
3. **Build React Native app** for patients/tablets
4. **Add file upload** to Cloud Storage
5. **Set up CI/CD** with GitHub Actions
6. **Add monitoring** and alerts

## Troubleshooting

### Service Account Issues

**"GOOGLE_APPLICATION_CREDENTIALS not set"**
```bash
# Check if set
echo $GOOGLE_APPLICATION_CREDENTIALS

# If empty, set it
export GOOGLE_APPLICATION_CREDENTIALS=~/.gcp-keys/terraform-key.json

# Make it permanent
echo 'export GOOGLE_APPLICATION_CREDENTIALS=~/.gcp-keys/terraform-key.json' >> ~/.zshrc
source ~/.zshrc
```

**"Permission denied" errors with Terraform**
```bash
# Verify service account has correct permissions
gcloud projects get-iam-policy cognitiva-310369 \
  --flatten="bindings[].members" \
  --filter="bindings.members:terraform-sa@cognitiva-310369.iam.gserviceaccount.com"

# If missing permissions, re-run the IAM binding commands from Step 1.4
```

**"Service account key file not found"**
```bash
# Check if file exists
ls -la ~/.gcp-keys/terraform-key.json

# If missing, recreate it
gcloud iam service-accounts keys create ~/.gcp-keys/terraform-key.json \
  --iam-account=terraform-sa@cognitiva-310369.iam.gserviceaccount.com
```

### Can't connect to database locally
```bash
# Restart Cloud SQL Proxy
pkill cloud-sql-proxy
cloud-sql-proxy $(terraform output -raw db_connection_name) &
```

### Cloud Run can't connect to database
- Check VPC connector is attached
- Verify DB_HOST is the **private IP** (not public)
- Check Secret Manager permissions

### Migrations fail
```bash
# Check database connection
alembic current
# Downgrade if needed
alembic downgrade -1
# Then upgrade again
alembic upgrade head
```

---

**Estimated total time: ~2 hours** (most of it waiting for GCP to provision resources)
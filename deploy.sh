#!/bin/bash

# Monday.com Portfolio MCP Server - Cloud Run Deployment Script
# This script deploys the MCP server to Google Cloud Run

set -e  # Exit on error

# Configuration
PROJECT_ID="gbo-monday-api"  # CHANGE THIS
SERVICE_NAME="monday-portfolio-mcp"
REGION="us-central1"
MEMORY="512Mi"
CPU="1"
MAX_INSTANCES="10"
MIN_INSTANCES="0"  # Set to 1 for always-on

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Monday.com Portfolio MCP Server to Cloud Run${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if project ID is set
if [ "$PROJECT_ID" = "your-gcp-project-id" ]; then
    echo -e "${RED}❌ Please set your GCP project ID in this script${NC}"
    echo "Edit deploy.sh and change PROJECT_ID to your actual project ID"
    exit 1
fi

# Set the project
echo -e "${BLUE}📋 Setting GCP project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please create a .env file with your Monday.com credentials"
    exit 1
fi

# Create secrets in Secret Manager (if they don't exist)
echo -e "${BLUE}🔐 Setting up secrets in Secret Manager...${NC}"

# Read .env and create secrets
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue
    
    # Remove any quotes and whitespace from value
    value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//" -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    
    # Check if secret exists
    if gcloud secrets describe "$key" --project=$PROJECT_ID &> /dev/null; then
        echo "  ✓ Secret $key already exists, updating..."
        echo -n "$value" | gcloud secrets versions add "$key" --data-file=-
    else
        echo "  + Creating secret $key..."
        echo -n "$value" | gcloud secrets create "$key" --data-file=- --replication-policy="automatic"
    fi
done < .env

echo -e "${GREEN}✅ Secrets configured${NC}"

# Build secret mount arguments
echo -e "${BLUE}🔗 Preparing secret mounts...${NC}"
SECRET_ARGS=""
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue
    
    if [ -z "$SECRET_ARGS" ]; then
        SECRET_ARGS="${key}=${key}:latest"
    else
        SECRET_ARGS="${SECRET_ARGS},${key}=${key}:latest"
    fi
done < .env

# Build and deploy to Cloud Run
echo -e "${BLUE}🏗️  Building and deploying to Cloud Run...${NC}"

gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --memory $MEMORY \
    --cpu $CPU \
    --min-instances $MIN_INSTANCES \
    --max-instances $MAX_INSTANCES \
    --timeout 300 \
    --no-allow-unauthenticated \
    --update-secrets "$SECRET_ARGS"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${BLUE}📍 Service URL:${NC} $SERVICE_URL"
echo ""
echo -e "${BLUE}🔗 Next Steps:${NC}"
echo "1. Test the MCP server endpoint"
echo "2. Configure Gemini to use this MCP server URL"
echo "3. Grant IAM permissions to users who need access"
echo ""
echo -e "${BLUE}💡 Grant access to a user:${NC}"
echo "   gcloud run services add-iam-policy-binding $SERVICE_NAME \\"
echo "     --region=$REGION \\"
echo "     --member='user:email@example.com' \\"
echo "     --role='roles/run.invoker'"
echo ""
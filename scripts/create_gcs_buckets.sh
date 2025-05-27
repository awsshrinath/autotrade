#!/bin/bash

# TRON Cognitive System - GCS Bucket Creation Script
# Creates required Cloud Storage buckets for cognitive data persistence

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧠 TRON Cognitive System - GCS Bucket Setup${NC}"
echo "=============================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ No active gcloud authentication found.${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project set. Please run: gcloud config set project YOUR_PROJECT_ID${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Using GCP Project: ${PROJECT_ID}${NC}"

# Define bucket names
BUCKETS=(
    "tron-cognitive-memory"
    "tron-thought-archives"
    "tron-analysis-reports"
    "tron-memory-backups"
)

# Define bucket descriptions
declare -A BUCKET_DESCRIPTIONS
BUCKET_DESCRIPTIONS["tron-cognitive-memory"]="Stores compressed cognitive memory snapshots for daily reconstruction"
BUCKET_DESCRIPTIONS["tron-thought-archives"]="Archives daily thought journal data in compressed format"
BUCKET_DESCRIPTIONS["tron-analysis-reports"]="Stores performance attribution and learning analysis reports"
BUCKET_DESCRIPTIONS["tron-memory-backups"]="Disaster recovery backups of all cognitive data"

# Default region (change if needed)
REGION=${GCS_REGION:-"asia-south1"}

echo -e "${BLUE}📍 Using region: ${REGION}${NC}"
echo ""

# Function to create bucket with error handling
create_bucket() {
    local bucket_name=$1
    local description=$2
    
    echo -e "${YELLOW}🔨 Creating bucket: ${bucket_name}${NC}"
    echo "   Purpose: ${description}"
    
    # Check if bucket already exists
    if gsutil ls -b gs://${bucket_name} &>/dev/null; then
        echo -e "${GREEN}✅ Bucket ${bucket_name} already exists${NC}"
        return 0
    fi
    
    # Create the bucket
    if gsutil mb -p ${PROJECT_ID} -c STANDARD -l ${REGION} gs://${bucket_name}; then
        echo -e "${GREEN}✅ Successfully created bucket: ${bucket_name}${NC}"
        
        # Set lifecycle policy for automatic cleanup (optional)
        case $bucket_name in
            "tron-thought-archives")
                # Keep thought archives for 1 year
                cat > /tmp/lifecycle-${bucket_name}.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
EOF
                gsutil lifecycle set /tmp/lifecycle-${bucket_name}.json gs://${bucket_name}
                echo -e "${BLUE}   📅 Set 1-year lifecycle policy${NC}"
                rm /tmp/lifecycle-${bucket_name}.json
                ;;
            "tron-memory-backups")
                # Keep backups for 6 months
                cat > /tmp/lifecycle-${bucket_name}.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 180}
      }
    ]
  }
}
EOF
                gsutil lifecycle set /tmp/lifecycle-${bucket_name}.json gs://${bucket_name}
                echo -e "${BLUE}   📅 Set 6-month lifecycle policy${NC}"
                rm /tmp/lifecycle-${bucket_name}.json
                ;;
        esac
        
        # Set versioning for backup bucket
        if [ "$bucket_name" = "tron-memory-backups" ]; then
            gsutil versioning set on gs://${bucket_name}
            echo -e "${BLUE}   🔄 Enabled versioning${NC}"
        fi
        
    else
        echo -e "${RED}❌ Failed to create bucket: ${bucket_name}${NC}"
        return 1
    fi
    
    echo ""
}

# Create all buckets
echo -e "${BLUE}🚀 Creating required GCS buckets...${NC}"
echo ""

SUCCESS_COUNT=0
TOTAL_COUNT=${#BUCKETS[@]}

for bucket in "${BUCKETS[@]}"; do
    if create_bucket "$bucket" "${BUCKET_DESCRIPTIONS[$bucket]}"; then
        ((SUCCESS_COUNT++))
    fi
done

echo "=============================================="
echo -e "${GREEN}📊 Summary: ${SUCCESS_COUNT}/${TOTAL_COUNT} buckets ready${NC}"

if [ $SUCCESS_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "${GREEN}🎉 All cognitive storage buckets created successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "1. Set environment variable: export GCP_PROJECT_ID=${PROJECT_ID}"
    echo "2. Deploy TRON with cognitive system enabled"
    echo "3. Monitor cognitive health through logs"
    echo ""
    echo -e "${BLUE}🔧 Bucket Usage:${NC}"
    for bucket in "${BUCKETS[@]}"; do
        echo "• gs://${bucket} - ${BUCKET_DESCRIPTIONS[$bucket]}"
    done
    echo ""
    echo -e "${YELLOW}💡 Tip: These buckets will automatically store and manage cognitive data${NC}"
    echo "   across daily Kubernetes cluster recreations."
else
    echo -e "${RED}⚠️  Some buckets failed to create. Please check the errors above.${NC}"
    exit 1
fi
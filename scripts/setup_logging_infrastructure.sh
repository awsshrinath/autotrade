#!/bin/bash

# TRON Trading System - Logging Infrastructure Setup
# Creates required GCS buckets and verifies Firestore access for enhanced logging

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 TRON Enhanced Logging Infrastructure Setup${NC}"
echo "=================================================="

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project set. Please run: gcloud config set project YOUR_PROJECT_ID${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Using GCP Project: ${PROJECT_ID}${NC}"

# Define required buckets for enhanced logging
BUCKETS=(
    "tron-trading-logs"
    "tron-trade-data"
    "tron-analysis-reports"
    "tron-memory-backups"
)

# Function to create bucket if it doesn't exist
create_bucket_if_not_exists() {
    local bucket_name=$1
    
    echo -e "${YELLOW}🔍 Checking bucket: ${bucket_name}${NC}"
    
    if gsutil ls -b "gs://${bucket_name}" &>/dev/null; then
        echo -e "${GREEN}✅ Bucket ${bucket_name} already exists${NC}"
    else
        echo -e "${YELLOW}🔨 Creating bucket: ${bucket_name}${NC}"
        if gsutil mb -p "${PROJECT_ID}" -c STANDARD -l asia-south1 "gs://${bucket_name}"; then
            echo -e "${GREEN}✅ Successfully created bucket: ${bucket_name}${NC}"
            
            # Set lifecycle policy to delete logs older than 90 days
            cat > /tmp/lifecycle-${bucket_name}.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF
            
            if gsutil lifecycle set /tmp/lifecycle-${bucket_name}.json "gs://${bucket_name}"; then
                echo -e "${BLUE}   📅 Set 90-day lifecycle policy${NC}"
            fi
            
            rm -f /tmp/lifecycle-${bucket_name}.json
        else
            echo -e "${RED}❌ Failed to create bucket: ${bucket_name}${NC}"
            return 1
        fi
    fi
}

# Create all required buckets
echo -e "\n${BLUE}📦 Setting up GCS buckets...${NC}"
for bucket in "${BUCKETS[@]}"; do
    create_bucket_if_not_exists "$bucket"
done

# Test Firestore access
echo -e "\n${BLUE}🔥 Testing Firestore access...${NC}"
if gcloud firestore databases describe --database="(default)" &>/dev/null; then
    echo -e "${GREEN}✅ Firestore access verified${NC}"
else
    echo -e "${RED}❌ Firestore access failed. Please check permissions.${NC}"
    exit 1
fi

# Create test collections to verify write access
echo -e "${YELLOW}🧪 Testing Firestore write access...${NC}"
cat > /tmp/test_firestore.py <<EOF
import os
from google.cloud import firestore
import datetime

try:
    db = firestore.Client()
    test_doc = db.collection('enhanced_logs_system').document('test')
    test_doc.set({
        'test': True,
        'timestamp': datetime.datetime.now(),
        'setup_script': 'logging_infrastructure'
    })
    test_doc.delete()
    print("✅ Firestore write access verified")
except Exception as e:
    print(f"❌ Firestore write test failed: {e}")
    exit(1)
EOF

if python3 /tmp/test_firestore.py; then
    echo -e "${GREEN}✅ Firestore write access verified${NC}"
else
    echo -e "${RED}❌ Firestore write access failed${NC}"
    exit 1
fi

rm -f /tmp/test_firestore.py

# Test GCS write access
echo -e "${YELLOW}🧪 Testing GCS write access...${NC}"
test_file="/tmp/test_gcs_write.txt"
echo "Test file for GCS write access" > "$test_file"

for bucket in "${BUCKETS[@]}"; do
    if gsutil cp "$test_file" "gs://${bucket}/test_write.txt" &>/dev/null; then
        gsutil rm "gs://${bucket}/test_write.txt" &>/dev/null
        echo -e "${GREEN}✅ GCS write access verified for ${bucket}${NC}"
    else
        echo -e "${RED}❌ GCS write access failed for ${bucket}${NC}"
        exit 1
    fi
done

rm -f "$test_file"

# Display environment variables needed
echo -e "\n${BLUE}🔧 Environment Configuration${NC}"
echo "The following environment variables should be set in your pods:"
echo ""
echo "GCP_PROJECT_ID=${PROJECT_ID}"
echo "ENVIRONMENT=prod"
echo "GCS_LOGS_BUCKET=tron-trading-logs"
echo "GCS_TRADES_BUCKET=tron-trade-data"
echo "GCS_PERFORMANCE_BUCKET=tron-analysis-reports"
echo "GCS_BACKUPS_BUCKET=tron-memory-backups"

echo -e "\n${GREEN}🎉 Enhanced Logging Infrastructure Setup Complete!${NC}"
echo ""
echo "Your pods should now be able to:"
echo "• Write logs to Firestore collections"
echo "• Upload compressed logs to GCS buckets"
echo "• Store trade data and performance metrics"
echo "• Maintain cognitive memory backups"
echo ""
echo "Next steps:"
echo "1. Redeploy your pods with the updated code"
echo "2. Monitor logs in Firestore and GCS buckets"
echo "3. Check the enhanced logger performance metrics" 
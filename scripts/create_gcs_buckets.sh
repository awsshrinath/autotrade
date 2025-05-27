#!/bin/bash

# TRON Trading System - GCS Bucket Creation Script
# Creates required Cloud Storage buckets for trading data, logs, and cognitive system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 TRON Trading System - GCS Bucket Setup${NC}"
echo "=============================================="

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --project PROJECT_ID    Set GCP project ID"
    echo "  -r, --region REGION         Set GCS region (default: asia-south1)"
    echo "  -e, --env ENVIRONMENT       Set environment (dev/staging/prod, default: prod)"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use current gcloud project"
    echo "  $0 -p autotrade-453303               # Set specific project"
    echo "  $0 -r us-central1 -e staging        # Set region and environment"
    exit 1
}

# Parse command line arguments
ENVIRONMENT="prod"
REGION="asia-south1"
PROJECT_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod.${NC}"
    exit 1
fi

echo -e "${CYAN}🌍 Environment: ${ENVIRONMENT}${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if gsutil is installed
if ! command -v gsutil &> /dev/null; then
    echo -e "${RED}❌ gsutil is not installed. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ No active gcloud authentication found.${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Get current project if not specified
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ No GCP project set. Please run: gcloud config set project YOUR_PROJECT_ID${NC}"
        echo "Or use: $0 -p YOUR_PROJECT_ID"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Using GCP Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}📍 Using region: ${REGION}${NC}"

# Check if project exists and user has access
if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
    echo -e "${RED}❌ Cannot access project ${PROJECT_ID}. Please check project ID and permissions.${NC}"
    exit 1
fi

# Define bucket names with environment prefix
ENV_PREFIX="${ENVIRONMENT}-"
if [ "$ENVIRONMENT" = "prod" ]; then
    ENV_PREFIX=""  # No prefix for production
fi

BUCKETS=(
    "${ENV_PREFIX}tron-trading-logs"
    "${ENV_PREFIX}tron-trade-data"
    "${ENV_PREFIX}tron-strategy-configs"
    "${ENV_PREFIX}tron-cognitive-memory"
    "${ENV_PREFIX}tron-thought-archives"
    "${ENV_PREFIX}tron-analysis-reports"
    "${ENV_PREFIX}tron-memory-backups"
    "${ENV_PREFIX}tron-model-artifacts"
    "${ENV_PREFIX}tron-market-data"
)

# Define bucket descriptions
declare -A BUCKET_DESCRIPTIONS
BUCKET_DESCRIPTIONS["${ENV_PREFIX}tron-trading-logs"]="Stores daily trading bot logs and error reports"
BUCKET_DESCRIPTIONS["${ENV_PREFIX}tron-trade-data"]="Historical trade execution data and performance metrics"
BUCKET_DESCRIPTIONS["${ENV_PREFIX}tron-strategy-configs"]="Trading strategy configurations and parameters"
BUCKET_DESCRIPTIONS["${ENV_PREFIX}tron-cognitive-memory"]="Compressed cognitive memory snapshots for daily reconstruction"
BUCKET_DESCRIPTIONS["${ENV_PREFIX}tron-thought-archives"]="Archives daily thought journal data in compressed format"
BUCKET_DESCRIPTIONS["${ENV_PREFIX}tron-analysis-reports"]="Performance attribution and learning analysis reports"
BUCKET_DESCRIPTIONS["${ENV_PREFIX}tron-memory-backups"]="Disaster recovery backups of all cognitive and trading data"
BUCKET_DESCRIPTIONS["${ENV_PREFIX}tron-model-artifacts"]="ML model artifacts and training data"
BUCKET_DESCRIPTIONS["${ENV_PREFIX}tron-market-data"]="Market data cache and historical price data"

echo ""

# Function to create lifecycle policy
create_lifecycle_policy() {
    local bucket_name=$1
    local days=$2
    local policy_file="/tmp/lifecycle-${bucket_name}.json"
    
    cat > "$policy_file" <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": ${days}}
      }
    ]
  }
}
EOF
    
    if gsutil lifecycle set "$policy_file" "gs://${bucket_name}"; then
        echo -e "${BLUE}   📅 Set ${days}-day lifecycle policy${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Failed to set lifecycle policy${NC}"
    fi
    
    rm -f "$policy_file"
}

# Function to set bucket permissions
set_bucket_permissions() {
    local bucket_name=$1
    
    # Set uniform bucket-level access
    if gsutil uniformbucketlevelaccess set on "gs://${bucket_name}" 2>/dev/null; then
        echo -e "${BLUE}   🔒 Enabled uniform bucket-level access${NC}"
    fi
    
    # Set public access prevention
    if gsutil pap set enforced "gs://${bucket_name}" 2>/dev/null; then
        echo -e "${BLUE}   🛡️  Enabled public access prevention${NC}"
    fi
}

# Function to create bucket with error handling
create_bucket() {
    local bucket_name=$1
    local description=$2
    
    echo -e "${YELLOW}🔨 Creating bucket: ${bucket_name}${NC}"
    echo "   Purpose: ${description}"
    
    # Check if bucket already exists
    if gsutil ls -b "gs://${bucket_name}" &>/dev/null; then
        echo -e "${GREEN}✅ Bucket ${bucket_name} already exists${NC}"
        return 0
    fi
    
    # Create the bucket
    if gsutil mb -p "${PROJECT_ID}" -c STANDARD -l "${REGION}" "gs://${bucket_name}"; then
        echo -e "${GREEN}✅ Successfully created bucket: ${bucket_name}${NC}"
        
        # Set bucket permissions
        set_bucket_permissions "$bucket_name"
        
        # Set lifecycle policies based on bucket type
        case $bucket_name in
            *"trading-logs"*)
                create_lifecycle_policy "$bucket_name" 90  # Keep logs for 3 months
                ;;
            *"trade-data"*)
                create_lifecycle_policy "$bucket_name" 2555  # Keep trade data for 7 years (regulatory)
                ;;
            *"thought-archives"*)
                create_lifecycle_policy "$bucket_name" 365  # Keep thought archives for 1 year
                ;;
            *"memory-backups"*)
                create_lifecycle_policy "$bucket_name" 180  # Keep backups for 6 months
                gsutil versioning set on "gs://${bucket_name}"
                echo -e "${BLUE}   🔄 Enabled versioning${NC}"
                ;;
            *"market-data"*)
                create_lifecycle_policy "$bucket_name" 30  # Keep market data cache for 1 month
                ;;
            *"model-artifacts"*)
                gsutil versioning set on "gs://${bucket_name}"
                echo -e "${BLUE}   🔄 Enabled versioning for model artifacts${NC}"
                ;;
        esac
        
    else
        echo -e "${RED}❌ Failed to create bucket: ${bucket_name}${NC}"
        return 1
    fi
    
    echo ""
}

# Function to verify bucket access
verify_bucket_access() {
    local bucket_name=$1
    
    # Try to list bucket contents (should work even if empty)
    if gsutil ls "gs://${bucket_name}/" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Create all buckets
echo -e "${BLUE}🚀 Creating required GCS buckets for ${ENVIRONMENT} environment...${NC}"
echo ""

SUCCESS_COUNT=0
TOTAL_COUNT=${#BUCKETS[@]}
FAILED_BUCKETS=()

for bucket in "${BUCKETS[@]}"; do
    if create_bucket "$bucket" "${BUCKET_DESCRIPTIONS[$bucket]}"; then
        if verify_bucket_access "$bucket"; then
            ((SUCCESS_COUNT++))
        else
            echo -e "${YELLOW}   ⚠️  Bucket created but access verification failed${NC}"
            FAILED_BUCKETS+=("$bucket")
        fi
    else
        FAILED_BUCKETS+=("$bucket")
    fi
done

echo "=============================================="
echo -e "${GREEN}📊 Summary: ${SUCCESS_COUNT}/${TOTAL_COUNT} buckets ready${NC}"

if [ $SUCCESS_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "${GREEN}🎉 All storage buckets created successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "1. Set environment variables:"
    echo "   export GCP_PROJECT_ID=${PROJECT_ID}"
    echo "   export GCS_REGION=${REGION}"
    echo "   export ENVIRONMENT=${ENVIRONMENT}"
    echo ""
    echo "2. Update your Kubernetes deployments with bucket names"
    echo "3. Deploy TRON trading system"
    echo "4. Monitor bucket usage and costs"
    echo ""
    echo -e "${BLUE}🔧 Bucket Usage:${NC}"
    for bucket in "${BUCKETS[@]}"; do
        echo "• gs://${bucket} - ${BUCKET_DESCRIPTIONS[$bucket]}"
    done
    echo ""
    echo -e "${PURPLE}💰 Cost Optimization Tips:${NC}"
    echo "• Lifecycle policies are set to automatically delete old data"
    echo "• Monitor bucket usage: gsutil du -sh gs://bucket-name"
    echo "• Use 'gsutil lifecycle get gs://bucket-name' to view policies"
    echo ""
    echo -e "${CYAN}🔍 Verification Commands:${NC}"
    echo "• List all buckets: gsutil ls -p ${PROJECT_ID}"
    echo "• Check bucket details: gsutil ls -L -b gs://bucket-name"
    
else
    echo -e "${RED}⚠️  Some buckets failed to create. Please check the errors above.${NC}"
    if [ ${#FAILED_BUCKETS[@]} -gt 0 ]; then
        echo -e "${RED}Failed buckets:${NC}"
        for bucket in "${FAILED_BUCKETS[@]}"; do
            echo "  • $bucket"
        done
    fi
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting:${NC}"
    echo "1. Check GCP permissions: gcloud projects get-iam-policy ${PROJECT_ID}"
    echo "2. Verify billing is enabled for the project"
    echo "3. Check if Cloud Storage API is enabled"
    echo "4. Try running with different region: $0 -r us-central1"
    exit 1
fi

echo -e "${GREEN}✨ GCS bucket setup complete!${NC}"
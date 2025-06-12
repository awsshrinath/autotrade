#!/bin/bash

# Validation script for service account fix

set -e

echo "🔍 VALIDATING SERVICE ACCOUNT FIX"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ID="autotrade-453303"
SA_NAME="gpt-runner-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
NAMESPACE="gpt"

echo -e "${YELLOW}📋 Checking requirements...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ gcloud CLI found${NC}"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ kubectl found${NC}"

echo ""
echo -e "${YELLOW}🔐 Checking GCP Service Account...${NC}"

# Check if GCP service account exists
if gcloud iam service-accounts describe $SA_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo -e "${GREEN}✅ GCP service account exists: $SA_EMAIL${NC}"
else
    echo -e "${RED}❌ GCP service account does not exist: $SA_EMAIL${NC}"
    echo -e "${YELLOW}📝 You can create it with:${NC}"
    echo "   gcloud iam service-accounts create $SA_NAME --project=$PROJECT_ID"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔑 Checking IAM roles...${NC}"

# Check required roles
REQUIRED_ROLES=(
    "roles/secretmanager.secretAccessor"
    "roles/storage.admin"
    "roles/datastore.user"
)

for role in "${REQUIRED_ROLES[@]}"; do
    if gcloud projects get-iam-policy $PROJECT_ID \
        --flatten="bindings[].members" \
        --format="table(bindings.role)" \
        --filter="bindings.role:$role AND bindings.members:serviceAccount:$SA_EMAIL" | grep -q "$role"; then
        echo -e "${GREEN}✅ Role assigned: $role${NC}"
    else
        echo -e "${RED}❌ Missing role: $role${NC}"
        echo -e "${YELLOW}📝 You can assign it with:${NC}"
        echo "   gcloud projects add-iam-policy-binding $PROJECT_ID --member='serviceAccount:$SA_EMAIL' --role='$role'"
    fi
done

echo ""
echo -e "${YELLOW}🐙 Checking Kubernetes manifests...${NC}"

# Check if service account manifest exists
if [ -f "deployments/service-account.yaml" ]; then
    echo -e "${GREEN}✅ Service account manifest exists${NC}"
else
    echo -e "${RED}❌ Service account manifest missing${NC}"
    exit 1
fi

# Check if namespace manifest exists
if [ -f "deployments/namespace.yaml" ]; then
    echo -e "${GREEN}✅ Namespace manifest exists${NC}"
else
    echo -e "${RED}❌ Namespace manifest missing${NC}"
    exit 1
fi

# Validate deployment manifests reference the service account
echo ""
echo -e "${YELLOW}🔍 Validating deployment references...${NC}"

DEPLOYMENT_FILES=(
    "deployments/main.yaml"
    "deployments/stock-trader.yaml"
    "deployments/options-trader.yaml"
    "deployments/futures-trader.yaml"
    "deployments/dashboard.yaml"
)

for file in "${DEPLOYMENT_FILES[@]}"; do
    if [ -f "$file" ]; then
        if grep -q "serviceAccountName: gpt-runner-sa" "$file"; then
            echo -e "${GREEN}✅ $file references service account${NC}"
        else
            echo -e "${RED}❌ $file missing service account reference${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ $file not found${NC}"
    fi
done

echo ""
echo -e "${YELLOW}🎯 Testing local deployment (dry-run)...${NC}"

# Check if we have kubectl context
if kubectl config current-context &>/dev/null; then
    CONTEXT=$(kubectl config current-context)
    echo -e "${GREEN}✅ kubectl context: $CONTEXT${NC}"
    
    # Test dry-run of manifests
    echo -e "${YELLOW}🧪 Testing manifest deployment (dry-run)...${NC}"
    
    if kubectl apply -f deployments/namespace.yaml --dry-run=client &>/dev/null; then
        echo -e "${GREEN}✅ namespace.yaml is valid${NC}"
    else
        echo -e "${RED}❌ namespace.yaml has errors${NC}"
    fi
    
    if kubectl apply -f deployments/service-account.yaml --dry-run=client &>/dev/null; then
        echo -e "${GREEN}✅ service-account.yaml is valid${NC}"
    else
        echo -e "${RED}❌ service-account.yaml has errors${NC}"
    fi
    
else
    echo -e "${YELLOW}⚠️ No kubectl context configured - skipping k8s validation${NC}"
fi

echo ""
echo -e "${YELLOW}📊 Summary${NC}"
echo "=========="

if [ -f "deployments/service-account.yaml" ] && \
   gcloud iam service-accounts describe $SA_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo -e "${GREEN}✅ Service account fix appears to be correctly implemented${NC}"
    echo ""
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo "1. Commit and push the changes to trigger CI/CD"
    echo "2. Monitor the deployment workflow"
    echo "3. Verify pods are running: kubectl get pods -n gpt"
    echo ""
    echo -e "${GREEN}🎉 Ready for deployment!${NC}"
else
    echo -e "${RED}❌ Service account fix needs attention${NC}"
    echo ""
    echo -e "${YELLOW}📝 Required actions:${NC}"
    echo "1. Ensure GCP service account exists"
    echo "2. Assign required IAM roles"
    echo "3. Ensure Kubernetes manifests are present"
    exit 1
fi 
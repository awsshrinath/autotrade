#!/bin/bash

# TRON Trading System - Manual Deployment Test Script
# Tests individual deployment files (GitHub Actions CI/CD is the preferred method)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 TRON Trading System - Manual Deployment Test${NC}"
echo "=============================================="
echo -e "${YELLOW}⚠️  Note: This is for manual testing. The preferred deployment method is via GitHub Actions CI/CD.${NC}"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if we can connect to the cluster
if ! kubectl cluster-info &>/dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${GREEN}✅ kubectl and cluster connectivity verified${NC}"

# Check if namespace exists
if ! kubectl get namespace gpt &>/dev/null; then
    echo -e "${YELLOW}⚠️  Namespace 'gpt' does not exist. Creating it...${NC}"
    kubectl create namespace gpt
fi

echo -e "${GREEN}✅ Namespace 'gpt' verified${NC}"

# Warning about infrastructure
echo -e "${YELLOW}⚠️  Important: This script only deploys the trading pods.${NC}"
echo -e "${YELLOW}    GCS buckets and Firestore access should be set up via GitHub Actions first.${NC}"
echo -e "${YELLOW}    Or run the GitHub Actions workflow manually in your repository.${NC}"
echo ""

read -p "Do you want to continue with manual pod deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Deployment cancelled. Use GitHub Actions for full infrastructure setup.${NC}"
    exit 0
fi

# Deploy individual trading pods
echo -e "${BLUE}🚀 Deploying TRON Trading Pods...${NC}"

echo -e "${YELLOW}📦 Deploying main runner...${NC}"
kubectl apply -f deployments/main.yaml

echo -e "${YELLOW}📦 Deploying stock trader...${NC}"
kubectl apply -f deployments/stock-trader.yaml

echo -e "${YELLOW}📦 Deploying options trader...${NC}"
kubectl apply -f deployments/options-trader.yaml

echo -e "${YELLOW}📦 Deploying futures trader...${NC}"
kubectl apply -f deployments/futures-trader.yaml

# Wait a bit for pods to start
echo -e "${YELLOW}⏳ Waiting for trading pods to start...${NC}"
sleep 30

# Check pod status
echo -e "${BLUE}📊 Pod Status:${NC}"
kubectl get pods -n gpt

# Check if pods are running
RUNNING_PODS=$(kubectl get pods -n gpt --field-selector=status.phase=Running --no-headers | wc -l)
TOTAL_EXPECTED=4  # main-runner, stock-trader, options-trader, futures-trader

echo -e "${BLUE}📈 Running Pods: ${RUNNING_PODS}/${TOTAL_EXPECTED}${NC}"

if [ "$RUNNING_PODS" -eq "$TOTAL_EXPECTED" ]; then
    echo -e "${GREEN}✅ All trading pods are running${NC}"
else
    echo -e "${YELLOW}⚠️  Not all pods are running yet. This may be normal during startup.${NC}"
fi

# Check for enhanced logging initialization in logs
echo -e "${BLUE}🔍 Checking for Enhanced Logging Initialization...${NC}"

# Get pod names
STOCK_POD=$(kubectl get pods -n gpt -l app=stock-trader -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
MAIN_POD=$(kubectl get pods -n gpt -l app=main-runner -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -n "$STOCK_POD" ]; then
    echo -e "${BLUE}Stock Trader Enhanced Logging Check:${NC}"
    if kubectl logs "$STOCK_POD" -n gpt 2>/dev/null | grep -i "enhanced.*logging" | head -3; then
        echo -e "${GREEN}✅ Enhanced logging detected in stock trader${NC}"
    else
        echo -e "${YELLOW}⚠️  Enhanced logging not yet visible in stock trader logs${NC}"
        echo -e "${YELLOW}    This may indicate missing GCS buckets or Firestore access issues${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Stock trader pod not found or not ready${NC}"
fi

if [ -n "$MAIN_POD" ]; then
    echo -e "${BLUE}Main Runner Enhanced Logging Check:${NC}"
    if kubectl logs "$MAIN_POD" -n gpt 2>/dev/null | grep -i "enhanced.*logging" | head -3; then
        echo -e "${GREEN}✅ Enhanced logging detected in main runner${NC}"
    else
        echo -e "${YELLOW}⚠️  Enhanced logging not yet visible in main runner logs${NC}"
        echo -e "${YELLOW}    This may indicate missing GCS buckets or Firestore access issues${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Main runner pod not found or not ready${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}📋 Manual Deployment Test Summary:${NC}"
echo "=================================="
echo -e "Trading Pods Deployed: ${BLUE}${RUNNING_PODS}/${TOTAL_EXPECTED}${NC}"
echo ""
echo -e "${YELLOW}⚠️  Infrastructure Setup Status: Unknown${NC}"
echo -e "${YELLOW}    GCS buckets and Firestore access should be verified separately${NC}"
echo ""
echo -e "${GREEN}🎉 Manual deployment test completed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Verify GCS buckets exist: gsutil ls | grep tron-"
echo "2. Test Firestore access in GCP console"
echo "3. Monitor pods: kubectl get pods -n gpt -w"
echo "4. Check logs: kubectl logs -f <pod-name> -n gpt"
echo ""
echo -e "${BLUE}For production deployment, use GitHub Actions CI/CD:${NC}"
echo "git push origin main  # Triggers full automated deployment"
echo ""
echo -e "${BLUE}To clean up this test deployment:${NC}"
echo "kubectl delete -f deployments/" 
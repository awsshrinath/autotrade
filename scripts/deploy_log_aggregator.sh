#!/bin/bash
set -eo pipefail

# Required environment variables
# GCP_PROJECT_ID: Google Cloud project ID
# GCS_BUCKET_NAME: GCS bucket for logs
# GKE_CLUSTER_NAME: The name of the GKE cluster
# GKE_ZONE: The zone where the cluster is located
# IMAGE_TAG: The tag for the docker image, defaults to the git sha
# DOCKER_IMAGE: The Docker image to deploy

# Set variables
IMAGE_TAG=${IMAGE_TAG:-${GITHUB_SHA::7}}
IMAGE_NAME="gpt-runner-log-aggregator"
GCR_PATH="gcr.io/${GCP_PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}"
DEPLOYMENT_FILE="deployments/log-aggregator/deployment.yaml"

echo "--- Building Docker Image ---"
docker build -t "${GCR_PATH}" -f gpt_runner/log_aggregator/Dockerfile .

echo "--- Pushing Docker Image to GCR ---"
docker push "${GCR_PATH}"

echo "--- Preparing Kubernetes Manifest ---"
# Create a temporary deployment file
TMP_DEPLOYMENT_FILE=$(mktemp)
cp "${DEPLOYMENT_FILE}" "${TMP_DEPLOYMENT_FILE}"

# Substitute placeholders
sed -i "s|__IMAGE_PATH__|${GCR_PATH}|g" "${TMP_DEPLOYMENT_FILE}"
sed -i "s|__GCP_PROJECT_ID__|${GCP_PROJECT_ID}|g" "${TMP_DEPLOYMENT_FILE}"
sed -i "s|__GCS_BUCKET_NAME__|${GCS_BUCKET_NAME}|g" "${TMP_DEPLOYMENT_FILE}"

echo "--- Deploying to GKE ---"
gcloud container clusters get-credentials "${GKE_CLUSTER_NAME}" --zone "${GKE_ZONE}" --project "${GCP_PROJECT_ID}"

# Apply infrastructure components in order
echo "Applying ConfigMap..."
kubectl apply -f deployments/log-aggregator/configmap.yaml

echo "Applying NetworkPolicy..."
kubectl apply -f deployments/log-aggregator/network-policy.yaml

echo "Applying Service..."
kubectl apply -f deployments/log-aggregator/service.yaml

echo "Applying Deployment..."
kubectl apply -f "${TMP_DEPLOYMENT_FILE}"

echo "Applying Ingress..."
kubectl apply -f deployments/log-aggregator/ingress.yaml

echo "--- Waiting for deployment to be ready ---"
kubectl rollout status deployment/log-aggregator -n gpt --timeout=300s

echo "--- Checking service status ---"
kubectl get pods -n gpt -l app=log-aggregator
kubectl get services -n gpt -l app=log-aggregator
kubectl get ingress -n gpt -l app=log-aggregator

echo "--- Deployment Successful ---"
kubectl get pods -l app=log-aggregator

# Clean up temporary file
rm "${TMP_DEPLOYMENT_FILE}" 
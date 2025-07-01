#!/bin/bash
set -e

# --- Configuration ---
# Your GCP Project ID
PROJECT_ID="autotrade-453303"

# Your Docker repository location
REPO_LOCATION="asia-south1-docker.pkg.dev"

# The name of your repository
REPO_NAME="tron-system"

# Define the services to build and push
SERVICES=("gpt-runner" "stock-trader" "options-trader" "futures-trader")

# Generate a unique version tag using the current date and a timestamp
VERSION_TAG="v$(date +%Y%m%d)-$(date +%H%M%S)"

echo "🚀 Starting Build and Deploy Process"
echo "==================================="
echo "Project ID: $PROJECT_ID"
echo "Repository: $REPO_LOCATION/$PROJECT_ID/$REPO_NAME"
echo "Version Tag: $VERSION_TAG"
echo "Services: ${SERVICES[@]}"
echo "-----------------------------------"

# Authenticate Docker with Google Cloud
echo "🔐 Authenticating Docker with GCR..."
gcloud auth configure-docker $REPO_LOCATION -q

# Loop through each service to build and push the image
for SERVICE in "${SERVICES[@]}"; do
    IMAGE_NAME="$REPO_LOCATION/$PROJECT_ID/$REPO_NAME/$SERVICE"
    IMAGE_TAG="$IMAGE_NAME:$VERSION_TAG"
    
    echo "🏗️  Building image for $SERVICE..."
    echo "   Image: $IMAGE_TAG"
    
    # Build the Docker image. The --build-arg is used to pass the service name to the Dockerfile
    # if you want to use it for anything, e.g. installing service-specific packages.
    # In this case, we build the same image for all services.
    docker build -t "$IMAGE_TAG" .
    
    echo "   ✅ Build complete for $SERVICE."
    
    echo "⬆️  Pushing image for $SERVICE..."
    docker push "$IMAGE_TAG"
    echo "   ✅ Push complete for $SERVICE."
    echo "-----------------------------------"
done

echo "🔄 Deploying to Kubernetes with Helm..."

# Run Helm upgrade to apply the new image tags to the deployments.
# We will override the image tag for each service.
helm upgrade --install tron-system helm/ -n gpt \\
    --set mainRunner.image.tag=$VERSION_TAG \\
    --set stockTrader.image.tag=$VERSION_TAG \\
    --set optionsTrader.image.tag=$VERSION_TAG \\
    --set futuresTrader.image.tag=$VERSION_TAG

echo "✅ Helm deployment initiated!"
echo "-----------------------------------"
echo "🎉 Build and Deploy Complete!"
echo ""
echo "Monitor the rollout status with:"
echo "kubectl get pods -n gpt -w" 
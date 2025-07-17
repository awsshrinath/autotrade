#!/bin/bash

# Deploy dashboard system with permanent configuration
echo "Deploying dashboard system with permanent configuration..."

# Create k8s directory if it doesn't exist
mkdir -p k8s

# Apply services first
echo "Applying services..."
kubectl apply -f k8s/services.yaml

# Apply nginx configuration
echo "Applying nginx configuration..."
kubectl apply -f k8s/nginx-deployment.yaml

# Apply frontend configuration
echo "Applying frontend configuration..."
kubectl apply -f k8s/frontend-deployment.yaml

# Apply dashboard API configuration
echo "Applying dashboard API configuration..."
kubectl apply -f k8s/dashboard-api-deployment.yaml

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/dashboard-api -n gpt
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n gpt
kubectl wait --for=condition=available --timeout=300s deployment/nginx-proxy -n gpt

echo "Dashboard system deployed successfully!"
echo "Testing API endpoints..."

# Test API endpoints
sleep 5
kubectl get pods -n gpt

echo "Testing dashboard access..."
kubectl get svc -n gpt nginx-proxy
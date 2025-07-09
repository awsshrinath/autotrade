#!/bin/bash

echo "Applying all fixed Kubernetes configurations..."

# Apply all scaler cronjobs
kubectl apply -f k8s/scaling/market-open-scaler.yaml
kubectl apply -f k8s/scaling/market-close-scaler.yaml
kubectl apply -f k8s/scaling/weekend-scaler.yaml
kubectl apply -f k8s/scaling/holiday-scaler.yaml
kubectl apply -f k8s/scaling/trade-start-scaler.yaml
kubectl apply -f k8s/scaling/trade-stop-scaler.yaml

# Apply the tron-backend deployment
kubectl apply -f k8s/deployments/tron-backend.yaml

echo "All configurations applied." 
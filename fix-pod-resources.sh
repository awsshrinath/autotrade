#!/bin/bash

echo "Updating pod resource limits to fix OOM and startup issues..."

# Update futures-trader deployment
kubectl patch deployment futures-trader -n gpt -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "futures-trader",
            "resources": {
              "requests": {
                "memory": "256Mi",
                "cpu": "50m"
              },
              "limits": {
                "memory": "512Mi",
                "cpu": "200m"
              }
            }
          }
        ]
      }
    }
  }
}'

# Update stock-trader deployment
kubectl patch deployment stock-trader -n gpt -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "stock-trader",
            "resources": {
              "requests": {
                "memory": "256Mi",
                "cpu": "50m"
              },
              "limits": {
                "memory": "512Mi",
                "cpu": "200m"
              }
            }
          }
        ]
      }
    }
  }
}'

# Update options-trader deployment
kubectl patch deployment options-trader -n gpt -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "options-trader",
            "resources": {
              "requests": {
                "memory": "256Mi",
                "cpu": "50m"
              },
              "limits": {
                "memory": "512Mi",
                "cpu": "200m"
              }
            }
          }
        ]
      }
    }
  }
}'

echo "Resource limits updated. Waiting for pods to restart..."

# Wait for deployments to be ready
kubectl rollout status deployment/futures-trader -n gpt --timeout=300s
kubectl rollout status deployment/stock-trader -n gpt --timeout=300s
kubectl rollout status deployment/options-trader -n gpt --timeout=300s

echo "Checking pod status..."
kubectl get pods -n gpt
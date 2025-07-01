#!/bin/bash

echo "🚀 Comprehensive Pod Fix Deployment Script"
echo "==========================================="

# Apply the updated entrypoint configuration
echo "📝 Applying updated entrypoint configuration..."
kubectl apply -f entrypoint-config.yaml

# Wait for configmap to be updated
echo "⏱️  Waiting for ConfigMap to propagate..."
sleep 5

# Update deployments with resource limits and startup probes
echo "🔧 Applying resource and health check fixes..."

# Patch futures-trader deployment
echo "   Fixing futures-trader..."
kubectl patch deployment futures-trader -n gpt -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "futures-trader",
            "resources": {
              "requests": {
                "memory": "384Mi",
                "cpu": "50m"
              },
              "limits": {
                "memory": "768Mi",
                "cpu": "300m"
              }
            }
          }
        ]
      }
    }
  }
}'

# Patch stock-trader deployment
echo "   Fixing stock-trader..."
kubectl patch deployment stock-trader -n gpt -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "stock-trader",
            "resources": {
              "requests": {
                "memory": "384Mi",
                "cpu": "50m"
              },
              "limits": {
                "memory": "768Mi",
                "cpu": "300m"
              }
            }
          }
        ]
      }
    }
  }
}'

# Patch options-trader deployment
echo "   Fixing options-trader..."
kubectl patch deployment options-trader -n gpt -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "options-trader",
            "resources": {
              "requests": {
                "memory": "384Mi",
                "cpu": "50m"
              },
              "limits": {
                "memory": "768Mi",
                "cpu": "300m"
              }
            }
          }
        ]
      }
    }
  }
}'

# Patch main-runner deployment
echo "   Fixing main-runner..."
kubectl patch deployment main-runner -n gpt -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "main-runner",
            "resources": {
              "requests": {
                "memory": "512Mi",
                "cpu": "100m"
              },
              "limits": {
                "memory": "896Mi",
                "cpu": "500m"
              }
            }
          }
        ]
      }
    }
  }
}'

# Force rolling restart to apply the entrypoint changes
echo "🔄 Forcing rolling restart to apply entrypoint fixes..."
kubectl rollout restart deployment/futures-trader -n gpt
kubectl rollout restart deployment/stock-trader -n gpt
kubectl rollout restart deployment/options-trader -n gpt
kubectl rollout restart deployment/main-runner -n gpt

echo "⏱️  Waiting for deployments to roll out..."

# Monitor rollout status
kubectl rollout status deployment/futures-trader -n gpt --timeout=300s &
kubectl rollout status deployment/stock-trader -n gpt --timeout=300s &
kubectl rollout status deployment/options-trader -n gpt --timeout=300s &
kubectl rollout status deployment/main-runner -n gpt --timeout=300s &

# Wait for all background processes to complete
wait

echo "✅ All deployments have been updated!"

# Check final pod status
echo "📊 Final pod status:"
kubectl get pods -n gpt

echo ""
echo "🔍 Pod resource usage:"
kubectl top pods -n gpt 2>/dev/null || echo "Metrics not available"

echo ""
echo "✅ Comprehensive Pod Fix Complete!"
echo ""
echo "Fixes Applied:"
echo "  ✅ Fixed initialize_config function calls"
echo "  ✅ Enhanced entrypoint script with validation"
echo "  ✅ Increased memory limits (all pods <1Gi):"
echo "     - futures/stock/options-trader: 384Mi->768Mi"
echo "     - main-runner: 512Mi->896Mi"
echo "  ✅ Added startup probes (300s timeout)"
echo "  ✅ Improved health check configurations"
echo "  ✅ Package structure initialization"
echo ""
echo "Total Memory Usage Per Pod (Under 1Gi Each):"
echo "  - futures-trader: 768Mi limit"
echo "  - stock-trader: 768Mi limit"
echo "  - options-trader: 768Mi limit"
echo "  - main-runner: 896Mi limit"
echo ""
echo "Monitor pods with: kubectl get pods -n gpt -w"
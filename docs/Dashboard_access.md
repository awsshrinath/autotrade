# Find your pod name (already running)
kubectl get pods -n gpt -l app=trading-dashboard

# Port-forward directly to the pod
kubectl port-forward pod/trading-dashboard-5f47898f88-p4ng2 8501:8501 -n gpt
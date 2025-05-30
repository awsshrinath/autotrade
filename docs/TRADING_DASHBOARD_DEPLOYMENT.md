# Trading Dashboard Deployment Guide

## 📋 Overview

The TRON Trading Dashboard is a Streamlit-based real-time monitoring interface that provides comprehensive insights into your trading operations, including live trades, P&L analysis, system health, and cognitive insights.

## 🎯 Features

- **Real-time Trade Monitoring**: Live trade execution tracking
- **P&L Analysis**: Comprehensive profit/loss analytics with interactive charts
- **System Health Dashboard**: Monitor all trading bots and system components
- **Cognitive Insights**: View AI decision-making processes and learning patterns
- **Risk Monitoring**: Real-time risk metrics and alerts
- **Enhanced Logging**: View structured logs from Firestore and GCS

## 🛠️ Prerequisites

### Required Tools
- `kubectl` (Kubernetes CLI)
- `gcloud` (Google Cloud SDK)
- Access to the GKE cluster
- Docker (for local development)

### Required Permissions
- GKE cluster access
- Artifact Registry read/write permissions
- Firestore read permissions
- GCS bucket read permissions

### Environment Setup
```bash
# Set your project ID
export PROJECT_ID="autotrade-453303"
export REGION="asia-south1"
export CLUSTER_NAME="gpt-runner"
export NAMESPACE="gpt"
```

## 🚀 Deployment Methods

### Method 1: Automatic Deployment (Recommended)

The dashboard is automatically deployed via GitHub Actions when you push code to the main branch.

1. **Push your changes:**
   ```bash
   git add .
   git commit -m "Deploy dashboard updates"
   git push origin main
   ```

2. **Monitor the deployment:**
   - Check GitHub Actions at: https://github.com/your-repo/actions
   - Watch for the "CI/CD - Test, Build, Deploy" workflow

3. **Verify deployment:**
   ```bash
   kubectl get pods -n gpt -l app=trading-dashboard
   ```

### Method 2: Manual Deployment

#### Step 1: Build and Push Dashboard Image

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project $PROJECT_ID

# Configure Docker for Artifact Registry
gcloud auth configure-docker asia-south1-docker.pkg.dev

# Build and push the dashboard image
docker build -f dashboard/Dockerfile -t asia-south1-docker.pkg.dev/$PROJECT_ID/gpt-repo/trading-dashboard:latest .
docker push asia-south1-docker.pkg.dev/$PROJECT_ID/gpt-repo/trading-dashboard:latest
```

#### Step 2: Deploy to Kubernetes

```bash
# Get cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID

# Create namespace if it doesn't exist
kubectl apply -f deployments/namespace.yaml

# Deploy the dashboard
kubectl apply -f deployments/dashboard.yaml

# Verify deployment
kubectl rollout status deployment/trading-dashboard -n gpt
```

## 🔍 Accessing the Dashboard

### Method 1: Port Forwarding (Local Development)

```bash
# Forward the dashboard port to your local machine
kubectl port-forward service/trading-dashboard-service 8501:8501 -n gpt

# Open in your browser
open http://localhost:8501
```

### Method 2: LoadBalancer (Production)

If you have configured a LoadBalancer service:

```bash
# Get the external IP
kubectl get service trading-dashboard-service -n gpt

# Access via external IP
open http://<EXTERNAL-IP>:8501
```

### Method 3: Ingress (Domain Access)

If you have configured an Ingress controller:

```bash
# Check ingress status
kubectl get ingress -n gpt

# Access via your domain
open https://dashboard.yourdomain.com
```

## 🔐 Authentication

The dashboard supports built-in authentication:

- **Username**: `admin` (default)
- **Password**: `tron2024` (default)

### Customize Authentication

Edit the dashboard deployment to change credentials:

```yaml
env:
  - name: DASHBOARD_USERNAME
    value: "your-username"
  - name: DASHBOARD_PASSWORD
    value: "your-secure-password"
  - name: AUTH_ENABLED
    value: "true"
```

## ⚙️ Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `production` | Deployment environment |
| `DASHBOARD_USERNAME` | `admin` | Login username |
| `DASHBOARD_PASSWORD` | `tron2024` | Login password |
| `AUTH_ENABLED` | `true` | Enable/disable authentication |
| `REAL_TIME_UPDATES` | `true` | Enable real-time data updates |
| `AUTO_REFRESH_INTERVAL` | `30` | Auto-refresh interval in seconds |
| `FEATURE_LIVE_TRADING` | `false` | Enable live trading features |
| `FEATURE_COGNITIVE_INSIGHTS` | `true` | Enable AI insights |
| `FEATURE_RISK_MONITORING` | `true` | Enable risk monitoring |
| `ALERTS_ENABLED` | `true` | Enable alert notifications |

### Resource Configuration

```yaml
resources:
  requests:
    cpu: "200m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "1Gi"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Pod Stuck in Pending State

```bash
# Check pod events
kubectl describe pod -l app=trading-dashboard -n gpt

# Common causes:
# - Insufficient resources
# - Image pull errors
# - PVC mount issues
```

#### 2. Image Pull Errors

```bash
# Check if image exists
gcloud artifacts docker images list asia-south1-docker.pkg.dev/$PROJECT_ID/gpt-repo/trading-dashboard

# Verify image digest
kubectl get pod -l app=trading-dashboard -n gpt -o yaml | grep image:
```

#### 3. Wrong Image Being Used

If the dashboard pod is running the wrong script (e.g., `main_runner_combined.py`):

```bash
# Check current image digest
kubectl describe pod -l app=trading-dashboard -n gpt | grep "Image ID"

# Compare with futures-trader image
gcloud artifacts docker images list asia-south1-docker.pkg.dev/$PROJECT_ID/gpt-repo/futures-trader

# If digests match, rebuild the dashboard image
docker build -f dashboard/Dockerfile -t asia-south1-docker.pkg.dev/$PROJECT_ID/gpt-repo/trading-dashboard:latest .
docker push asia-south1-docker.pkg.dev/$PROJECT_ID/gpt-repo/trading-dashboard:latest

# Restart deployment
kubectl rollout restart deployment/trading-dashboard -n gpt
```

#### 4. Import Module Errors

If you see `ModuleNotFoundError`:

```bash
# Check logs
kubectl logs -l app=trading-dashboard -n gpt

# Verify the correct Dockerfile is being used
# Dashboard should use dashboard/Dockerfile, not the main Dockerfile
```

#### 5. Streamlit App Not Starting

```bash
# Check pod logs
kubectl logs -l app=trading-dashboard -n gpt

# Check if port 8501 is accessible
kubectl exec -it deployment/trading-dashboard -n gpt -- curl localhost:8501/_stcore/health
```

### Health Checks

The dashboard includes health checks:

```yaml
livenessProbe:
  httpGet:
    path: /_stcore/health
    port: 8501
  initialDelaySeconds: 30
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /_stcore/health
    port: 8501
  initialDelaySeconds: 10
  periodSeconds: 10
```

### Debug Commands

```bash
# Check pod status
kubectl get pods -n gpt -l app=trading-dashboard

# View logs
kubectl logs -f deployment/trading-dashboard -n gpt

# Get detailed pod information
kubectl describe pod -l app=trading-dashboard -n gpt

# Check service
kubectl get service trading-dashboard-service -n gpt

# Test internal connectivity
kubectl exec -it deployment/main-runner -n gpt -- curl http://trading-dashboard-service.gpt.svc.cluster.local:8501/_stcore/health
```

### Log Analysis

Dashboard logs can be found in:

1. **Kubernetes logs**: `kubectl logs -l app=trading-dashboard -n gpt`
2. **GCS logs**: `gs://tron-trading-logs/logs/YYYY/MM/DD/dashboard/`
3. **Firestore logs**: Collection `live_system_status`

## 🔄 Updating the Dashboard

### Code Updates

1. Make changes to dashboard files
2. Commit and push to trigger automatic rebuild
3. Monitor deployment via GitHub Actions

### Manual Update

```bash
# Rebuild image
docker build -f dashboard/Dockerfile -t asia-south1-docker.pkg.dev/$PROJECT_ID/gpt-repo/trading-dashboard:latest .
docker push asia-south1-docker.pkg.dev/$PROJECT_ID/gpt-repo/trading-dashboard:latest

# Force pod restart to pull new image
kubectl rollout restart deployment/trading-dashboard -n gpt

# Watch rollout status
kubectl rollout status deployment/trading-dashboard -n gpt
```

## 📊 Monitoring and Performance

### Performance Metrics

- **Startup Time**: ~30-60 seconds
- **Memory Usage**: ~300-800MB
- **CPU Usage**: ~0.1-0.5 cores
- **Response Time**: <2 seconds for most queries

### Monitoring Commands

```bash
# Monitor resource usage
kubectl top pod -l app=trading-dashboard -n gpt

# Check deployment status
kubectl get deployment trading-dashboard -n gpt

# View recent events
kubectl get events -n gpt --field-selector involvedObject.name=trading-dashboard
```

## 🔒 Security Best Practices

1. **Change default credentials** before production use
2. **Use HTTPS** in production environments
3. **Implement proper RBAC** for Kubernetes access
4. **Enable authentication** in production
5. **Use secrets** for sensitive configuration
6. **Regular security updates** for base images

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Google Cloud Artifact Registry](https://cloud.google.com/artifact-registry/docs)
- [TRON Trading System Documentation](./README.md)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review pod logs and events
3. Verify image builds and deployments
4. Check network connectivity and permissions
5. Consult the development team

---

**Last Updated**: `date +%Y-%m-%d`
**Version**: 1.0
**Maintainer**: TRON Trading Team 
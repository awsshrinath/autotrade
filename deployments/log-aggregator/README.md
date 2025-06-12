# Log Aggregator Infrastructure Integration

This document describes how the Log Aggregator service integrates with the existing GPT Runner+ infrastructure on Google Kubernetes Engine (GKE).

## Infrastructure Overview

The Log Aggregator is deployed as part of the existing `gpt` namespace and integrates seamlessly with the current infrastructure:

### Namespace Integration
- **Namespace**: `gpt` (shared with existing services)
- **Service Account**: `gpt-runner-sa` (reuses existing RBAC permissions)
- **Labels**: Consistent labeling with `component: log-monitoring`

### Network Architecture

```
Internet
    ↓
Load Balancer (GCP)
    ↓
Ingress Controller
    ↓
log-aggregator-service (ClusterIP: 80 → 8001)
    ↓
log-aggregator pods (8001)
```

### External Access
- **Domain**: `logs.tron-trading.com`
- **Protocol**: HTTPS with automatic SSL/TLS via cert-manager
- **Load Balancer**: GCP Load Balancer for high availability

## Kubernetes Resources

### Core Components
1. **Deployment** (`deployment.yaml`)
   - Runs in `gpt` namespace
   - Uses `gpt-runner-sa` service account
   - Mounts GCP service account key for authentication
   - Configured with health checks and resource limits

2. **Service** (`service.yaml`)
   - LoadBalancer type for external access
   - Routes traffic from port 80 to container port 8001

3. **Ingress** (`ingress.yaml`)
   - Provides HTTPS termination
   - Routes `logs.tron-trading.com` to the service
   - Includes CORS configuration for API access

4. **ConfigMap** (`configmap.yaml`)
   - Manages non-sensitive configuration
   - Centralizes environment variables
   - Easy configuration updates without rebuilding images

5. **NetworkPolicy** (`network-policy.yaml`)
   - Secures pod-to-pod communication
   - Allows traffic from dashboard and ingress
   - Restricts egress to necessary external services

## Integration Points

### With Existing Services

1. **Dashboard Integration**
   - Dashboard can access log aggregator via internal service name
   - NetworkPolicy allows traffic from `trading-dashboard` pods
   - Shared namespace enables service discovery

2. **Service Account Reuse**
   - Uses existing `gpt-runner-sa` with cluster-admin permissions
   - Inherits GCP Workload Identity configuration
   - No additional RBAC setup required

3. **Monitoring Integration**
   - Health checks at `/api/v1/health`
   - Prometheus metrics available (if configured)
   - Structured logging compatible with existing log aggregation

### With GCP Services

1. **Google Cloud Storage**
   - Accesses logs from existing GCS buckets
   - Uses same service account for authentication
   - Reads from `trades/`, `reflections/`, `strategies/` prefixes

2. **Firestore**
   - Connects to existing Firestore project (`autotrade-453303`)
   - Reads from `gpt_runner_trades` and `gpt_runner_reflections` collections
   - Uses existing authentication mechanisms

3. **Kubernetes API**
   - Accesses pod logs within the `gpt` namespace
   - Uses in-cluster authentication
   - Leverages existing RBAC permissions

## Security Configuration

### Network Security
- **NetworkPolicy**: Restricts ingress/egress traffic
- **TLS Termination**: HTTPS-only access via ingress
- **CORS**: Configured for cross-origin API access

### Authentication & Authorization
- **Service Account**: Reuses existing `gpt-runner-sa`
- **GCP IAM**: Inherits existing permissions via Workload Identity
- **API Keys**: Stored in Kubernetes secrets

### Secrets Management
- **OpenAI API Key**: Stored in `log-aggregator-secrets`
- **JWT Secret**: For API authentication
- **GCP Service Account**: Mounted as volume from secret

## Deployment Process

### Prerequisites
1. Existing GKE cluster with `gpt` namespace
2. `gpt-runner-sa` service account configured
3. cert-manager for SSL certificate management
4. Ingress controller (nginx or GCE)

### Deployment Steps
```bash
# 1. Apply ConfigMap
kubectl apply -f deployments/log-aggregator/configmap.yaml

# 2. Apply NetworkPolicy
kubectl apply -f deployments/log-aggregator/network-policy.yaml

# 3. Apply Service
kubectl apply -f deployments/log-aggregator/service.yaml

# 4. Apply Deployment
kubectl apply -f deployments/log-aggregator/deployment.yaml

# 5. Apply Ingress
kubectl apply -f deployments/log-aggregator/ingress.yaml
```

### Automated Deployment
Use the provided script for automated deployment:
```bash
./scripts/deploy_log_aggregator.sh
```

## Configuration Management

### Environment Variables
Configuration is managed through:
- **ConfigMap**: Non-sensitive settings
- **Secrets**: API keys and sensitive data
- **Deployment**: Container-specific settings

### Key Configuration Points
- **GCP Project**: `autotrade-453303`
- **Namespace**: `gpt`
- **Service Port**: `8001`
- **External Port**: `80` (via LoadBalancer)

## Monitoring & Troubleshooting

### Health Checks
- **Liveness Probe**: `/api/v1/health` (30s interval)
- **Readiness Probe**: `/api/v1/health` (10s interval)

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Log Level**: Configurable via ConfigMap
- **Log Aggregation**: Compatible with existing log collection

### Common Issues
1. **Pod Not Starting**: Check service account permissions
2. **External Access Issues**: Verify ingress and DNS configuration
3. **GCP Access Issues**: Check Workload Identity setup
4. **Internal Communication**: Verify NetworkPolicy rules

## Scaling & Performance

### Resource Allocation
- **CPU**: 200m request, 1000m limit
- **Memory**: 512Mi request, 2Gi limit
- **Replicas**: 1 (can be scaled horizontally)

### Performance Considerations
- **Log Processing**: Optimized for large log volumes
- **API Response**: Pagination for large datasets
- **Memory Usage**: Efficient streaming for large files

## Future Enhancements

### Potential Improvements
1. **Horizontal Pod Autoscaler**: Auto-scaling based on CPU/memory
2. **Persistent Storage**: For caching and temporary files
3. **Service Mesh**: Istio integration for advanced traffic management
4. **Monitoring**: Prometheus metrics and Grafana dashboards

### Integration Opportunities
1. **Alert Manager**: Integration with existing alerting
2. **Backup Strategy**: Log data backup and retention
3. **Multi-Region**: Cross-region deployment for disaster recovery 
# Cost Monitoring for Kubernetes

Tracking the cost impact of this new scaling strategy is crucial. While the estimated savings are significant, continuous monitoring ensures that the cluster remains cost-effective.

Here are recommended approaches for monitoring GKE costs:

## 1. Using GKE Cost Allocation

GKE has built-in features for cost visibility.

- **Enable Cost Allocation**: Make sure GKE cost allocation is enabled for your cluster. This will tag GKE resources so you can filter them in Google Cloud's billing reports.
- **Use Labels**: We have already added `app` labels to our deployments (`app: stock-trader`, etc.). You can use these labels to group costs by application in the GCP Billing console.

## 2. Using Open-Source Tools (Recommended)

For more granular, real-time cost analysis, consider deploying an open-source tool like OpenCost.

### OpenCost Installation

You can install OpenCost via Helm:

```bash
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm install opencost opencost/opencost --namespace opencost --create-namespace
```

### Accessing the OpenCost UI

Once installed, you can access the dashboard to see a detailed breakdown of costs by namespace, deployment, label, etc.

```bash
kubectl port-forward --namespace opencost service/opencost 9090
```

Navigate to `http://localhost:9090` in your browser.

## 3. Key Metrics to Track

- **Idle Costs**: With the new scaling model, monitor the cost of the cluster during off-market hours. This is your new baseline cost.
- **Per-Pod Costs**: Use OpenCost to see the cost of each trading pod (`stock-trader`, `options-trader`, etc.) when they are running.
- **Node Costs**: Track the cost of the GKE nodes. You should see a clear correlation between the number of nodes and market hours.
- **Total Cluster Cost**: Monitor the overall daily and monthly cost of the cluster to validate the projected ~90% savings. 
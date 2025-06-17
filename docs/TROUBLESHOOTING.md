# Tron Trading System: Troubleshooting Guide

**Last Updated:** 2024-07-16

This guide provides solutions to common problems encountered during the development and deployment of the Tron Trading System.

---

### 1. GKE & Kubernetes Issues

#### Issue: Pod is in `CrashLoopBackOff` or `Error` state.

This is a generic error indicating the container is starting and then immediately crashing.

-   **Solution 1: Check Logs**
    The first step is always to check the pod's logs for a specific error message.
    ```bash
    # Get the exact pod name first
    kubectl get pods -n gpt

    # Then get the logs
    kubectl logs <pod-name> -n gpt

    # If the pod is restarting quickly, use the --previous flag
    kubectl logs <pod-name> -n gpt --previous
    ```
    Common errors found in logs include Python `ImportError`, authentication failures, or missing environment variables.

-   **Solution 2: Check `describe` output**
    The `describe` command provides more details about the pod's lifecycle and events.
    ```bash
    kubectl describe pod <pod-name> -n gpt
    ```
    Look for events at the bottom of the output, such as "Back-off restarting failed container."

-   **Solution 3: Incorrect Image**
    Ensure the Docker image specified in your `deployment.yaml` exists in GCR and the tag is correct. If you pushed a new image but forgot to update the tag in the YAML (e.g., it's still `latest`), Kubernetes might be using an old, broken version.

#### Issue: Pod is in `Pending` state.

This usually means the cluster cannot schedule the pod.

-   **Solution 1: Insufficient Resources**
    The cluster may not have enough CPU or memory to meet the pod's `resources.requests` defined in the YAML.
    -   Check cluster resource usage.
    -   Consider reducing the pod's resource requests or adding a new node to the cluster.

-   **Solution 2: Taints and Tolerations**
    The pod may not have the required tolerations to be scheduled on the available nodes.

#### Issue: Cannot connect to the dashboard or an API.

-   **Solution 1: Check Service and External IP**
    Ensure the service is running and has an external IP address.
    ```bash
    kubectl get services -n gpt
    ```
    If the `EXTERNAL-IP` for `nginx-proxy` is `<pending>`, it might take a few minutes for the cloud provider to assign one.

-   **Solution 2: Check NGINX Proxy Logs**
    The NGINX proxy routes traffic to the backend services. Check its logs to see if requests are being received and where they are being forwarded.
    ```bash
    kubectl logs <nginx-proxy-pod-name> -n gpt
    ```

---

### 2. Application & Python Issues

#### Issue: `ImportError: No module named 'runner'`

-   **Cause:** The Python interpreter cannot find the project's modules. This typically happens when a script is run directly from a subdirectory without the project root being in `sys.path`.
-   **Solution:** Ensure that the entry-point script you are running contains the path modification snippet at the very top.
    ```python
    import os
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    ```

#### Issue: Authentication errors with Zerodha or GCP.

-   **Cause:** Missing or incorrect API keys or credentials.
-   **Solution 1: Check `.env` file:** For local execution, ensure your `.env` file is present, correctly populated, and being loaded.
-   **Solution 2: Check Kubernetes Secrets:** For GKE deployments, verify that the Kubernetes secret exists and is correctly mounted as an environment variable in your deployment YAML.
    ```bash
    # Check if the secret exists
    kubectl get secrets -n gpt

    # Decode a secret to check its value (e.g., for openai-api-key)
    kubectl get secret openai-api-key -n gpt -o jsonpath="{.data.OPENAI_API_KEY}" | base64 --decode
    ```

#### Issue: Dashboard shows "API unavailable"

-   **Cause:** The Streamlit frontend cannot connect to the FastAPI backend.
-   **Solution:**
    1.  Verify the `temp-backend` pod is `Running`.
    2.  Check the `temp-backend` pod's logs for any startup errors.
    3.  Confirm the service name in the NGINX configuration matches the actual backend service name in Kubernetes.
    4.  As a temporary measure, use the dashboard in its offline/fallback mode.

---

### 3. Task Master AI Issues

#### Issue: `task-master` command not found.

-   **Cause:** The Task Master AI CLI tool is not installed or not in the system's PATH.
-   **Solution:**
    -   Install it globally: `npm install -g task-master-ai`
    -   Or run it locally using npx: `npx task-master-ai <command>` 
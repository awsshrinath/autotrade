# Tron Trading System: Development Setup Guide

**Last Updated:** 2024-07-16

This guide provides detailed instructions for setting up a local development environment to work on the Tron Trading System.

---

### 1. Prerequisites

Before you begin, ensure you have the following tools installed and configured on your system:

-   **Git:** For version control.
-   **Python:** Version 3.9 or higher.
-   **pip:** Python's package installer.
-   **Docker:** For building and running containerized applications. [Install Docker](https://docs.docker.com/get-docker/)
-   **Google Cloud SDK:** For interacting with GCP and GKE. [Install gcloud](https://cloud.google.com/sdk/docs/install)
-   **kubectl:** The Kubernetes command-line tool. Install it via gcloud: `gcloud components install kubectl`

---

### 2. Initial Setup

#### Step 1: Clone the Repository

Clone the project from the source repository.

```bash
git clone <your-repository-url>
cd Tron
```

#### Step 2: Set Up Python Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install the required Python packages
pip install -r requirements.txt
```

#### Step 3: Configure Environment Variables

The system relies on environment variables for configuration and secrets.

1.  **Create a `.env` file:** Copy the example file.
    ```bash
    cp .env.example .env
    ```
2.  **Edit the `.env` file:** Open the newly created `.env` file and fill in the required values for:
    -   `ZERODHA_API_KEY`
    -   `ZERODHA_API_SECRET`
    -   `ZERODHA_ACCESS_TOKEN` (You may need to generate this initially)
    -   `OPENAI_API_KEY`
    -   `GCP_PROJECT_ID`
    -   `GCP_SERVICE_ACCOUNT_KEY_PATH` (Path to your GCP service account JSON key)

    **Note:** The `.env` file is listed in `.gitignore` and should never be committed to version control.

---

### 3. Google Cloud & GKE Setup

#### Step 1: Authenticate with GCP

Log in to your Google Cloud account.

```bash
gcloud auth login
gcloud config set project <your-gcp-project-id>
```

#### Step 2: Connect to the GKE Cluster

Fetch the credentials for your GKE cluster to configure `kubectl`.

```bash
# Replace with your actual cluster name and zone
gcloud container clusters get-credentials <your-cluster-name> --zone <your-cluster-zone>
```

#### Step 3: Configure Docker

Configure Docker to authenticate with Google Container Registry (GCR) to pull and push images.

```bash
gcloud auth configure-docker
```

---

### 4. Running the System

#### Building the Docker Image

Before deploying, you need to build the Docker image for the trading applications.

```bash
# Build the image and tag it for GCR
docker build -t gcr.io/<your-gcp-project-id>/tron-trader:latest .

# Push the image to GCR
docker push gcr.io/<your-gcp-project-id>/tron-trader:latest
```

#### Deploying to GKE

You can deploy the system using the provided Kubernetes manifest files.

1.  **Deploy the Minimal System:** This includes the core dashboard components.
    ```bash
    kubectl apply -f minimal-trading-system.yaml
    ```
2.  **Deploy the Trading Pods:** Once the base system is running, deploy the traders.
    ```bash
    kubectl apply -f simple-trading-pods.yaml
    ```
3.  **Verify the Deployment:** Check the status of your pods.
    ```bash
    kubectl get pods -n gpt
    ```
    You should see the `nginx-proxy`, `temp-backend`, `tron-frontend-simple`, `stock-trader-simple`, etc., in `Running` status.

#### Accessing the Dashboard

1.  **Find the NGINX Proxy IP:** Get the external IP address of the load balancer.
    ```bash
    kubectl get services -n gpt | grep nginx-proxy
    ```
2.  Open a web browser and navigate to the `EXTERNAL-IP` listed for the `nginx-proxy` service.

---

### 5. Local Development (Without Docker/GKE)

For quickly testing a single script (e.g., a strategy), you can run it directly:

```bash
# Ensure your .env file is populated and your virtual environment is active
source .venv/bin/activate

# Run a specific runner
python stock_trading/stock_runner.py
```
This is useful for unit testing but does not replicate the full distributed environment. 
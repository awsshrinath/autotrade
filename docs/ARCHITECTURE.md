# Tron Trading System: Architecture

**Last Updated:** 2024-07-16

This document provides a detailed overview of the Tron Trading System's architecture, technology stack, and data flow.

---

### 1. High-Level System Architecture

The system is designed as a cloud-native, event-driven architecture running on Google Kubernetes Engine (GKE). It consists of several independent microservices (pods) that communicate via a shared data layer (Firestore) and are managed by a central orchestrator.

```
+------------------+      +-----------------+      +--------------------+
|  End User / Dev  |----->|  NGINX Proxy    |----->| Streamlit Dashboard|
+------------------+      +-------+---------+      +----------+---------+
                                  |                       |
                                  |                       |
                       +----------v---------+      +------v------+
                       | FastAPI Backend    |<---->|  Firestore  |
                       +--------------------+      +------+------+
                                                          ^
                                                          |
+-------------------------+                               |
|   External Services     |                               |
| (Zerodha Kite, OpenAI)  |                               |
+-----------+-------------+                               |
            ^                                             |
            |                                             |
+-----------v---------------------------------------------v-----------+
|                          GKE Cluster                                |
|                                                                     |
| +------------------------+      +---------------------------------+ |
| |   Main Runner Pod      |----->|   Trading Pods (Stock, Options) | |
| | (Orchestrator, AI)     |      +---------------------------------+ |
| +-------+----------------+                ^        |               |
|         |                                 |        |               |
|         +-------------------------------->+        v               |
|                                                    +---------------+ |
|                                                    | GCS (Logs)    | |
|                                                    +---------------+ |
+---------------------------------------------------------------------+
```

### 2. Technology Stack

-   **Cloud Provider:** Google Cloud Platform (GCP)
-   **Container Orchestration:** Google Kubernetes Engine (GKE) v1.28+
-   **Backend Language:** Python 3.9+
-   **API Framework:** FastAPI
-   **Dashboard:** Streamlit
-   **Real-time Database:** Google Firestore
-   **Log/Data Lake:** Google Cloud Storage (GCS)
-   **Broker API:** Zerodha Kite Connect v3
-   **AI/LLM Provider:** OpenAI
-   **Task Management:** Task Master AI
-   **Containerization:** Docker

### 3. Component Breakdown

#### a. Main Runner (Orchestrator)

-   **Purpose:** The "brain" of the system.
-   **Responsibilities:**
    -   Fetches market data and sentiment at the start of the day.
    -   Uses GPT to determine the daily trading strategy.
    -   Writes the daily plan to the `gpt_runner_daily_plan` collection in Firestore.
    -   Initiates and monitors the trading pods.

#### b. Trading Pods (Stock, Options, Futures)

-   **Purpose:** Execute trades for a specific asset class.
-   **Responsibilities:**
    -   Starts up and waits for the daily plan from Firestore.
    -   Loads the specified trading strategy (e.g., VWAP).
    -   Fetches real-time market data from Kite Connect.
    -   Executes paper or live trades based on strategy signals.
    -   Logs all actions to the `enhanced_logging` system (Firestore/GCS).

#### c. Dashboard (Streamlit + FastAPI)

-   **Purpose:** Provide a user interface for monitoring the system.
-   **Components:**
    -   **Frontend (`tron-frontend-simple`):** A Streamlit application that visualizes data.
    -   **Backend (`temp-backend`):** A FastAPI service that provides APIs for system health, pod status, and trade logs.
    -   **Proxy (`nginx-proxy`):** Routes traffic to the frontend and backend services.
-   **Resilience:** The frontend includes a fallback mechanism to read local data if the backend API is down.

#### d. Data Stores

-   **Firestore:**
    -   Used for real-time, frequently accessed data.
    -   **Collections:**
        -   `gpt_runner_daily_plan`: Stores the daily strategy plan.
        -   `trades`: A log of all executed trades.
        -   `system_logs_realtime`: A collection for high-priority, real-time logs.
-   **Google Cloud Storage (GCS):**
    -   Used for long-term, cost-effective storage.
    -   **Buckets:**
        -   `tron-trade-logs-[DATE]`: Stores detailed, verbose logs from all pods for archival and batch analysis.

### 4. Security Architecture

-   **Authentication:** API keys are required for accessing sensitive endpoints on the FastAPI backend.
-   **Secrets Management:** Kubernetes Secrets are used to store all external API keys (Zerodha, OpenAI, GCP service accounts) and inject them into pods as environment variables.
-   **Network Policies:** (Future) Implement Kubernetes Network Policies to restrict traffic between pods, ensuring pods can only communicate with the services they need.

### 5. Deployment Architecture

-   **Strategy:** GitOps; the state of the GKE cluster is defined by the `.yaml` files in the repository.
-   **Process:**
    1.  A developer pushes a change to a `.yaml` file.
    2.  A CI/CD pipeline (e.g., GitHub Actions) triggers.
    3.  The pipeline runs `kubectl apply -f <changed-file.yaml>` against the GKE cluster.
-   **Environments:** The current setup uses a single `default` namespace. Future work will involve creating `development`, `staging`, and `production` namespaces. 
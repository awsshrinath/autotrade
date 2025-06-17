# Tron Trading System: Enhanced README & Memory Hub

**Last Updated:** 2024-07-16

This README serves as the central memory hub for the Tron Trading System. It provides a high-level overview, current status, and quick links to detailed documentation for developers and AI assistants.

---

### 🎯 Current Status & Priorities

-   **Current Phase:** `Production Hardening & Optimization`
-   **Immediate Focus:** Stabilizing the enhanced logging system and ensuring all trading pods operate flawlessly on GKE.
-   **Active Priorities:**
    -   [x] **Fix Critical Logging Bugs:** Validate and deploy fixes for import path errors, missing logs, and API mismatches.
    -   [ ] **Optimize GKE Deployment:** Continue refining resource limits and high-availability configurations for the minimal trading system.
    -   [ ] **Enhance Dashboard Resilience:** Improve the dashboard's ability to handle backend service outages gracefully.
    -   [ ] **Scale Options & Futures Pods:** Fully integrate and stabilize options and futures trading pods alongside the stock trader.
-   **Blockers:** None at the moment.

---

### 🏗️ Architecture at a Glance

A multi-pod, event-driven trading system deployed on Google Kubernetes Engine (GKE).

-   **Core Logic:** Python
-   **Trading Pods:** Separate deployments for Stocks, Options, and Futures.
-   **Orchestration:** A `main-runner` pod that uses AI to generate daily trading plans and manage other pods.
-   **API Broker:** Zerodha Kite Connect
-   **Database:** Google Firestore (for real-time data, trades, and plans)
-   **Log Storage:** Google Cloud Storage (GCS) for archival/bulk logs.
-   **Frontend:** Streamlit Dashboard (`dashboard_streamlit_backup`)
-   **Backend API:** FastAPI (`dashboard_api`) for serving data to the dashboard.
-   **AI/LLM:** GPT models via `gpt_runner` for analysis and strategy.
-   **Task Management:** Task Master AI (`.taskmaster/`)

---

### 📋 Active Requirements

-   [ ] **High:** Implement a robust, unified logging framework across all trading pods.
-   [ ] **High:** Ensure the system can execute paper trades for all asset classes (stocks, options, futures) based on AI-generated strategies.
-   [ ] **Medium:** The dashboard must display real-time system health, pod status, and recent trades.
-   [ ] **Medium:** The system must gracefully handle market-off hours by exiting open positions.
-   [ ] **Low:** Implement a CI/CD pipeline for automated testing and deployment.

*For a full list, see [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md).*

---

### 🎨 Coding Patterns We Use

1.  **Enhanced Structured Logging**
    All services use a centralized `enhanced_logging` module to send structured logs to both Firestore (real-time) and GCS (archive).

    ```python
    # runner/stock_runner.py
    from runner.enhanced_logging import create_trading_logger, LogLevel, LogCategory

    enhanced_logger = create_trading_logger(session_id="stock_trader_123", bot_type="stock-trader")

    enhanced_logger.log_event(
        "Trade signal received",
        LogLevel.INFO,
        LogCategory.STRATEGY,
        data={'symbol': 'RELIANCE', 'signal': 'BUY'},
        source="vwap_strategy"
    )
    ```

2.  **Kubernetes Deployment Manifests**
    All applications are deployed via `.yaml` files, defining services, deployments, resource limits, and environment variables.

    ```yaml
    # simple-trading-pods.yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: stock-trader-simple
    spec:
      replicas: 1
      template:
        spec:
          containers:
          - name: stock-trader
            image: gcr.io/your-project/tron-trader:latest
            env:
            - name: TRADING_TYPE
              value: "stock"
            - name: PAPER_TRADE
              value: "true"
    ```

3.  **AI-Driven Daily Planning**
    The `main-runner` pod analyzes market sentiment and generates a daily plan, which it stores in Firestore for the trading pods to retrieve.

    ```python
    # runner/main_runner.py
    plan = {
        "stocks": ("vwap", {"atr_multiplier": 2.0}),
        "options": ("scalp", {"strike_distance": 1}),
        "mode": "paper",
        "timestamp": datetime.datetime.now().isoformat(),
    }
    firestore_client.db.collection("gpt_runner_daily_plan").document(today_date).set(plan)
    ```

*For more, see [docs/PATTERNS.md](docs/PATTERNS.md).*

---

### 🚨 Known Issues & Workarounds

-   **Issue:** `CrashLoopBackOff` on initial pod deployment.
    -   **Workaround:** Check pod logs (`kubectl logs <pod-name>`) for import errors or missing environment variables. Often caused by incorrect image tags or missing secrets.
-   **Issue:** Dashboard shows "API unavailable".
    -   **Workaround:** Ensure the `temp-backend` or `dashboard-api` pod is running and the `nginx-proxy` is correctly routing traffic. The dashboard has a local fallback mode for limited functionality.

*For more, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).*

---

### 📚 Quick Reference Links

-   [**Detailed Requirements**](docs/REQUIREMENTS.md)
-   [**System Architecture**](docs/ARCHITECTURE.md)
-   [**Coding Patterns**](docs/PATTERNS.md)
-   [**Architectural Decisions**](docs/DECISIONS.md)
-   [**Development Setup**](docs/SETUP.md)
-   [**Troubleshooting Guide**](docs/TROUBLESHOOTING.md)

---

### 🚀 Getting Started

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Tron
    ```
2.  **Set up environment:**
    -   Ensure you have `gcloud`, `kubectl`, and `docker` installed and configured.
    -   Create a `.env` file from `.env.example` and populate it with your Zerodha and GCP credentials.
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Deploy to GKE:**
    ```bash
    # Apply the minimal system first
    kubectl apply -f minimal-trading-system.yaml
    ```

*For detailed instructions, see [docs/SETUP.md](docs/SETUP.md).*

---

### 📝 Recent Updates

-   **2024-07-16:**
    -   **FIX:** Corrected critical logging import paths and parameter mismatches across all trading pods.
    -   **FEAT:** Implemented enhanced structured logging to Firestore and GCS.
    -   **FEAT:** Added dashboard resilience with a local data fallback mode.
-   **2024-07-15:**
    -   **FEAT:** Deployed initial minimal trading system on GKE.
    -   **TASK:** Cleaned up unnecessary pods to optimize resource usage.

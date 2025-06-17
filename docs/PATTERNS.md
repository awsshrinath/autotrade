# Tron Trading System: Coding Patterns & Standards

**Last Updated:** 2024-07-16

This document outlines the established coding patterns, conventions, and standards for the Tron Trading System to ensure consistency, maintainability, and quality.

---

### 1. File and Folder Naming Conventions

-   **Folders:** `snake_case` (e.g., `stock_trading`, `futures_trading`).
-   **Python Files:** `snake_case.py` (e.g., `stock_runner.py`, `kiteconnect_manager.py`).
-   **Kubernetes Manifests:** `kebab-case.yaml` (e.g., `minimal-trading-system.yaml`).
-   **Documentation:** `UPPERCASE.md` (e.g., `README.md`, `ARCHITECTURE.md`).

---

### 2. Python Code Structure

-   **Imports:** Group imports in the following order:
    1.  Standard library imports (`os`, `sys`, `datetime`).
    2.  Third-party library imports (`requests`, `pytz`).
    3.  Project-specific imports (`from runner.logger import Logger`).
-   **Path Manipulation:** The project root must be added to `sys.path` at the very beginning of any entry-point script to ensure consistent module resolution.
    ```python
    # stock_trading/stock_runner.py
    import os
    import sys

    # Add project root to path BEFORE any other imports
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    import time
    from runner.logger import Logger
    # ... rest of the imports
    ```
-   **Class Structure:** Keep classes focused on a single responsibility.
-   **Functions:** Use type hints for function arguments and return values.

---

### 3. Logging Pattern

-   **Standard:** Use the `enhanced_logging` module for all logging.
-   **Dual Destination:** Logs are sent to Firestore for real-time viewing and GCS for long-term archival.
-   **Structured Data:** All log entries must be structured with consistent fields (`log_level`, `category`, `bot_type`, `data`, `source`).

    ```python
    # from runner.enhanced_logging import create_trading_logger, LogLevel, LogCategory

    enhanced_logger.log_event(
        "Trade execution failed",
        LogLevel.ERROR,
        LogCategory.TRADE,
        data={
            'symbol': 'RELIANCE',
            'order_type': 'BUY',
            'error_message': str(e)
        },
        source="trade_manager"
    )
    ```

### 4. Error Handling Pattern

-   **Graceful Fallbacks:** When a critical service (like a backend API or a database) is unavailable, the application should fall back to a safe mode of operation. For example, the dashboard uses local data when the API is down.
-   **Specific Exceptions:** Catch specific exceptions rather than generic `Exception`.
-   **Comprehensive Logging:** Always log the full exception details in the `except` block.

    ```python
    # dashboard_streamlit_backup/data/system_data_provider.py
    try:
        response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Fallback to local log reading when API is not available
        return self._get_local_fallback_data(endpoint, str(e))
    ```

---

### 5. API Response Pattern (FastAPI Backend)

-   **Standard Success Response:**
    ```json
    {
      "status": "success",
      "data": {
        "key": "value"
      }
    }
    ```
-   **Standard Error Response:**
    ```json
    {
      "status": "error",
      "message": "A descriptive error message.",
      "details": { ... } // Optional
    }
    ```

---

### 6. Configuration Management

-   **Environment Variables:** All configuration that varies between environments (dev, prod) or contains secrets (API keys) MUST be managed via environment variables.
-   **Kubernetes Injection:** In production, these are injected into pods from Kubernetes Secrets and ConfigMaps.
-   **Access in Code:** Use `os.getenv("VARIABLE_NAME", "default_value")`.

    ```python
    # runner/main_runner.py
    PAPER_TRADE = os.getenv("PAPER_TRADE", "true").lower() == "true"
    ```

---

### 7. Code Review Checklist

-   [ ] Does the code adhere to the naming conventions?
-   [ ] Are all new functions and classes documented with docstrings?
-   [ ] Is the enhanced logging pattern used for all significant events?
-   [ ] Is error handling specific and robust?
-   [ ] Are secrets and configurations handled via environment variables?
-   [ ] Are there corresponding updates to documentation if the change affects architecture or requirements?
-   [ ] Are all dependencies added to `requirements.txt`? 
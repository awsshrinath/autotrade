# Deployment Guide: Tron Dashboard (Backend + Frontend)

This guide provides the instructions to run the re-architected Tron Dashboard, which consists of two main components:
1.  **FastAPI Backend:** Handles all data processing and external connections.
2.  **Streamlit Frontend:** Provides the user interface.

Both components must be running simultaneously for the dashboard to be fully functional.

---

## 1. Running the Backend (FastAPI)

The backend server is the data engine for the dashboard.

### Prerequisites

-   Ensure all required runner components and authentications (e.g., GCP, Kite) are correctly configured in your environment. The backend relies on these to function.
-   Python 3.8+

### Steps

1.  **Navigate to the backend directory:**
    ```bash
    cd dashboard_api
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the server:**
    ```bash
    python main.py
    ```

The backend API will now be running and accessible at `http://localhost:8000`. You can visit this URL in your browser to see the welcome message.

---

## 2. Running the Frontend (Streamlit)

The frontend provides the user interface you interact with.

### Prerequisites

-   Python 3.8+
-   The backend API must be running.

### Steps

1.  **Navigate to the dashboard directory from the project root:**
    ```bash
    cd dashboard
    ```

2.  **Create a virtual environment (recommended, if not using a global one):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Streamlit app:**
    ```bash
    streamlit run main.py
    ```

The Streamlit dashboard will now be running and accessible at the URL provided in your terminal, typically `http://localhost:8501`. It will automatically connect to the backend API running on port 8000. 
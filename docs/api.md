# Tron Trading System API Documentation

This document provides an overview of the API endpoints available in the Tron trading system. The API is built using FastAPI, which provides automatic, interactive documentation.

## Accessing the API Documentation

Once the `gpt_runner` application is running, you can access the interactive API documentation at the following endpoints:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Main Endpoints

The API is organized into several routers, each handling a specific area of functionality.

### Market Data (`/api/v1/market`)

This router provides access to real-time and historical market data.

- `GET /api/v1/market/regime/{instrument_id}`: Get the current market regime for an instrument.
- `GET /api/v1/market/latest_candle/{instrument_token}`: Get the latest candle data for an instrument.
- `GET /api/v1/market/correlation`: Get the market correlation matrix.

### Log Aggregation (`/api/v1/logs`)

This set of routers is used to aggregate logs from various sources.

- `GET /api/v1/logs/gcs`: Access logs from Google Cloud Storage.
- `GET /api/v1/logs/firestore`: Access logs from Firestore.
- `GET /api/v1/logs/k8s`: Access logs from Kubernetes.

### Summary (`/api/v1/summary`)

This router provides log summarization capabilities.

---

For detailed information about each endpoint, including request parameters, response models, and examples, please refer to the interactive documentation linked above. 
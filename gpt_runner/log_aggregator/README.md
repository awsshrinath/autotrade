# GPT Runner Log Aggregator Service

A unified log monitoring system for the GPT Runner+ project that centralizes log collection from multiple sources and serves them through a FastAPI-based service.

## Overview

This service aggregates logs from:
- **GCS buckets**: trades/, reflections/, strategies/ directories
- **Firestore collections**: gpt_runner_trades, gpt_runner_reflections
- **GKE pods**: Using Kubernetes API or Cloud Logging API

## Features

- RESTful API endpoints for log retrieval and filtering
- GPT-powered log summarization
- Real-time log monitoring capabilities
- Authentication and authorization
- Caching for performance optimization
- Integration with existing Streamlit dashboard

## API Endpoints

### Core Endpoints
- `GET /logs/gcs` - Retrieve logs from GCS buckets
- `GET /logs/firestore` - Retrieve logs from Firestore collections
- `GET /logs/pods` - Retrieve logs from Kubernetes pods
- `POST /logs/summary` - Generate GPT-powered log summaries

### Utility Endpoints
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics endpoint

## Quick Start

### Prerequisites
- Python 3.9+
- Access to GCP services (GCS, Firestore, GKE)
- Kubernetes cluster access (for pod logs)
- OpenAI API key (for summarization)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export OPENAI_API_KEY="your-openai-api-key"
export LOG_AGGREGATOR_SECRET_KEY="your-secret-key"
```

3. Run the service:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

Configuration is managed through environment variables:

### Required
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to GCP service account JSON
- `OPENAI_API_KEY` - OpenAI API key for log summarization
- `LOG_AGGREGATOR_SECRET_KEY` - Secret key for JWT authentication

### Optional
- `GCS_BUCKET_NAME` - Default GCS bucket name
- `FIRESTORE_PROJECT_ID` - Firestore project ID
- `KUBERNETES_NAMESPACE` - Default Kubernetes namespace
- `REDIS_URL` - Redis connection URL for caching
- `LOG_LEVEL` - Logging level (default: INFO)

## Architecture

```
log_aggregator/
├── main.py                 # FastAPI application entry point
├── routers/                # API endpoint routers
│   ├── gcs_logs.py        # GCS log endpoints
│   ├── firestore_logs.py  # Firestore log endpoints
│   ├── pod_logs.py        # Kubernetes pod log endpoints
│   └── summary.py         # GPT summarization endpoints
├── services/              # Business logic services
│   ├── gcs_service.py     # GCS integration
│   ├── firestore_service.py # Firestore integration
│   ├── k8s_service.py     # Kubernetes integration
│   └── gpt_service.py     # GPT summarization
├── models/                # Pydantic models
│   └── log_models.py      # Request/response schemas
└── utils/                 # Utility modules
    ├── auth.py           # Authentication utilities
    ├── cache.py          # Caching utilities
    └── config.py         # Configuration management
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
flake8 .
```

### Docker Build
```bash
docker build -t gpt-runner-log-aggregator .
```

## Deployment

The service is designed to be deployed as a Kubernetes pod in GKE. See the deployment manifests in the `deployments/` directory.

## Monitoring

- Health checks available at `/health`
- Prometheus metrics at `/metrics`
- Structured logging with correlation IDs
- Performance monitoring for API endpoints

## Security

- JWT-based authentication for API endpoints
- Role-based access control
- Secure handling of sensitive log data
- Rate limiting and request validation

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation for API changes
4. Follow Python PEP 8 style guidelines 
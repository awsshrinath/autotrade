"""
GPT Runner Log Aggregator Service

A unified log monitoring system that centralizes logs from:
- GCS buckets (trades/, reflections/, strategies/)
- Firestore collections (gpt_runner_trades, gpt_runner_reflections)
- GKE pods (using Kubernetes API or Logging API)
"""

__version__ = "1.0.0"
__author__ = "GPT Runner Team"
__description__ = "Unified log monitoring and aggregation service for GPT Runner+" 
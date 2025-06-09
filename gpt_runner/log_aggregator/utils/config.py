"""
Configuration management for the log aggregator service.
Handles environment variables, settings, and application configuration.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LogAggregatorConfig(BaseSettings):
    """Configuration settings for the log aggregator service."""
    
    # GCP Configuration
    google_application_credentials: Optional[str] = Field(
        default=None,
        env="GOOGLE_APPLICATION_CREDENTIALS",
        description="Path to GCP service account JSON file"
    )
    firestore_project_id: Optional[str] = Field(
        default=None,
        env="FIRESTORE_PROJECT_ID",
        description="GCP project ID for Firestore"
    )
    gcs_bucket_name: Optional[str] = Field(
        default=None,
        env="GCS_BUCKET_NAME",
        description="Default GCS bucket name for log retrieval"
    )
    
    # Kubernetes Configuration
    kubernetes_namespace: str = Field(
        default="default",
        env="KUBERNETES_NAMESPACE",
        description="Default Kubernetes namespace"
    )
    kubernetes_config_path: Optional[str] = Field(
        default=None,
        env="KUBERNETES_CONFIG_PATH",
        description="Path to Kubernetes config file"
    )
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(
        default=None,
        env="OPENAI_API_KEY",
        description="OpenAI API key for GPT summarization"
    )
    openai_model: str = Field(
        default="gpt-3.5-turbo",
        env="OPENAI_MODEL",
        description="OpenAI model to use for summarization"
    )
    openai_max_tokens: int = Field(
        default=1000,
        env="OPENAI_MAX_TOKENS",
        description="Maximum tokens for OpenAI responses"
    )
    openai_temperature: float = Field(
        default=0.3,
        env="OPENAI_TEMPERATURE",
        description="Temperature for OpenAI responses"
    )
    openai_timeout: int = Field(
        default=30,
        env="OPENAI_TIMEOUT",
        description="Timeout for OpenAI API calls in seconds"
    )
    
    # Security Configuration
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="LOG_AGGREGATOR_SECRET_KEY",
        description="Secret key for JWT signing"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        env="JWT_ALGORITHM",
        description="JWT algorithm for token signing"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="JWT token expiration time in minutes"
    )
    

    
    # Application Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    api_host: str = Field(
        default="0.0.0.0",
        env="API_HOST",
        description="API host address"
    )
    api_port: int = Field(
        default=8000,
        env="API_PORT",
        description="API port number"
    )
    workers: int = Field(
        default=1,
        env="WORKERS",
        description="Number of worker processes"
    )
    
    # Performance Configuration
    max_log_entries: int = Field(
        default=1000,
        env="MAX_LOG_ENTRIES",
        description="Maximum number of log entries to return"
    )
    default_page_size: int = Field(
        default=50,
        env="DEFAULT_PAGE_SIZE",
        description="Default page size for pagination"
    )
    max_page_size: int = Field(
        default=500,
        env="MAX_PAGE_SIZE",
        description="Maximum page size for pagination"
    )
    
    # GPT Summarization Configuration
    max_tokens_for_summary: int = Field(
        default=500,
        env="MAX_TOKENS_FOR_SUMMARY",
        description="Maximum tokens for GPT summary"
    )
    summary_model: str = Field(
        default="gpt-4o-mini",
        env="SUMMARY_MODEL",
        description="GPT model for summarization"
    )
    summary_temperature: float = Field(
        default=0.3,
        env="SUMMARY_TEMPERATURE",
        description="Temperature for GPT summarization"
    )
    
    # GCS Log Prefixes
    gcs_log_prefixes: List[str] = Field(
        default=["trades/", "reflections/", "strategies/"],
        description="GCS bucket prefixes to monitor for logs"
    )
    
    # Firestore Collections
    firestore_collections: List[str] = Field(
        default=["gpt_runner_trades", "gpt_runner_reflections"],
        description="Firestore collections to monitor for logs"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global configuration instance
config = LogAggregatorConfig()


def get_config() -> LogAggregatorConfig:
    """Get the global configuration instance."""
    return config


def validate_config() -> bool:
    """Validate that required configuration is present."""
    errors = []
    warnings = []
    
    # Check required GCP configuration (optional in some deployments)
    if not config.google_application_credentials:
        warnings.append("GOOGLE_APPLICATION_CREDENTIALS not set - GCP features may be limited")
    
    if not config.firestore_project_id:
        warnings.append("FIRESTORE_PROJECT_ID not set - Firestore logs unavailable")
    
    if not config.gcs_bucket_name:
        warnings.append("GCS_BUCKET_NAME not set - GCS logs unavailable")
    
    # Check OpenAI configuration for summarization (auto-pulls from environment)
    if not config.openai_api_key:
        warnings.append("OPENAI_API_KEY not found in environment - AI summarization disabled")
    else:
        print(f"✅ OpenAI API key loaded from environment (key: {config.openai_api_key[:15]}...)")
    
    # Check security configuration
    if config.secret_key == "your-secret-key-change-in-production":
        warnings.append("LOG_AGGREGATOR_SECRET_KEY should be changed from default")
    
    # Display warnings but don't fail validation
    if warnings:
        print("Configuration warnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    
    # Only fail on critical errors
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  ❌ {error}")
        return False
    
    return True


def get_gcs_bucket_name() -> str:
    """Get the GCS bucket name with fallback."""
    return config.gcs_bucket_name or "default-bucket"


def get_firestore_project_id() -> str:
    """Get the Firestore project ID with fallback."""
    return config.firestore_project_id or "default-project"





def get_log_prefixes() -> List[str]:
    """Get the list of GCS log prefixes to monitor."""
    return config.gcs_log_prefixes


def get_firestore_collections() -> List[str]:
    """Get the list of Firestore collections to monitor."""
    return config.firestore_collections 
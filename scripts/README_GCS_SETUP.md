# GCS Bucket Setup Guide

This guide explains how to use the `create_gcs_buckets.sh` script to set up Google Cloud Storage buckets for the TRON trading system.

## Prerequisites

1. **Google Cloud SDK installed**
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   ```

2. **Authentication**
   ```bash
   # Login to your Google account
   gcloud auth login
   
   # Set your project (replace with your project ID)
   gcloud config set project autotrade-453303
   ```

3. **Required APIs enabled**
   ```bash
   # Enable Cloud Storage API
   gcloud services enable storage.googleapis.com
   
   # Enable Cloud Resource Manager API (for project validation)
   gcloud services enable cloudresourcemanager.googleapis.com
   ```

4. **Permissions required**
   - `storage.buckets.create`
   - `storage.buckets.get`
   - `storage.buckets.list`
   - `storage.buckets.update`

## Usage

### Basic Usage (Production Environment)

```bash
# Use current gcloud project and default settings
./scripts/create_gcs_buckets.sh
```

### Advanced Usage

```bash
# Specify project ID
./scripts/create_gcs_buckets.sh -p autotrade-453303

# Set different region
./scripts/create_gcs_buckets.sh -r us-central1

# Create buckets for staging environment
./scripts/create_gcs_buckets.sh -e staging

# Combine options
./scripts/create_gcs_buckets.sh -p autotrade-453303 -r asia-south1 -e dev
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-p, --project` | GCP Project ID | Current gcloud project |
| `-r, --region` | GCS Region | `asia-south1` |
| `-e, --env` | Environment (dev/staging/prod) | `prod` |
| `-h, --help` | Show help message | - |

## Created Buckets

The script creates the following buckets:

### Production Environment (no prefix)
- `tron-trading-logs` - Daily trading bot logs and error reports (90-day retention)
- `tron-trade-data` - Historical trade execution data (7-year retention for regulatory compliance)
- `tron-strategy-configs` - Trading strategy configurations and parameters
- `tron-cognitive-memory` - Compressed cognitive memory snapshots
- `tron-thought-archives` - Daily thought journal data (1-year retention)
- `tron-analysis-reports` - Performance attribution and learning analysis reports
- `tron-memory-backups` - Disaster recovery backups (6-month retention, versioning enabled)
- `tron-model-artifacts` - ML model artifacts and training data (versioning enabled)
- `tron-market-data` - Market data cache (30-day retention)

### Development/Staging Environment (with prefix)
Same buckets but prefixed with `dev-` or `staging-`

## Lifecycle Policies

The script automatically sets up lifecycle policies for cost optimization:

| Bucket Type | Retention Period | Notes |
|-------------|------------------|-------|
| Trading Logs | 90 days | Automatic deletion after 3 months |
| Trade Data | 7 years | Regulatory compliance requirement |
| Thought Archives | 1 year | Cognitive system data |
| Memory Backups | 6 months | With versioning enabled |
| Market Data | 30 days | Cache data, frequently refreshed |
| Model Artifacts | No limit | With versioning for rollbacks |

## Security Features

- **Uniform bucket-level access** - Simplified permission management
- **Public access prevention** - Blocks accidental public exposure
- **Versioning** - Enabled for critical buckets (backups, model artifacts)

## Verification

After running the script, verify the setup:

```bash
# List all buckets in your project
gsutil ls -p autotrade-453303

# Check specific bucket details
gsutil ls -L -b gs://tron-trading-logs

# View lifecycle policy
gsutil lifecycle get gs://tron-trading-logs

# Check bucket size and usage
gsutil du -sh gs://tron-trading-logs
```

## Environment Variables

After successful creation, set these environment variables:

```bash
export GCP_PROJECT_ID=autotrade-453303
export GCS_REGION=asia-south1
export ENVIRONMENT=prod
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Check your permissions
   gcloud projects get-iam-policy autotrade-453303
   
   # Ensure you have the Storage Admin role
   gcloud projects add-iam-policy-binding autotrade-453303 \
     --member="user:your-email@gmail.com" \
     --role="roles/storage.admin"
   ```

2. **Billing Not Enabled**
   ```bash
   # Check billing status
   gcloud billing projects describe autotrade-453303
   ```

3. **API Not Enabled**
   ```bash
   # Enable required APIs
   gcloud services enable storage.googleapis.com
   gcloud services enable cloudresourcemanager.googleapis.com
   ```

4. **Bucket Already Exists (Different Project)**
   - Bucket names are globally unique
   - Try a different region or add a unique suffix

### Debug Mode

Run with debug output:
```bash
bash -x ./scripts/create_gcs_buckets.sh -p autotrade-453303
```

## Cost Optimization

1. **Monitor Usage**
   ```bash
   # Check bucket sizes
   gsutil du -sh gs://tron-*
   
   # Monitor costs in GCP Console
   # Navigation: Billing > Reports > Filter by Cloud Storage
   ```

2. **Lifecycle Management**
   ```bash
   # View current lifecycle policies
   gsutil lifecycle get gs://bucket-name
   
   # Update lifecycle policy if needed
   gsutil lifecycle set lifecycle.json gs://bucket-name
   ```

3. **Storage Classes**
   - Standard: For frequently accessed data
   - Nearline: For data accessed less than once per month
   - Coldline: For data accessed less than once per quarter
   - Archive: For data accessed less than once per year

## Integration with Kubernetes

Update your Kubernetes deployments to use these buckets:

```yaml
env:
- name: GCS_TRADING_LOGS_BUCKET
  value: "tron-trading-logs"
- name: GCS_TRADE_DATA_BUCKET
  value: "tron-trade-data"
- name: GCS_STRATEGY_CONFIGS_BUCKET
  value: "tron-strategy-configs"
```

## Backup and Disaster Recovery

The script sets up automatic backups:

1. **Memory Backups Bucket** - Versioning enabled for point-in-time recovery
2. **Cross-Region Replication** - Consider setting up for critical data
3. **Regular Exports** - Automate exports to other storage systems

## Next Steps

1. Update your application configuration to use the new buckets
2. Set up monitoring and alerting for bucket usage
3. Configure backup schedules for critical data
4. Review and adjust lifecycle policies based on usage patterns
5. Set up cost budgets and alerts in GCP Console

## Support

For issues with the script:
1. Check the troubleshooting section above
2. Review GCP documentation for Cloud Storage
3. Check GCP Console for detailed error messages
4. Ensure all prerequisites are met 
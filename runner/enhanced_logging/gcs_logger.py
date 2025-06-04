"""
GCS Logger - Bulk storage and archival for long-term analysis
=============================================================

Optimized for:
- Trade entry/exit logs (JSON/CSV)
- Historical GPT reflections and system performance metrics
- Archived detailed logs and debug traces
- Long-term data analysis and compliance

Cost optimization:
- Batched uploads to minimize operations
- Compressed storage (gzip)
- Structured folder organization
- Lifecycle policies for automatic cleanup
- Version tagging for deduplication
"""

import datetime
import json
import gzip
import csv
import io
import os
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from google.cloud import storage
from .log_types import LogEntry, LogType, TradeLogData, CognitiveLogData, ErrorLogData


class GCSBuckets:
    """GCS bucket names organized by purpose"""
    
    TRADE_LOGS = "tron-trade-logs"                    # Trade entry/exit logs
    COGNITIVE_ARCHIVES = "tron-cognitive-archives"    # Historical cognitive data
    SYSTEM_LOGS = "tron-system-logs"                  # System performance and debug logs
    ANALYTICS_DATA = "tron-analytics-data"            # Processed data for analysis
    COMPLIANCE_LOGS = "tron-compliance-logs"          # Regulatory compliance data


class GCSLogger:
    """Optimized GCS logger for bulk storage and archival"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id
        self.client = storage.Client(project=project_id)
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.year = datetime.datetime.now().strftime("%Y")
        self.month = datetime.datetime.now().strftime("%m")
        self.day = datetime.datetime.now().strftime("%d")
        
        # Batch operations for efficiency
        self.batch_size = 100
        self.pending_uploads = {}  # bucket -> [data]
        self.last_flush_time = time.time()
        self.flush_interval = 60  # seconds
        
        # Version tracking for deduplication
        self.version_tracker = {}
        
        # Ensure buckets exist with lifecycle policies
        self._ensure_buckets_with_lifecycle()
    
    def _ensure_buckets_with_lifecycle(self):
        """Ensure buckets exist with proper lifecycle policies in asia-south1 region"""
        buckets_config = {
            GCSBuckets.TRADE_LOGS: {
                'lifecycle_days': 365,  # 1 year retention
                'storage_class': 'STANDARD'
            },
            GCSBuckets.COGNITIVE_ARCHIVES: {
                'lifecycle_days': 180,  # 6 months retention
                'storage_class': 'NEARLINE'
            },
            GCSBuckets.SYSTEM_LOGS: {
                'lifecycle_days': 90,   # 3 months retention
                'storage_class': 'COLDLINE'
            },
            GCSBuckets.ANALYTICS_DATA: {
                'lifecycle_days': 730,  # 2 years retention
                'storage_class': 'STANDARD'
            },
            GCSBuckets.COMPLIANCE_LOGS: {
                'lifecycle_days': 2555, # 7 years retention (regulatory)
                'storage_class': 'ARCHIVE'
            }
        }
        
        for bucket_name, config in buckets_config.items():
            try:
                bucket = self.client.bucket(bucket_name)
                
                # Check if bucket exists first
                bucket_exists = bucket.exists()
                
                if not bucket_exists:
                    # Create bucket in asia-south1 region (labels set separately)
                    try:
                        # FIXED: Create bucket without labels parameter
                        bucket = self.client.create_bucket(
                            bucket_name, 
                            location='asia-south1'  # Force asia-south1 region
                        )
                        
                        # FIXED: Set labels after bucket creation
                        bucket.labels = {
                            'environment': 'production',
                            'system': 'tron-trading',
                            'purpose': bucket_name.split('-')[-1],  # e.g., 'logs', 'archives'
                            'region': 'asia-south1'
                        }
                        bucket.patch()  # Apply the labels
                        
                        print(f"✅ Created GCS bucket: {bucket_name} in asia-south1")
                    except Exception as create_error:
                        print(f"❌ Failed to create bucket {bucket_name}: {create_error}")
                        continue
                else:
                    # Bucket exists, check region and handle appropriately
                    try:
                        bucket.reload()
                        current_region = bucket.location.upper() if bucket.location else 'UNKNOWN'
                        
                        if current_region == 'US':
                            # Existing US bucket - this is the problem we need to address
                            print(f"⚠️ REGION ISSUE: Bucket {bucket_name} is in US region (needs asia-south1)")
                            print(f"   SOLUTION: Consider recreating bucket in asia-south1:")
                            print(f"   1. Export data: gsutil -m cp -r gs://{bucket_name}/* /local/backup/")
                            print(f"   2. Delete bucket: gsutil rm -r gs://{bucket_name}")
                            print(f"   3. Let system recreate in asia-south1")
                            print(f"   4. Restore data: gsutil -m cp -r /local/backup/* gs://{bucket_name}/")
                            print(f"   OR use gsutil to move bucket region (if supported)")
                            
                            # For now, continue with existing US bucket but flag it
                            self._mark_bucket_for_migration(bucket_name, current_region)
                            
                        elif current_region == 'ASIA-SOUTH1':
                            # Perfect region
                            print(f"✅ Bucket {bucket_name} already in asia-south1")
                        else:
                            # Other region
                            print(f"⚠️ Bucket {bucket_name} is in {current_region} (expected asia-south1)")
                    except Exception as reload_error:
                        print(f"❌ Could not check region for {bucket_name}: {reload_error}")
                
                # Set lifecycle policy only if bucket exists and we can modify it
                try:
                    # Check if lifecycle rules already exist
                    existing_rules = bucket.lifecycle_rules
                    
                    # Only set lifecycle policy if it doesn't exist or is different
                    needs_lifecycle_update = True
                    if existing_rules:
                        for rule in existing_rules:
                            if (rule.action.get('type') == 'Delete' and 
                                rule.condition.get('age') == config['lifecycle_days']):
                                needs_lifecycle_update = False
                                break
                    
                    if needs_lifecycle_update:
                        # Set lifecycle policy
                        lifecycle_rule = {
                            'action': {'type': 'Delete'},
                            'condition': {'age': config['lifecycle_days']}
                        }
                        
                        # Transition to cheaper storage classes after 30 days
                        transition_rule = {
                            'action': {
                                'type': 'SetStorageClass',
                                'storageClass': config['storage_class']
                            },
                            'condition': {'age': 30}
                        }
                        
                        bucket.lifecycle_rules = [lifecycle_rule, transition_rule]
                        bucket.patch()
                        
                        print(f"✅ Set lifecycle policy for {bucket_name}: {config['lifecycle_days']} days retention")
                        
                except Exception as lifecycle_error:
                    print(f"❌ Could not set lifecycle policy for {bucket_name}: {lifecycle_error}")
                
            except Exception as e:
                print(f"❌ Error setting up bucket {bucket_name}: {e}")
                # Continue with other buckets even if one fails
    
    def _mark_bucket_for_migration(self, bucket_name: str, current_region: str):
        """Mark bucket for region migration"""
        # Store migration info for later processing
        if not hasattr(self, 'buckets_needing_migration'):
            self.buckets_needing_migration = {}
        
        self.buckets_needing_migration[bucket_name] = {
            'current_region': current_region,
            'target_region': 'asia-south1',
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get status of buckets that need region migration"""
        if not hasattr(self, 'buckets_needing_migration'):
            return {}
        return self.buckets_needing_migration
    
    def create_bucket_migration_script(self, output_file: str = "migrate_buckets.sh") -> str:
        """Create a shell script to migrate buckets to asia-south1"""
        if not hasattr(self, 'buckets_needing_migration') or not self.buckets_needing_migration:
            return "No buckets need migration"
        
        script_content = """#!/bin/bash
# GCS Bucket Migration Script - Move from US to asia-south1
# Generated automatically by TRON Trading System

set -e  # Exit on any error

echo "🚀 Starting GCS bucket migration to asia-south1..."
echo "⚠️  IMPORTANT: This will temporarily disrupt logging!"
echo "📋 Buckets to migrate:"
"""
        
        for bucket_name, info in self.buckets_needing_migration.items():
            script_content += f'echo "   - {bucket_name} ({info["current_region"]} → {info["target_region"]})"\n'
        
        script_content += """
echo ""
read -p "Continue with migration? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "Migration cancelled"
    exit 1
fi

# Create backup directory
BACKUP_DIR="/tmp/gcs_migration_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📁 Backup directory: $BACKUP_DIR"

"""
        
        for bucket_name in self.buckets_needing_migration.keys():
            script_content += f"""
echo "🔄 Migrating {bucket_name}..."

# 1. Backup existing data
echo "  📥 Backing up {bucket_name}..."
gsutil -m cp -r "gs://{bucket_name}/*" "$BACKUP_DIR/{bucket_name}/" || echo "  ⚠️  No data to backup in {bucket_name}"

# 2. Delete old bucket
echo "  🗑️  Deleting old {bucket_name}..."
gsutil rm -r "gs://{bucket_name}"

# 3. Wait a moment for propagation
sleep 5

# 4. Recreate bucket in asia-south1 (system will handle this automatically)
echo "  ✨ {bucket_name} will be recreated in asia-south1 on next application start"

# 5. Restore data if backup exists
if [ "$(ls -A $BACKUP_DIR/{bucket_name}/ 2>/dev/null)" ]; then
    echo "  📤 Restoring data to {bucket_name}..."
    # Wait for bucket to be recreated by the application
    sleep 10
    gsutil -m cp -r "$BACKUP_DIR/{bucket_name}/*" "gs://{bucket_name}/"
    echo "  ✅ {bucket_name} migration complete"
else
    echo "  ℹ️  No data to restore for {bucket_name}"
fi

"""
        
        script_content += f"""
echo "🎉 Migration complete!"
echo "📁 Backup stored in: $BACKUP_DIR"
echo "🔄 Restart the application to verify all buckets are in asia-south1"
echo "🧹 You can delete the backup after verifying: rm -rf '$BACKUP_DIR'"
"""
        
        # Write script to file
        with open(output_file, 'w') as f:
            f.write(script_content)
        
        # Make executable
        import stat
        os.chmod(output_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        return f"Migration script created: {output_file}"
    
    def _get_blob_path(self, bucket_type: str, file_type: str, bot_type: str = None, 
                      version: str = None) -> str:
        """Generate structured blob path"""
        # Structure: logs/YYYY/MM/DD/bot_type/file_type_version.json.gz
        path_parts = [
            "logs",
            self.year,
            self.month,
            self.day
        ]
        
        if bot_type:
            path_parts.append(bot_type)
        
        # Add timestamp and version for uniqueness
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        filename = f"{file_type}_{timestamp}"
        
        if version:
            filename += f"_v{version}"
        
        filename += ".json.gz"
        path_parts.append(filename)
        
        return "/".join(path_parts)
    
    def _compress_data(self, data: Union[Dict, List, str]) -> bytes:
        """Compress data for efficient storage"""
        if isinstance(data, (dict, list)):
            json_str = json.dumps(data, default=str, separators=(',', ':'))
        else:
            json_str = str(data)
        
        return gzip.compress(json_str.encode('utf-8'))
    
    def _add_to_batch(self, bucket_name: str, blob_path: str, data: bytes):
        """Add upload to batch for efficiency"""
        if bucket_name not in self.pending_uploads:
            self.pending_uploads[bucket_name] = []
        
        self.pending_uploads[bucket_name].append({
            'blob_path': blob_path,
            'data': data
        })
        
        # Auto-flush if batch is full or time interval exceeded
        total_pending = sum(len(uploads) for uploads in self.pending_uploads.values())
        if (total_pending >= self.batch_size or 
            time.time() - self.last_flush_time > self.flush_interval):
            self.flush_batch()
    
    def flush_batch(self):
        """Flush all pending uploads to GCS"""
        if not self.pending_uploads:
            return
        
        for bucket_name, uploads in self.pending_uploads.items():
            try:
                bucket = self.client.bucket(bucket_name)
                
                for upload in uploads:
                    blob = bucket.blob(upload['blob_path'])
                    blob.upload_from_string(
                        upload['data'],
                        content_type='application/gzip',
                        content_encoding='gzip'
                    )
                
                print(f"Uploaded {len(uploads)} files to {bucket_name}")
                
            except Exception as e:
                print(f"Error uploading to {bucket_name}: {e}")
        
        self.pending_uploads.clear()
        self.last_flush_time = time.time()
    
    def archive_trade_logs(self, trades: List[TradeLogData], bot_type: str):
        """Archive trade logs in both JSON and CSV formats"""
        # JSON format for detailed data
        json_data = [trade.to_dict() for trade in trades]
        compressed_json = self._compress_data(json_data)
        
        json_path = self._get_blob_path(
            GCSBuckets.TRADE_LOGS, 
            "trades_detailed", 
            bot_type,
            self._get_version("trades", bot_type)
        )
        
        self._add_to_batch(GCSBuckets.TRADE_LOGS, json_path, compressed_json)
        
        # CSV format for easy analysis
        csv_buffer = io.StringIO()
        if trades:
            fieldnames = trades[0].to_dict().keys()
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            for trade in trades:
                writer.writerow(trade.to_dict())
        
        csv_data = csv_buffer.getvalue()
        compressed_csv = gzip.compress(csv_data.encode('utf-8'))
        
        csv_path = self._get_blob_path(
            GCSBuckets.TRADE_LOGS, 
            "trades_summary", 
            bot_type,
            self._get_version("trades_csv", bot_type)
        ).replace('.json.gz', '.csv.gz')
        
        self._add_to_batch(GCSBuckets.TRADE_LOGS, csv_path, compressed_csv)
    
    def archive_cognitive_data(self, cognitive_logs: List[CognitiveLogData], bot_type: str):
        """Archive cognitive decision logs"""
        json_data = [log.to_dict() for log in cognitive_logs]
        compressed_data = self._compress_data(json_data)
        
        blob_path = self._get_blob_path(
            GCSBuckets.COGNITIVE_ARCHIVES,
            "cognitive_decisions",
            bot_type,
            self._get_version("cognitive", bot_type)
        )
        
        self._add_to_batch(GCSBuckets.COGNITIVE_ARCHIVES, blob_path, compressed_data)
    
    def archive_system_logs(self, log_entries: List[LogEntry], bot_type: str = None):
        """Archive system logs and debug traces"""
        json_data = [entry.to_dict() for entry in log_entries]
        compressed_data = self._compress_data(json_data)
        
        blob_path = self._get_blob_path(
            GCSBuckets.SYSTEM_LOGS,
            "system_logs",
            bot_type,
            self._get_version("system", bot_type or "all")
        )
        
        self._add_to_batch(GCSBuckets.SYSTEM_LOGS, blob_path, compressed_data)
    
    def archive_performance_metrics(self, metrics: Dict[str, Any], bot_type: str):
        """Archive performance metrics for analysis"""
        # Add metadata
        metrics_with_meta = {
            'date': self.today,
            'bot_type': bot_type,
            'timestamp': datetime.datetime.now().isoformat(),
            'metrics': metrics
        }
        
        compressed_data = self._compress_data(metrics_with_meta)
        
        blob_path = self._get_blob_path(
            GCSBuckets.ANALYTICS_DATA,
            "performance_metrics",
            bot_type,
            self._get_version("performance", bot_type)
        )
        
        self._add_to_batch(GCSBuckets.ANALYTICS_DATA, blob_path, compressed_data)
    
    def archive_gpt_reflections(self, reflections: List[Dict[str, Any]], bot_type: str):
        """Archive GPT reflections for historical analysis"""
        compressed_data = self._compress_data(reflections)
        
        blob_path = self._get_blob_path(
            GCSBuckets.COGNITIVE_ARCHIVES,
            "gpt_reflections",
            bot_type,
            self._get_version("reflections", bot_type)
        )
        
        self._add_to_batch(GCSBuckets.COGNITIVE_ARCHIVES, blob_path, compressed_data)
    
    def archive_error_logs(self, errors: List[ErrorLogData], bot_type: str = None):
        """Archive error logs for debugging and compliance"""
        json_data = [error.to_dict() for error in errors]
        compressed_data = self._compress_data(json_data)
        
        # Store in both system logs and compliance logs
        system_path = self._get_blob_path(
            GCSBuckets.SYSTEM_LOGS,
            "error_logs",
            bot_type,
            self._get_version("errors", bot_type or "all")
        )
        
        compliance_path = self._get_blob_path(
            GCSBuckets.COMPLIANCE_LOGS,
            "error_logs",
            bot_type,
            self._get_version("compliance_errors", bot_type or "all")
        )
        
        self._add_to_batch(GCSBuckets.SYSTEM_LOGS, system_path, compressed_data)
        self._add_to_batch(GCSBuckets.COMPLIANCE_LOGS, compliance_path, compressed_data)
    
    def _get_version(self, log_type: str, bot_type: str) -> str:
        """Get version number for deduplication"""
        key = f"{log_type}_{bot_type}_{self.today}"
        
        if key not in self.version_tracker:
            self.version_tracker[key] = 1
        else:
            self.version_tracker[key] += 1
        
        return str(self.version_tracker[key])
    
    # Query and retrieval methods
    
    def list_archived_trades(self, bot_type: str = None, date_range: tuple = None) -> List[str]:
        """List archived trade files"""
        bucket = self.client.bucket(GCSBuckets.TRADE_LOGS)
        prefix = "logs/"
        
        if date_range:
            start_date, end_date = date_range
            # Complex date filtering would need custom implementation
        
        if bot_type:
            prefix += f"*/{bot_type}/"
        
        blobs = bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs if 'trades' in blob.name]
    
    def download_archived_data(self, bucket_name: str, blob_path: str) -> Dict[str, Any]:
        """Download and decompress archived data"""
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            compressed_data = blob.download_as_bytes()
            decompressed_data = gzip.decompress(compressed_data)
            
            return json.loads(decompressed_data.decode('utf-8'))
            
        except Exception as e:
            print(f"Error downloading {blob_path}: {e}")
            return {}
    
    def get_performance_history(self, bot_type: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get performance metrics history"""
        bucket = self.client.bucket(GCSBuckets.ANALYTICS_DATA)
        
        # List performance metric files for the bot
        prefix = f"logs/*/*/{bot_type}/performance_metrics"
        blobs = list(bucket.list_blobs(prefix=prefix))
        
        # Sort by date and limit
        blobs.sort(key=lambda b: b.time_created, reverse=True)
        
        performance_data = []
        for blob in blobs[:days]:
            try:
                data = self.download_archived_data(GCSBuckets.ANALYTICS_DATA, blob.name)
                performance_data.append(data)
            except Exception as e:
                print(f"Error loading performance data from {blob.name}: {e}")
        
        return performance_data
    
    def cleanup_old_versions(self, keep_versions: int = 5):
        """Clean up old versions to save storage costs"""
        for bucket_name in [GCSBuckets.TRADE_LOGS, GCSBuckets.COGNITIVE_ARCHIVES, 
                           GCSBuckets.SYSTEM_LOGS, GCSBuckets.ANALYTICS_DATA]:
            try:
                bucket = self.client.bucket(bucket_name)
                
                # Group blobs by base name (without version)
                blob_groups = {}
                for blob in bucket.list_blobs():
                    # Extract base name without version
                    base_name = blob.name.split('_v')[0] if '_v' in blob.name else blob.name
                    
                    if base_name not in blob_groups:
                        blob_groups[base_name] = []
                    blob_groups[base_name].append(blob)
                
                # Keep only latest versions
                for base_name, blobs in blob_groups.items():
                    if len(blobs) > keep_versions:
                        # Sort by creation time, keep latest
                        blobs.sort(key=lambda b: b.time_created, reverse=True)
                        old_blobs = blobs[keep_versions:]
                        
                        for old_blob in old_blobs:
                            old_blob.delete()
                            print(f"Deleted old version: {old_blob.name}")
                
            except Exception as e:
                print(f"Error cleaning up {bucket_name}: {e}")
    
    def export_data_for_analysis(self, output_format: str = "csv", 
                                date_range: tuple = None) -> str:
        """Export data in analysis-friendly format"""
        # This would implement data export functionality
        # for external analysis tools like BigQuery, Pandas, etc.
        pass
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.flush_batch()
        except:
            pass 
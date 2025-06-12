"""
Log Lifecycle Manager - Automated cleanup and cost optimization
===============================================================

Manages:
- Automatic cleanup of expired data
- Cost optimization through storage transitions
- Version management and deduplication
- Monitoring and alerting for storage costs
"""

import datetime
import time
from typing import Dict, Any, List, Optional
from google.cloud import storage, firestore
from .firestore_logger import FirestoreLogger, FirestoreCollections
from .gcs_logger import GCSLogger, GCSBuckets


class LogLifecycleManager:
    """Manages log lifecycle and cost optimization"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id
        self.firestore_logger = FirestoreLogger(project_id)
        self.gcs_logger = GCSLogger(project_id)
        
        # Lifecycle policies
        self.cleanup_policies = {
            'firestore': {
                'live_trades': 7,        # days
                'live_positions': 7,     # days
                'live_alerts': 7,        # days
                'live_cognitive': 14,    # days
                'system_status': 1,      # days
                'daily_summaries': 30,   # days
                'daily_reflections': 30, # days
                'dashboard_metrics': 30  # days
            },
            'gcs': {
                'versions_to_keep': 5,
                'archive_after_days': 30,
                'delete_after_days': {
                    'trade_logs': 365,
                    'cognitive_archives': 180,
                    'system_logs': 90,
                    'analytics_data': 730,
                    'compliance_logs': 2555
                }
            }
        }
        
        # Cost monitoring thresholds
        self.cost_thresholds = {
            'daily_firestore_writes': 10000,    # Alert if > 10k writes/day
            'daily_gcs_operations': 50000,      # Alert if > 50k ops/day
            'storage_size_gb': 100,              # Alert if > 100GB
            'monthly_cost_usd': 50               # Alert if > $50/month
        }
    
    def run_daily_cleanup(self):
        """Run daily cleanup tasks"""
        print("Starting daily log cleanup...")
        
        # Cleanup Firestore
        self._cleanup_firestore()
        
        # Cleanup GCS versions
        self._cleanup_gcs_versions()
        
        # Archive old data
        self._archive_old_data()
        
        # Monitor costs
        self._monitor_costs()
        
        print("Daily cleanup completed")
    
    def _cleanup_firestore(self):
        """Clean up expired Firestore documents"""
        print("Cleaning up Firestore...")
        
        try:
            # Use built-in TTL cleanup if available
            self.firestore_logger.cleanup_expired_data()
            
            # Manual cleanup for collections without TTL
            self._manual_firestore_cleanup()
            
        except Exception as e:
            print(f"Error in Firestore cleanup: {e}")
    
    def _manual_firestore_cleanup(self):
        """Manual cleanup for collections without automatic TTL"""
        db = self.firestore_logger.db
        now = datetime.datetime.utcnow()
        
        # Cleanup old system status (keep only last 24 hours)
        cutoff_time = now - datetime.timedelta(hours=24)
        
        try:
            old_status_query = (db.collection(FirestoreCollections.LIVE_SYSTEM_STATUS)
                              .where('last_heartbeat', '<', cutoff_time))
            
            old_docs = list(old_status_query.stream())
            if old_docs:
                batch = db.batch()
                for doc in old_docs:
                    batch.delete(doc.reference)
                batch.commit()
                print(f"Cleaned up {len(old_docs)} old system status documents")
                
        except Exception as e:
            print(f"Error cleaning system status: {e}")
    
    def _cleanup_gcs_versions(self):
        """Clean up old GCS file versions"""
        print("Cleaning up GCS versions...")
        
        try:
            self.gcs_logger.cleanup_old_versions(
                keep_versions=self.cleanup_policies['gcs']['versions_to_keep']
            )
        except Exception as e:
            print(f"Error in GCS version cleanup: {e}")
    
    def _archive_old_data(self):
        """Archive data that should move from Firestore to GCS"""
        print("Archiving old data...")
        
        try:
            # Archive old trades from Firestore to GCS
            self._archive_old_trades()
            
            # Archive old cognitive decisions
            self._archive_old_cognitive_data()
            
        except Exception as e:
            print(f"Error in archival process: {e}")
    
    def _archive_old_trades(self):
        """Archive old trades from Firestore to GCS"""
        archive_cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        
        try:
            # Get old trades from Firestore
            db = self.firestore_logger.db
            old_trades_query = (db.collection(FirestoreCollections.LIVE_TRADES)
                              .where('last_updated', '<', archive_cutoff))
            
            old_trades = list(old_trades_query.stream())
            
            if old_trades:
                # Group by bot type for efficient archival
                trades_by_bot = {}
                for trade_doc in old_trades:
                    trade_data = trade_doc.to_dict()
                    bot_type = trade_data.get('bot_type', 'unknown')
                    
                    if bot_type not in trades_by_bot:
                        trades_by_bot[bot_type] = []
                    trades_by_bot[bot_type].append(trade_data)
                
                # Archive each bot's trades
                for bot_type, trades in trades_by_bot.items():
                    from .log_types import TradeLogData
                    trade_objects = []
                    
                    for trade in trades:
                        try:
                            trade_obj = TradeLogData(**trade)
                            trade_objects.append(trade_obj)
                        except Exception as e:
                            print(f"Error converting trade data: {e}")
                    
                    if trade_objects:
                        self.gcs_logger.archive_trade_logs(trade_objects, bot_type)
                
                # Delete archived trades from Firestore
                batch = db.batch()
                for trade_doc in old_trades:
                    batch.delete(trade_doc.reference)
                batch.commit()
                
                print(f"Archived {len(old_trades)} old trades to GCS")
                
        except Exception as e:
            print(f"Error archiving trades: {e}")
    
    def _archive_old_cognitive_data(self):
        """Archive old cognitive decisions from Firestore to GCS"""
        archive_cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=14)
        
        try:
            db = self.firestore_logger.db
            old_cognitive_query = (db.collection(FirestoreCollections.LIVE_COGNITIVE)
                                 .where('timestamp', '<', archive_cutoff))
            
            old_cognitive = list(old_cognitive_query.stream())
            
            if old_cognitive:
                # Group by bot type
                cognitive_by_bot = {}
                for cognitive_doc in old_cognitive:
                    cognitive_data = cognitive_doc.to_dict()
                    bot_type = cognitive_data.get('bot_type', 'unknown')
                    
                    if bot_type not in cognitive_by_bot:
                        cognitive_by_bot[bot_type] = []
                    cognitive_by_bot[bot_type].append(cognitive_data)
                
                # Archive each bot's cognitive data
                for bot_type, cognitive_list in cognitive_by_bot.items():
                    from .log_types import CognitiveLogData
                    cognitive_objects = []
                    
                    for cognitive in cognitive_list:
                        try:
                            cognitive_obj = CognitiveLogData(**cognitive)
                            cognitive_objects.append(cognitive_obj)
                        except Exception as e:
                            print(f"Error converting cognitive data: {e}")
                    
                    if cognitive_objects:
                        self.gcs_logger.archive_cognitive_data(cognitive_objects, bot_type)
                
                # Delete archived cognitive data from Firestore
                batch = db.batch()
                for cognitive_doc in old_cognitive:
                    batch.delete(cognitive_doc.reference)
                batch.commit()
                
                print(f"Archived {len(old_cognitive)} cognitive decisions to GCS")
                
        except Exception as e:
            print(f"Error archiving cognitive data: {e}")
    
    def _monitor_costs(self):
        """Monitor storage costs and usage"""
        try:
            # Get Firestore usage
            firestore_stats = self._get_firestore_stats()
            
            # Get GCS usage
            gcs_stats = self._get_gcs_stats()
            
            # Check thresholds and alert if needed
            self._check_cost_thresholds(firestore_stats, gcs_stats)
            
            # Log usage metrics
            usage_metrics = {
                'firestore': firestore_stats,
                'gcs': gcs_stats,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Store usage metrics in GCS for historical tracking
            self.gcs_logger.archive_performance_metrics(usage_metrics, 'cost_monitoring')
            
        except Exception as e:
            print(f"Error monitoring costs: {e}")
    
    def _get_firestore_stats(self) -> Dict[str, Any]:
        """Get Firestore usage statistics"""
        db = self.firestore_logger.db
        
        stats = {
            'collections': {},
            'total_documents': 0,
            'estimated_cost_factors': {}
        }
        
        collections_to_check = [
            FirestoreCollections.LIVE_TRADES,
            FirestoreCollections.LIVE_POSITIONS,
            FirestoreCollections.LIVE_ALERTS,
            FirestoreCollections.LIVE_COGNITIVE,
            FirestoreCollections.LIVE_SYSTEM_STATUS,
            FirestoreCollections.DAILY_SUMMARIES,
            FirestoreCollections.DAILY_REFLECTIONS,
            FirestoreCollections.DASHBOARD_METRICS
        ]
        
        for collection_name in collections_to_check:
            try:
                # Count documents in collection
                docs = list(db.collection(collection_name).limit(1000).stream())
                count = len(docs)
                
                stats['collections'][collection_name] = count
                stats['total_documents'] += count
                
            except Exception as e:
                print(f"Error getting stats for {collection_name}: {e}")
                stats['collections'][collection_name] = 0
        
        return stats
    
    def _get_gcs_stats(self) -> Dict[str, Any]:
        """Get GCS usage statistics"""
        client = self.gcs_logger.client
        
        stats = {
            'buckets': {},
            'total_size_bytes': 0,
            'total_objects': 0
        }
        
        buckets_to_check = [
            GCSBuckets.TRADE_LOGS,
            GCSBuckets.COGNITIVE_ARCHIVES,
            GCSBuckets.SYSTEM_LOGS,
            GCSBuckets.ANALYTICS_DATA,
            GCSBuckets.COMPLIANCE_LOGS
        ]
        
        for bucket_name in buckets_to_check:
            try:
                bucket = client.bucket(bucket_name)
                
                blobs = list(bucket.list_blobs())
                total_size = sum(blob.size or 0 for blob in blobs)
                object_count = len(blobs)
                
                stats['buckets'][bucket_name] = {
                    'size_bytes': total_size,
                    'object_count': object_count,
                    'size_mb': total_size / (1024 * 1024),
                    'size_gb': total_size / (1024 * 1024 * 1024)
                }
                
                stats['total_size_bytes'] += total_size
                stats['total_objects'] += object_count
                
            except Exception as e:
                print(f"Error getting stats for bucket {bucket_name}: {e}")
                stats['buckets'][bucket_name] = {'size_bytes': 0, 'object_count': 0}
        
        stats['total_size_gb'] = stats['total_size_bytes'] / (1024 * 1024 * 1024)
        
        return stats
    
    def _check_cost_thresholds(self, firestore_stats: Dict, gcs_stats: Dict):
        """Check if usage exceeds cost thresholds"""
        alerts = []
        
        # Check Firestore document count
        if firestore_stats['total_documents'] > self.cost_thresholds['daily_firestore_writes']:
            alerts.append(f"High Firestore document count: {firestore_stats['total_documents']}")
        
        # Check GCS storage size
        if gcs_stats['total_size_gb'] > self.cost_thresholds['storage_size_gb']:
            alerts.append(f"High GCS storage usage: {gcs_stats['total_size_gb']:.2f} GB")
        
        # Check individual bucket sizes
        for bucket_name, bucket_stats in gcs_stats['buckets'].items():
            if bucket_stats['size_gb'] > 10:  # Alert for buckets > 10GB
                alerts.append(f"Large bucket {bucket_name}: {bucket_stats['size_gb']:.2f} GB")
        
        # Send alerts if any
        if alerts:
            self._send_cost_alerts(alerts, firestore_stats, gcs_stats)
    
    def _send_cost_alerts(self, alerts: List[str], firestore_stats: Dict, gcs_stats: Dict):
        """Send cost alerts"""
        from .log_types import ErrorLogData
        
        alert_data = ErrorLogData(
            error_id=f"cost_alert_{int(time.time())}",
            error_type="cost_threshold_exceeded",
            error_message=f"Storage cost thresholds exceeded: {'; '.join(alerts)}",
            context={
                'firestore_stats': firestore_stats,
                'gcs_stats': gcs_stats,
                'alerts': alerts
            }
        )
        
        # Log to Firestore for immediate alerting
        self.firestore_logger.log_alert(alert_data, severity="high")
        
        print(f"COST ALERT: {'; '.join(alerts)}")
    
    def optimize_storage_costs(self):
        """Run comprehensive storage cost optimization"""
        print("Running storage cost optimization...")
        
        try:
            # 1. Clean up unnecessary data
            self.run_daily_cleanup()
            
            # 2. Optimize GCS storage classes
            self._optimize_gcs_storage_classes()
            
            # 3. Compress uncompressed data
            self._compress_old_data()
            
            # 4. Deduplication check
            self._deduplicate_data()
            
            print("Storage cost optimization completed")
            
        except Exception as e:
            print(f"Error in cost optimization: {e}")
    
    def _optimize_gcs_storage_classes(self):
        """Optimize GCS storage classes for cost efficiency"""
        client = self.gcs_logger.client
        
        # Define storage class transitions based on age
        transitions = [
            {'age_days': 30, 'storage_class': 'NEARLINE'},
            {'age_days': 90, 'storage_class': 'COLDLINE'},
            {'age_days': 365, 'storage_class': 'ARCHIVE'}
        ]
        
        for bucket_name in [GCSBuckets.TRADE_LOGS, GCSBuckets.COGNITIVE_ARCHIVES,
                           GCSBuckets.SYSTEM_LOGS, GCSBuckets.ANALYTICS_DATA]:
            try:
                bucket = client.bucket(bucket_name)
                
                # Clear existing rules first to avoid compatibility issues
                bucket.lifecycle_rules = []
                
                # Use the robust add_lifecycle_*_rule methods instead of direct assignment
                try:
                    # Add storage class transitions
                    for transition in transitions:
                        bucket.add_lifecycle_set_storage_class_rule(
                            storage_class=transition['storage_class'],
                            age=transition['age_days']
                        )
                    
                    # Add deletion rule
                    if bucket_name in self.cleanup_policies['gcs']['delete_after_days']:
                        delete_days = self.cleanup_policies['gcs']['delete_after_days'][bucket_name.replace('tron-', '').replace('-', '_')]
                        bucket.add_lifecycle_delete_rule(age=delete_days)
                    
                    bucket.patch()
                    
                except AttributeError:
                    # Fallback 1: Use LifecycleRule objects directly (Claude's approach)
                    try:
                        from google.cloud.storage.bucket import LifecycleRuleDelete, LifecycleRuleSetStorageClass
                        
                        lifecycle_rules = []
                        
                        # Add storage class transitions using LifecycleRule objects
                        for transition in transitions:
                            transition_rule = LifecycleRuleSetStorageClass(
                                storage_class=transition['storage_class'],
                                age=transition['age_days']
                            )
                            lifecycle_rules.append(transition_rule)
                        
                        # Add deletion rule
                        if bucket_name in self.cleanup_policies['gcs']['delete_after_days']:
                            delete_days = self.cleanup_policies['gcs']['delete_after_days'][bucket_name.replace('tron-', '').replace('-', '_')]
                            delete_rule = LifecycleRuleDelete(age=delete_days)
                            lifecycle_rules.append(delete_rule)
                        
                        bucket.lifecycle_rules = lifecycle_rules
                        bucket.patch()
                        
                        print(f"Optimized storage classes for {bucket_name} (LifecycleRule method)")
                        
                    except (ImportError, AttributeError, Exception):
                        # Fallback 2: Dictionary method if LifecycleRule classes don't work
                        lifecycle_rules = []
                        
                        for transition in transitions:
                            lifecycle_rules.append({
                                'action': {
                                    'type': 'SetStorageClass',
                                    'storageClass': transition['storage_class']
                                },
                                'condition': {'age': transition['age_days']}
                            })
                        
                        # Add deletion rule
                        if bucket_name in self.cleanup_policies['gcs']['delete_after_days']:
                            delete_days = self.cleanup_policies['gcs']['delete_after_days'][bucket_name.replace('tron-', '').replace('-', '_')]
                            lifecycle_rules.append({
                                'action': {'type': 'Delete'},
                                'condition': {'age': delete_days}
                            })
                        
                        bucket.lifecycle_rules = lifecycle_rules
                        bucket.patch()
                
                print(f"Optimized storage classes for {bucket_name}")
                
            except Exception as e:
                print(f"Error optimizing {bucket_name}: {e}")
    
    def _compress_old_data(self):
        """Compress any uncompressed old data"""
        # This would identify and compress uncompressed files
        # Implementation depends on specific compression needs
        pass
    
    def _deduplicate_data(self):
        """Check for and remove duplicate data"""
        # This would implement deduplication logic
        # Could use content hashing to identify duplicates
        pass
    
    def get_cost_report(self) -> Dict[str, Any]:
        """Generate comprehensive cost report"""
        firestore_stats = self._get_firestore_stats()
        gcs_stats = self._get_gcs_stats()
        
        # Estimate costs (rough estimates)
        estimated_costs = {
            'firestore_monthly_usd': (firestore_stats['total_documents'] * 0.000036 * 30),  # Very rough estimate
            'gcs_storage_monthly_usd': (gcs_stats['total_size_gb'] * 0.020),  # Standard storage pricing
            'total_estimated_monthly_usd': 0
        }
        
        estimated_costs['total_estimated_monthly_usd'] = (
            estimated_costs['firestore_monthly_usd'] + 
            estimated_costs['gcs_storage_monthly_usd']
        )
        
        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'firestore_stats': firestore_stats,
            'gcs_stats': gcs_stats,
            'estimated_costs': estimated_costs,
            'optimization_recommendations': self._get_optimization_recommendations(firestore_stats, gcs_stats)
        }
    
    def _get_optimization_recommendations(self, firestore_stats: Dict, gcs_stats: Dict) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        if firestore_stats['total_documents'] > 5000:
            recommendations.append("Consider archiving old Firestore documents to GCS")
        
        if gcs_stats['total_size_gb'] > 50:
            recommendations.append("Review GCS lifecycle policies and storage classes")
        
        for bucket_name, bucket_stats in gcs_stats['buckets'].items():
            if bucket_stats['size_gb'] > 20:
                recommendations.append(f"Large bucket {bucket_name} - consider data archival")
        
        return recommendations 
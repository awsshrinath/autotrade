"""
Firestore Logger - Real-time, queryable data for dashboards and alerts
======================================================================

Optimized for:
- Real-time trade status updates
- Live errors and warnings for alerting
- Cognitive decisions and state transitions
- Current day GPT reflections
- Dashboard queries

Cost optimization:
- TTL-based automatic cleanup
- Minimal document writes
- Efficient indexing
- Batch operations where possible
"""

import datetime
from datetime import timezone
import time
import uuid
from typing import Dict, Any, List, Optional
from google.cloud import firestore
from .log_types import LogEntry, LogType, LogLevel, LogCategory, TradeLogData, CognitiveLogData, ErrorLogData


class FirestoreCollections:
    """Firestore collection names organized by purpose"""
    
    # Real-time collections (TTL enabled)
    LIVE_TRADES = "live_trades"                    # Current trade status
    LIVE_POSITIONS = "live_positions"              # Active positions
    LIVE_ALERTS = "live_alerts"                    # Errors, warnings, alerts
    LIVE_COGNITIVE = "live_cognitive_decisions"    # Real-time cognitive decisions
    LIVE_SYSTEM_STATUS = "live_system_status"      # Bot health, connectivity
    
    # Dashboard collections (30-day retention)
    DAILY_SUMMARIES = "daily_summaries"            # Daily performance summaries
    DAILY_REFLECTIONS = "daily_reflections"        # Current day GPT reflections
    DASHBOARD_METRICS = "dashboard_metrics"        # Key metrics for dashboards
    
    # Organized by date for efficient queries
    TRADES_BY_DATE = "trades_by_date"              # trades_by_date/{YYYY-MM-DD}/trades/{trade_id}
    COGNITIVE_BY_DATE = "cognitive_by_date"        # cognitive_by_date/{YYYY-MM-DD}/decisions/{decision_id}


class FirestoreLogger:
    """Optimized Firestore logger for real-time, queryable data"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id
        self.db = firestore.Client(project=project_id)
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Batch operations
        self.batch_size = 10
        self.pending_writes = []
        self.last_batch_time = time.time()
        self.batch_interval = 5  # seconds
    
    def _add_to_batch(self, collection: str, doc_id: str, data: Dict[str, Any]):
        """Add write to batch for efficiency"""
        self.pending_writes.append({
            'collection': collection,
            'doc_id': doc_id,
            'data': data
        })
        
        # Auto-flush batch if needed
        if (len(self.pending_writes) >= self.batch_size or 
            time.time() - self.last_batch_time > self.batch_interval):
            self.flush_batch()
    
    def flush_batch(self):
        """Flush pending writes to Firestore"""
        if not self.pending_writes:
            return
        
        try:
            batch = self.db.batch()
            
            for write in self.pending_writes:
                doc_ref = self.db.collection(write['collection']).document(write['doc_id'])
                batch.set(doc_ref, write['data'], merge=True)
            
            batch.commit()
            self.pending_writes.clear()
            self.last_batch_time = time.time()
            
        except Exception as e:
            # Don't lose data on batch failure - write individually
            for write in self.pending_writes:
                try:
                    doc_ref = self.db.collection(write['collection']).document(write['doc_id'])
                    doc_ref.set(write['data'], merge=True)
                except Exception as individual_error:
                    print(f"Failed to write to Firestore: {individual_error}")
            
            self.pending_writes.clear()
            print(f"Batch write failed, wrote individually: {e}")
    
    def log_trade_status(self, trade_data: TradeLogData, urgent: bool = False):
        """
        Log real-time trade status for dashboard monitoring
        
        Args:
            trade_data: Trade information
            urgent: If True, writes immediately (for critical updates)
        """
        doc_data = {
            **trade_data.to_dict(),
            'last_updated': firestore.SERVER_TIMESTAMP,
            'ttl': datetime.datetime.now(timezone.utc) + datetime.timedelta(days=7),  # 1 week TTL
            'urgent': urgent
        }
        
        if urgent:
            # Write immediately for critical updates
            doc_ref = self.db.collection(FirestoreCollections.LIVE_TRADES).document(trade_data.trade_id)
            doc_ref.set(doc_data, merge=True)
        else:
            # Add to batch for efficiency
            self._add_to_batch(FirestoreCollections.LIVE_TRADES, trade_data.trade_id, doc_data)
    
    def log_position_update(self, position_id: str, position_data: Dict[str, Any]):
        """Log real-time position updates"""
        doc_data = {
            **position_data,
            'position_id': position_id,
            'last_updated': firestore.SERVER_TIMESTAMP,
            'ttl': datetime.datetime.now(timezone.utc) + datetime.timedelta(days=7)
        }
        
        self._add_to_batch(FirestoreCollections.LIVE_POSITIONS, position_id, doc_data)
    
    def log_alert(self, alert_data: ErrorLogData, severity: str = "medium"):
        """
        Log alerts and errors for real-time monitoring
        
        Args:
            alert_data: Error/alert information
            severity: low, medium, high, critical
        """
        alert_id = f"{alert_data.error_type}_{int(time.time())}"
        
        doc_data = {
            **alert_data.to_dict(),
            'alert_id': alert_id,
            'severity': severity,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'ttl': datetime.datetime.now(timezone.utc) + datetime.timedelta(days=7),
            'acknowledged': False,
            'resolved': False
        }
        
        # High severity alerts write immediately
        if severity in ['high', 'critical']:
            doc_ref = self.db.collection(FirestoreCollections.LIVE_ALERTS).document(alert_id)
            doc_ref.set(doc_data)
        else:
            self._add_to_batch(FirestoreCollections.LIVE_ALERTS, alert_id, doc_data)
    
    def log_cognitive_decision(self, cognitive_data: CognitiveLogData, bot_type: str):
        """Log real-time cognitive decisions"""
        decision_id = cognitive_data.decision_id or f"decision_{int(time.time())}"
        
        doc_data = {
            **cognitive_data.to_dict(),
            'decision_id': decision_id,
            'bot_type': bot_type,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'ttl': datetime.datetime.now(timezone.utc) + datetime.timedelta(days=14)  # 2 weeks for cognitive data
        }
        
        # Store in live collection for real-time access
        self._add_to_batch(FirestoreCollections.LIVE_COGNITIVE, decision_id, doc_data)
        
        # Also store in date-organized collection for historical queries
        date_doc_path = f"{self.today}/decisions"
        date_doc_ref = (self.db.collection(FirestoreCollections.COGNITIVE_BY_DATE)
                       .document(self.today)
                       .collection("decisions")
                       .document(decision_id))
        date_doc_ref.set(doc_data, merge=True)
    
    def log_system_status(self, bot_type: str, status_data: Dict[str, Any]):
        """Log system health and connectivity status"""
        doc_data = {
            **status_data,
            'bot_type': bot_type,
            'last_heartbeat': firestore.SERVER_TIMESTAMP,
            'ttl': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)  # 1 hour TTL for status
        }
        
        doc_ref = self.db.collection(FirestoreCollections.LIVE_SYSTEM_STATUS).document(bot_type)
        doc_ref.set(doc_data, merge=True)
    
    def log_daily_summary(self, bot_type: str, summary_data: Dict[str, Any]):
        """Log daily performance summary for dashboard"""
        summary_id = f"{bot_type}_{self.today}"
        
        doc_data = {
            **summary_data,
            'bot_type': bot_type,
            'date': self.today,
            'last_updated': firestore.SERVER_TIMESTAMP,
            'ttl': datetime.datetime.now(timezone.utc) + datetime.timedelta(days=30)  # 30 days retention
        }
        
        doc_ref = self.db.collection(FirestoreCollections.DAILY_SUMMARIES).document(summary_id)
        doc_ref.set(doc_data, merge=True)
    
    def log_daily_reflection(self, bot_type: str, reflection_text: str):
        """Log GPT reflection for current day dashboard display"""
        reflection_id = f"{bot_type}_{self.today}"
        
        doc_data = {
            'bot_type': bot_type,
            'date': self.today,
            'reflection': reflection_text,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'ttl': datetime.datetime.now(timezone.utc) + datetime.timedelta(days=30)
        }
        
        doc_ref = self.db.collection(FirestoreCollections.DAILY_REFLECTIONS).document(reflection_id)
        doc_ref.set(doc_data, merge=True)
    
    def log_dashboard_metric(self, metric_name: str, metric_value: Any, bot_type: str = None):
        """Log key metrics for dashboard display"""
        metric_id = f"{metric_name}_{bot_type}_{self.today}" if bot_type else f"{metric_name}_{self.today}"
        
        doc_data = {
            'metric_name': metric_name,
            'metric_value': metric_value,
            'bot_type': bot_type,
            'date': self.today,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'ttl': datetime.datetime.now(timezone.utc) + datetime.timedelta(days=30)
        }
        
        self._add_to_batch(FirestoreCollections.DASHBOARD_METRICS, metric_id, doc_data)
    
    # Query methods for dashboard and real-time monitoring
    
    def get_live_trades(self, bot_type: str = None, status: str = None) -> List[Dict]:
        """Get live trades for dashboard"""
        query = self.db.collection(FirestoreCollections.LIVE_TRADES)
        
        if bot_type:
            query = query.where('bot_type', '==', bot_type)
        if status:
            query = query.where('status', '==', status)
        
        query = query.order_by('last_updated', direction=firestore.Query.DESCENDING).limit(100)
        
        return [doc.to_dict() for doc in query.stream()]
    
    def get_live_alerts(self, severity: str = None, unresolved_only: bool = True) -> List[Dict]:
        """Get live alerts for monitoring"""
        query = self.db.collection(FirestoreCollections.LIVE_ALERTS)
        
        if unresolved_only:
            query = query.where('resolved', '==', False)
        if severity:
            query = query.where('severity', '==', severity)
        
        query = query.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50)
        
        return [doc.to_dict() for doc in query.stream()]
    
    def get_system_status(self) -> Dict[str, Dict]:
        """Get current system status for all bots"""
        docs = self.db.collection(FirestoreCollections.LIVE_SYSTEM_STATUS).stream()
        return {doc.id: doc.to_dict() for doc in docs}
    
    def get_daily_summaries(self, date: str = None) -> Dict[str, Dict]:
        """Get daily summaries for all bots"""
        date = date or self.today
        query = self.db.collection(FirestoreCollections.DAILY_SUMMARIES).where('date', '==', date)
        docs = query.stream()
        return {doc.id: doc.to_dict() for doc in docs}
    
    def acknowledge_alert(self, alert_id: str):
        """Mark an alert as acknowledged"""
        doc_ref = self.db.collection(FirestoreCollections.LIVE_ALERTS).document(alert_id)
        doc_ref.update({'acknowledged': True, 'acknowledged_at': firestore.SERVER_TIMESTAMP})
    
    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved"""
        doc_ref = self.db.collection(FirestoreCollections.LIVE_ALERTS).document(alert_id)
        doc_ref.update({'resolved': True, 'resolved_at': firestore.SERVER_TIMESTAMP})
    
    def cleanup_expired_data(self):
        """Manual cleanup of expired TTL data (in case automatic TTL isn't enabled)"""
        collections_to_clean = [
            FirestoreCollections.LIVE_TRADES,
            FirestoreCollections.LIVE_POSITIONS,
            FirestoreCollections.LIVE_ALERTS,
            FirestoreCollections.LIVE_COGNITIVE,
            FirestoreCollections.LIVE_SYSTEM_STATUS,
            FirestoreCollections.DAILY_SUMMARIES,
            FirestoreCollections.DAILY_REFLECTIONS,
            FirestoreCollections.DASHBOARD_METRICS
        ]
        
        now = datetime.datetime.now(timezone.utc)
        
        for collection_name in collections_to_clean:
            try:
                # Query documents with expired TTL
                expired_query = (self.db.collection(collection_name)
                               .where('ttl', '<', now)
                               .limit(100))  # Process in batches
                
                expired_docs = list(expired_query.stream())
                
                if expired_docs:
                    batch = self.db.batch()
                    for doc in expired_docs:
                        batch.delete(doc.reference)
                    
                    batch.commit()
                    print(f"Cleaned up {len(expired_docs)} expired documents from {collection_name}")
                    
            except Exception as e:
                print(f"Error cleaning up {collection_name}: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.flush_batch()
        except:
            pass 
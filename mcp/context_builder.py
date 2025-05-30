"""
Enhanced MCP Context Builder for TRON Trading System
===================================================

Builds structured context for GPT using Module Context Protocol (MCP) format.
Enhanced with comprehensive logging and multi-source data integration.

Data Sources:
- Firestore: Real-time trading data, recent logs, active positions
- GCS: Historical data, archived logs, performance analytics
- RAG: Contextual knowledge retrieval from vector store
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Import enhanced logging
try:
    from .enhanced_mcp_logger import get_mcp_logger, MCPDecisionType
    ENHANCED_MCP_LOGGING = True
except ImportError:
    print("Warning: Enhanced MCP logging not available")
    ENHANCED_MCP_LOGGING = False

# Import data sources
try:
    from runner.capital.portfolio_manager import get_current_capital
    from runner.firestore_client import fetch_recent_trades, FirestoreClient
    from runner.market_monitor import get_latest_market_context
except ImportError as e:
    print(f"Warning: Could not import data sources: {e}")
    
    # Fallback functions
    def get_current_capital(bot_name):
        return {"allocated": 0, "used": 0, "available": 0}
    
    def fetch_recent_trades(bot_name, limit=5):
        return []
    
    def get_latest_market_context():
        return {}

# Import RAG retrieval
try:
    from gpt_runner.rag.retriever import retrieve_similar_context, retrieve_by_category
    RAG_AVAILABLE = True
except ImportError:
    print("Warning: RAG retrieval not available")
    RAG_AVAILABLE = False
    
    def retrieve_similar_context(*args, **kwargs):
        return []
    
    def retrieve_by_category(*args, **kwargs):
        return []

# Import GCS data access
try:
    from runner.enhanced_logging.gcs_logger import GCSLogger
    GCS_AVAILABLE = True
except ImportError:
    print("Warning: GCS access not available")
    GCS_AVAILABLE = False


class EnhancedMCPContextBuilder:
    """Enhanced MCP context builder with multi-source data integration"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or f"mcp_context_{int(time.time())}"
        
        # Initialize logging
        self.mcp_logger = None
        if ENHANCED_MCP_LOGGING:
            self.mcp_logger = get_mcp_logger(self.session_id, "mcp_context")
        
        # Initialize data clients
        self.firestore_client = None
        try:
            self.firestore_client = FirestoreClient()
        except Exception as e:
            print(f"Warning: Could not initialize Firestore client: {e}")
        
        self.gcs_logger = None
        if GCS_AVAILABLE:
            try:
                self.gcs_logger = GCSLogger()
            except Exception as e:
                print(f"Warning: Could not initialize GCS client: {e}")
    
    def build_mcp_context(self, bot_name: str, context_request: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Build comprehensive MCP context from multiple sources
        
        Args:
            bot_name: Name of the bot requesting context
            context_request: Specific context requirements
            
        Returns:
            Structured MCP context dictionary
        """
        start_time = time.time()
        context_sources = []
        
        if context_request is None:
            context_request = {
                "include_trades": True,
                "include_capital": True,
                "include_market": True,
                "include_rag": True,
                "include_historical": False,
                "time_range_hours": 24
            }
        
        try:
            # 1. Get current capital allocation
            capital = {}
            if context_request.get("include_capital", True):
                capital = get_current_capital(bot_name)
                context_sources.append("capital_manager")
            
            # 2. Get recent trades from Firestore
            trades = []
            if context_request.get("include_trades", True):
                trades = fetch_recent_trades(
                    bot_name=bot_name, 
                    limit=context_request.get("trade_limit", 10)
                )
                context_sources.append("firestore_trades")
            
            # 3. Get market context
            market = {}
            if context_request.get("include_market", True):
                market = get_latest_market_context()
                context_sources.append("market_monitor")
            
            # 4. Get RAG knowledge retrieval
            retrieved_knowledge = []
            if context_request.get("include_rag", True) and RAG_AVAILABLE:
                # Retrieve relevant context based on bot performance
                query = f"trading performance for {bot_name} recent strategies"
                rag_results = retrieve_similar_context(
                    query=query,
                    limit=5,
                    bot_name=bot_name,
                    session_id=self.session_id,
                    context_type="performance_context"
                )
                retrieved_knowledge = [
                    {
                        "text": doc.get('text', ''),
                        "metadata": doc.get('metadata', {}),
                        "similarity": score
                    }
                    for doc, score in rag_results
                ]
                context_sources.append("rag_retrieval")
            
            # 5. Get historical data from GCS if requested
            historical_data = {}
            if context_request.get("include_historical", False) and self.gcs_logger:
                historical_data = self._get_historical_context(
                    bot_name, 
                    context_request.get("time_range_hours", 24)
                )
                context_sources.append("gcs_historical")
            
            # 6. Get recent logs and errors
            recent_logs = []
            error_context = []
            if self.firestore_client:
                # Get recent system logs
                recent_logs = self._get_recent_logs(bot_name, hours=6)
                context_sources.append("firestore_logs")
                
                # Get recent errors for debugging context
                error_context = self._get_recent_errors(bot_name, hours=24)
                if error_context:
                    context_sources.append("error_logs")
            
            # 7. Build structured context
            context = {
                "bot": bot_name,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "capital": capital,
                "market": market,
                "trades": trades,
                "retrieved_knowledge": retrieved_knowledge,
                "historical_data": historical_data,
                "recent_logs": recent_logs,
                "error_context": error_context,
                "actions_allowed": [
                    "suggest_strategy",
                    "fix_code",
                    "update_sl",
                    "log_reflection",
                    "adjust_parameters",
                    "risk_assessment"
                ],
                "context_metadata": {
                    "sources": context_sources,
                    "completeness_score": self._calculate_completeness(context_sources),
                    "build_time_ms": (time.time() - start_time) * 1000,
                    "request_params": context_request
                }
            }
            
            # Log context building
            if self.mcp_logger:
                self.mcp_logger.log_mcp_context(
                    context_request=context_request,
                    context_sources=context_sources,
                    context_data=context,
                    build_time_ms=(time.time() - start_time) * 1000,
                    completeness_score=context["context_metadata"]["completeness_score"]
                )
            
            return context
            
        except Exception as e:
            print(f"Error building MCP context: {e}")
            
            # Return minimal context on error
            fallback_context = {
                "bot": bot_name,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "capital": get_current_capital(bot_name),
                "market": {},
                "trades": [],
                "retrieved_knowledge": [],
                "actions_allowed": ["suggest_strategy", "log_reflection"],
                "error": str(e),
                "context_metadata": {
                    "sources": ["fallback"],
                    "completeness_score": 0.1,
                    "build_time_ms": (time.time() - start_time) * 1000
                }
            }
            
            if self.mcp_logger:
                self.mcp_logger.log_mcp_context(
                    context_request=context_request or {},
                    context_sources=["error_fallback"],
                    context_data=fallback_context,
                    build_time_ms=(time.time() - start_time) * 1000,
                    completeness_score=0.1
                )
            
            return fallback_context
    
    def _get_historical_context(self, bot_name: str, hours: int) -> Dict[str, Any]:
        """Get historical data from GCS"""
        if not self.gcs_logger:
            return {}
        
        try:
            # This would be implemented to read from GCS buckets
            # For now, return placeholder
            return {
                "trade_history": [],
                "performance_metrics": {},
                "strategy_evolution": [],
                "time_range_hours": hours
            }
        except Exception as e:
            print(f"Error fetching historical context: {e}")
            return {}
    
    def _get_recent_logs(self, bot_name: str, hours: int = 6) -> List[Dict[str, Any]]:
        """Get recent logs from Firestore"""
        if not self.firestore_client:
            return []
        
        try:
            # Query recent logs
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # This would use firestore client to query logs
            # For now, return placeholder
            return []
        except Exception as e:
            print(f"Error fetching recent logs: {e}")
            return []
    
    def _get_recent_errors(self, bot_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent errors for debugging context"""
        if not self.firestore_client:
            return []
        
        try:
            # This would query error logs from Firestore
            # For now, return placeholder
            return []
        except Exception as e:
            print(f"Error fetching error context: {e}")
            return []
    
    def _calculate_completeness(self, sources: List[str]) -> float:
        """Calculate context completeness score based on available sources"""
        expected_sources = [
            "capital_manager", "firestore_trades", "market_monitor", 
            "rag_retrieval", "firestore_logs"
        ]
        
        available_count = len([s for s in sources if s in expected_sources])
        return min(1.0, available_count / len(expected_sources))


# Backward compatibility with existing code
def build_mcp_context(bot_name: str, enhanced: bool = False) -> Dict[str, Any]:
    """
    Build MCP context with optional enhancement
    
    Args:
        bot_name: Name of the bot requesting context
        enhanced: Whether to use enhanced context builder
        
    Returns:
        MCP context dictionary
    """
    if enhanced:
        builder = EnhancedMCPContextBuilder()
        return builder.build_mcp_context(bot_name)
    else:
        # Legacy simple context building
        trades = fetch_recent_trades(bot_name=bot_name, limit=5)
        market = get_latest_market_context()
        capital = get_current_capital(bot_name)

        context = {
            "bot": bot_name,
            "capital": capital,
            "market": market,
            "trades": trades,
            "retrieved_knowledge": [],  # to be filled by RAG if needed
            "actions_allowed": [
                "suggest_strategy",
                "fix_code",
                "update_sl",
                "log_reflection",
            ],
        }
        return context


# Factory function for creating enhanced context builder
def create_mcp_context_builder(session_id: str = None) -> EnhancedMCPContextBuilder:
    """Create new enhanced MCP context builder"""
    return EnhancedMCPContextBuilder(session_id)

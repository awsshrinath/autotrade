from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import asyncio
import os
import openai

from .log_service import LogService, get_log_service

logger = logging.getLogger(__name__)

class CognitiveService:
    """Service for handling cognitive AI insights and analysis."""
    
    def __init__(self, log_service: LogService):
        self.logger = logger
        self.log_service = log_service
        self.is_enabled = bool(os.getenv("OPENAI_API_KEY"))
        if self.is_enabled:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        else:
            logger.warning("OPENAI_API_KEY not found. Cognitive insights will be disabled.")

    async def get_log_summary(self, source: str, identifier: str) -> Dict[str, Any]:
        """
        Generates a summary for logs from a specific source (gcs, firestore, k8s).
        """
        if not self.is_enabled:
            return {"status": "disabled", "message": "Cognitive features are disabled due to missing OPENAI_API_KEY."}

        try:
            # 1. Fetch logs using the LogService
            if source == "k8s":
                logs = await self.log_service.get_k8s_pod_logs(pod_name=identifier, limit=200)
                log_content = "\n".join(logs)
            elif source == "gcs":
                log_data = await self.log_service.get_gcs_log_content(file_path=identifier)
                log_content = log_data.get("content", "")
            else:
                return {"status": "error", "message": "Invalid log source specified."}

            if not log_content:
                return {"summary": "No log content available to summarize."}

            # 2. Call OpenAI to summarize
            prompt = f"""
            Analyze the following log entries from a trading bot system and provide a concise summary.
            Focus on errors, warnings, key trades, and system status changes.

            Logs:
            ---
            {log_content[:4000]}
            ---
            
            Summary:
            """

            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.3,
            )

            summary = response.choices[0].text.strip()
            return {"source": identifier, "summary": summary}

        except Exception as e:
            self.logger.error(f"Error generating log summary for {identifier}: {e}")
            return {"status": "error", "message": str(e)}

    async def get_cognitive_summary(self) -> Dict[str, Any]:
        """Get overall cognitive system summary."""
        try:
            if not self.is_enabled:
                return {
                    "status": "disabled",
                    "message": "Cognitive insights are disabled",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Mock data for now - in production this would connect to actual cognitive systems
            summary = {
                "status": "active",
                "ai_models_active": 3,
                "insights_generated": 45,
                "confidence_score": 0.87,
                "last_analysis": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
                "market_sentiment": "bullish",
                "risk_assessment": "moderate",
                "recommendation_accuracy": 0.82,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting cognitive summary: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get cognitive summary: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_cognitive_health(self) -> Dict[str, Any]:
        """Get cognitive system health status."""
        try:
            # Mock health check - in production this would check actual AI services
            health_status = {
                "status": "healthy" if self.is_enabled else "disabled",
                "uptime": "2h 34m",
                "memory_usage": 0.67,
                "cpu_usage": 0.23,
                "models_loaded": 3,
                "errors_last_hour": 0,
                "api_response_time": 0.145,
                "last_health_check": datetime.utcnow().isoformat(),
                "components": {
                    "sentiment_analyzer": "healthy",
                    "risk_predictor": "healthy", 
                    "pattern_detector": "healthy",
                    "recommendation_engine": "healthy"
                }
            }
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error getting cognitive health: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get cognitive health: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_trade_insights(self) -> List[Dict[str, Any]]:
        """Get AI-powered trade insights."""
        try:
            if not self.is_enabled:
                return []
            
            # Mock insights - in production this would use actual AI analysis
            insights = [
                {
                    "id": "insight_1",
                    "type": "trend_analysis",
                    "symbol": "NIFTY",
                    "confidence": 0.89,
                    "signal": "bullish",
                    "timeframe": "1D",
                    "message": "Strong upward momentum detected with RSI showing oversold recovery",
                    "generated_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                    "validity_until": (datetime.utcnow() + timedelta(hours=4)).isoformat()
                },
                {
                    "id": "insight_2", 
                    "type": "risk_warning",
                    "symbol": "BANKNIFTY",
                    "confidence": 0.76,
                    "signal": "caution",
                    "timeframe": "4H",
                    "message": "Volatility spike detected, consider position sizing",
                    "generated_at": (datetime.utcnow() - timedelta(minutes=12)).isoformat(),
                    "validity_until": (datetime.utcnow() + timedelta(hours=2)).isoformat()
                },
                {
                    "id": "insight_3",
                    "type": "pattern_detection", 
                    "symbol": "RELIANCE",
                    "confidence": 0.82,
                    "signal": "bearish",
                    "timeframe": "1H",
                    "message": "Head and shoulders pattern forming, potential reversal signal",
                    "generated_at": (datetime.utcnow() - timedelta(minutes=18)).isoformat(),
                    "validity_until": (datetime.utcnow() + timedelta(hours=6)).isoformat()
                }
            ]
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error getting trade insights: {str(e)}")
            return []

# Dependency injection
_cognitive_service_instance = None

def get_cognitive_service() -> Optional[CognitiveService]:
    """Get cognitive service instance, injecting LogService."""
    global _cognitive_service_instance
    if _cognitive_service_instance is None:
        log_service = get_log_service()
        _cognitive_service_instance = CognitiveService(log_service=log_service)
    return _cognitive_service_instance
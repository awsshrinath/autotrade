# runner/enhanced_openai_manager.py

import datetime
import os
import logging
from typing import Optional, Dict, Any

try:
import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from runner.logger import Logger

# Fallback logger setup
try:
logger = Logger(datetime.date.today().isoformat())
except Exception:
    logger = logging.getLogger(__name__)

PROJECT_ID = "autotrade-453303"  # Your GCP Project ID


class EnhancedOpenAIManager:
    """Enhanced OpenAI Manager with robust error handling and fallbacks"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.api_key = None
        self.client_initialized = False
        self.fallback_mode = False
        
        # Try to initialize OpenAI client
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client with fallbacks"""
        
        if not OPENAI_AVAILABLE:
            self._log_error("OpenAI package not available")
            self.fallback_mode = True
            return
            
        try:
            # Try to get API key from multiple sources
            self.api_key = self._get_api_key()
            
            if self.api_key:
        openai.api_key = self.api_key
                self.client_initialized = True
                self._log_success("OpenAI API client initialized successfully")
            else:
                self._log_warning("OpenAI API key not available - using fallback mode")
                self.fallback_mode = True
                
        except Exception as e:
            self._log_error(f"Failed to initialize OpenAI client: {e}")
            self.fallback_mode = True

    def _get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from multiple sources with fallbacks"""
        
        # Source 1: Environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "emergency_mode_no_key":
            self._log_info("Using OpenAI API key from environment variable")
            return api_key
            
        # Source 2: Try Kubernetes-native GCP Secret Manager (no impersonation)
        try:
            from runner.k8s_native_gcp_client import get_k8s_gcp_client
            k8s_client = get_k8s_gcp_client(logger=self.logger)
            if k8s_client and hasattr(k8s_client, 'get_secret'):
                api_key = k8s_client.get_secret("OPENAI_API_KEY")
                if api_key:
                    self._log_info("Using OpenAI API key from K8s-native Secret Manager")
                    return api_key
        except Exception as e:
            self._log_warning(f"K8s-native Secret Manager failed: {e}")
            
        # Source 3: Try Original Secret Manager (fallback)
        try:
            from runner.secret_manager_client import access_secret
            api_key = access_secret("OPENAI_API_KEY", PROJECT_ID)
            if api_key:
                self._log_info("Using OpenAI API key from original Secret Manager")
                return api_key
        except Exception as e:
            self._log_warning(f"Original Secret Manager failed: {e}")
            
        # Source 4: Local config file (if exists)
        try:
            config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'openai_key.txt')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    api_key = f.read().strip()
                if api_key:
                    self._log_info("Using OpenAI API key from local config file")
                    return api_key
        except Exception as e:
            self._log_warning(f"Could not read local config file: {e}")
            
        return None

    def get_suggestion(self, prompt_text: str) -> Optional[str]:
        """Get suggestion from OpenAI with fallback responses"""
        
        if self.fallback_mode or not self.client_initialized:
            return self._get_fallback_suggestion(prompt_text)
            
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a smart trading assistant.",
                    },
                    {"role": "user", "content": prompt_text},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            suggestion = response.choices[0].message.content.strip()
            return suggestion
            
        except Exception as e:
            self._log_error(f"OpenAI API call failed: {e}")
            return self._get_fallback_suggestion(prompt_text)

    def get_embedding(self, text: str) -> list:
        """Get text embedding with fallback to empty list"""
        
        if self.fallback_mode or not self.client_initialized:
            self._log_warning("Using fallback embedding (empty vector)")
            return []
            
        try:
            response = openai.Embedding.create(
                input=text, 
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
            
        except Exception as e:
            self._log_error(f"Embedding failed: {e}")
            return []

    def summarize_text(self, prompt: str) -> str:
        """Summarize text with fallback responses"""
        
        if self.fallback_mode or not self.client_initialized:
            return self._get_fallback_summary(prompt)
            
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trading analyst.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            return completion["choices"][0]["message"]["content"]
            
        except Exception as e:
            self._log_error(f"Summarization failed: {e}")
            return self._get_fallback_summary(prompt)

    def _get_fallback_suggestion(self, prompt_text: str) -> str:
        """Provide fallback trading suggestions"""
        
        # Simple rule-based fallback suggestions
        prompt_lower = prompt_text.lower()
        
        if "bullish" in prompt_lower or "positive" in prompt_lower:
            return "Market sentiment appears positive. Consider bullish strategies like buying calls or long positions."
        elif "bearish" in prompt_lower or "negative" in prompt_lower:
            return "Market sentiment appears negative. Consider bearish strategies like buying puts or short positions."
        elif "volatile" in prompt_lower or "uncertainty" in prompt_lower:
            return "High volatility detected. Consider neutral strategies like strangles or wait for clearer signals."
        else:
            return "Market sentiment unclear. Recommend VWAP strategy with conservative position sizing."

    def _get_fallback_summary(self, prompt: str) -> str:
        """Provide fallback summary"""
        return f"Summary not available (fallback mode). Original prompt length: {len(prompt)} characters."

    def _log_success(self, message: str):
        """Log success message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"✅ [OpenAI] {message}")
        else:
            self.logger.info(f"[OpenAI] {message}")

    def _log_info(self, message: str):
        """Log info message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"ℹ️ [OpenAI] {message}")
        else:
            self.logger.info(f"[OpenAI] {message}")

    def _log_warning(self, message: str):
        """Log warning message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"⚠️ [OpenAI] {message}")
        else:
            self.logger.warning(f"[OpenAI] {message}")

    def _log_error(self, message: str):
        """Log error message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"❌ [OpenAI] {message}")
        else:
            self.logger.error(f"[OpenAI] {message}")

    def is_available(self) -> bool:
        """Check if OpenAI services are available"""
        return self.client_initialized and not self.fallback_mode

    def get_status(self) -> Dict[str, Any]:
        """Get status information"""
        return {
            "client_initialized": self.client_initialized,
            "fallback_mode": self.fallback_mode,
            "api_key_available": bool(self.api_key),
            "openai_package_available": OPENAI_AVAILABLE
        }


def ask_gpt_enhanced(input_data: Dict[str, Any]) -> Dict[str, str]:
    """Enhanced GPT strategy selection with robust fallbacks"""
    
    try:
        # Initialize enhanced OpenAI manager
        gpt = EnhancedOpenAIManager(logger=logger)
        
        if gpt.is_available():
            # Use OpenAI if available
        prompt = f"""
You are a trading strategy selector bot.

Based on the following sentiment:
{input_data}

Respond with a strategy name (e.g., 'vwap_strategy', 'orb_strategy') and a direction (bullish, bearish, neutral)
for the bot type: {input_data.get("bot", "")}.

Reply strictly in the following JSON format:
{{
    "strategy": "<name>",
    "direction": "<bullish|bearish|neutral>"
}}
"""
        response_text = gpt.get_suggestion(prompt)

            if response_text:
        import json
                return json.loads(response_text)
                
        # Fallback strategy selection
        return _get_fallback_strategy(input_data)

    except Exception as e:
        if hasattr(logger, 'log_event'):
            logger.log_event(f"❌ [GPT] Strategy selection failed: {e}")
        else:
            logger.error(f"[GPT] Strategy selection failed: {e}")
        
        return _get_fallback_strategy(input_data)


def _get_fallback_strategy(input_data: Dict[str, Any]) -> Dict[str, str]:
    """Rule-based fallback strategy selection"""
    
    bot_type = input_data.get("bot", "").lower()
    sentiment = str(input_data).lower()
    
    # Default strategies by bot type
    if "stock" in bot_type:
        strategy = "vwap_strategy"
    elif "option" in bot_type:
        strategy = "scalp_strategy"
    elif "future" in bot_type:
        strategy = "orb_strategy"
    else:
        strategy = "vwap_strategy"
    
    # Determine direction based on sentiment keywords
    if any(word in sentiment for word in ["bullish", "positive", "good", "strong"]):
        direction = "bullish"
    elif any(word in sentiment for word in ["bearish", "negative", "bad", "weak"]):
        direction = "bearish"
    else:
        direction = "neutral"
    
    return {
        "strategy": strategy,
        "direction": direction
    }


# Create singleton instance for backward compatibility
_enhanced_openai_manager = None

def get_openai_manager(logger=None) -> EnhancedOpenAIManager:
    """Get singleton OpenAI manager instance"""
    global _enhanced_openai_manager
    
    if _enhanced_openai_manager is None:
        _enhanced_openai_manager = EnhancedOpenAIManager(logger)
    
    return _enhanced_openai_manager


# Backward compatibility
def OpenAIManager(logger=None):
    """Backward compatibility wrapper"""
    return get_openai_manager(logger) 
class StrategySelector:
    def __init__(self, logger=None):
        self.logger = logger

    @staticmethod
    def choose_strategy(bot_type="stock", sentiment=None, market_context=None):
        direction = "neutral"
        if sentiment:
            sgx_trend = sentiment.get("sgx_nifty", "neutral")
            dow_trend = sentiment.get("dow", "neutral")
            if sgx_trend == "bullish" and dow_trend != "bearish":
                direction = "bullish"
            elif sgx_trend == "bearish" and dow_trend != "bullish":
                direction = "bearish"
            else:
                direction = "neutral"

        # 🚀 NEW: Enhanced regime-based strategy selection using comprehensive market analysis
        if market_context and "regime_analysis" in market_context:
            regime_analysis = market_context.get("regime_analysis", {})
            overall_regime = regime_analysis.get("overall_regime", {})
            
            # Primary strategy selection based on overall regime recommendation
            recommended_strategy = overall_regime.get("strategy_recommendation")
            confidence = overall_regime.get("confidence", 0.5)
            
            if recommended_strategy and confidence > 0.4:  # Use regime recommendation if confident
                if sentiment and confidence > 0.7:  # High confidence, log detailed reasoning
                    StrategySelector._log_regime_decision(regime_analysis, recommended_strategy, direction)
                return recommended_strategy, direction
            
            # Fallback to detailed analysis if no clear recommendation
            trend_classification = regime_analysis.get("trend_classification", {})
            volatility_details = regime_analysis.get("volatility_regimes", {})
            correlation_analysis = regime_analysis.get("correlation_analysis", {})
            
            return StrategySelector._analyze_regime_factors(
                trend_classification, volatility_details, correlation_analysis, direction, bot_type
            )
        
        # Fallback to original volatility regime logic if new regime analysis not available
        elif market_context and "volatility_details" in market_context:
            vol_details = market_context.get("volatility_details", {})
            hr_regime = vol_details.get("1hr", {}).get("regime", "UNKNOWN")
            
            # Enhanced volatility-based logic
            if hr_regime == "HIGH":
                return "range_reversal", direction 
            elif hr_regime == "LOW":
                return "vwap", direction
            elif hr_regime == "MEDIUM":
                return "orb", direction
            else: # UNKNOWN or other cases
                # Check for VIX fallback
                vix_sentiment = market_context.get("sentiment", {}).get("vix", "moderate")
                if vix_sentiment == "high":
                    return "range_reversal", direction
                elif vix_sentiment == "low":
                    return "vwap", direction
                else:
                    return "orb", direction
        
        # Fallback to VIX-based logic if volatility_details not present
        elif market_context and "sentiment" in market_context:
            vix_sentiment_value = market_context.get("sentiment", {}).get("vix", "moderate")
            if vix_sentiment_value == "high":
                return "range_reversal", direction
            elif vix_sentiment_value == "low":
                return "vwap", direction
            else:
                return "orb", direction

        # Final fallback to static bot-type mapping
        if bot_type == "stock":
            return "vwap", direction
        elif bot_type == "futures":
            return "orb", direction
        elif bot_type == "options":
            return "scalp", direction
        else:
            return "range_reversal", direction

    @staticmethod
    def _analyze_regime_factors(trend_classification, volatility_details, correlation_analysis, direction, bot_type):
        """Analyze individual regime factors when no clear overall recommendation"""
        
        # Extract key indicators
        trend_regime = trend_classification.get("regime", "UNKNOWN")
        adx = trend_classification.get("adx", 0)
        trend_confidence = trend_classification.get("confidence", 0)
        
        vol_1hr = volatility_details.get("1hr", {}).get("regime", "UNKNOWN")
        
        correlation_breakdown = correlation_analysis.get("analysis", {}).get("correlation_breakdown", False)
        
        # Advanced strategy selection logic
        
        # Strong trending markets
        if trend_regime == "STRONGLY_TRENDING" and adx > 30:
            if vol_1hr == "HIGH":
                return "scalp", direction  # Quick trades in volatile trends
            else:
                return "vwap", direction   # Follow the strong trend
        
        # Weak trending or mixed markets
        elif trend_regime in ["WEAKLY_TRENDING", "MIXED"]:
            if vol_1hr == "HIGH":
                return "range_reversal", direction  # Mean reversion in choppy markets
            else:
                return "orb", direction  # Wait for clear breakout
        
        # Ranging markets
        elif trend_regime == "RANGING":
            if vol_1hr == "HIGH":
                return "range_reversal", direction  # Profit from range bounds
            else:
                return "orb", direction  # Wait for range breakout
        
        # Correlation breakdown scenarios
        elif correlation_breakdown:
            # During correlation breakdowns, prefer safer strategies
            if vol_1hr == "HIGH":
                return "scalp", direction  # Quick in/out trades
            else:
                return "vwap", direction  # Stick to established trends
        
        # Default fallback based on volatility
        else:
            if vol_1hr == "HIGH":
                return "range_reversal", direction
            elif vol_1hr == "LOW":
                return "vwap", direction
            else:
                return "orb", direction

    @staticmethod
    def _log_regime_decision(regime_analysis, strategy, direction):
        """Log detailed reasoning for regime-based strategy selection"""
        try:
            trend_data = regime_analysis.get("trend_classification", {})
            vol_data = regime_analysis.get("volatility_regimes", {})
            corr_data = regime_analysis.get("correlation_analysis", {})
            overall = regime_analysis.get("overall_regime", {})
            
            reasoning = {
                "selected_strategy": strategy,
                "direction": direction,
                "confidence": overall.get("confidence", 0),
                "regime": overall.get("regime", "UNKNOWN"),
                "factors": {
                    "adx": trend_data.get("adx", 0),
                    "trend_regime": trend_data.get("regime", "UNKNOWN"),
                    "volatility_1hr": vol_data.get("1hr", {}).get("regime", "UNKNOWN"),
                    "correlation_breakdown": corr_data.get("analysis", {}).get("correlation_breakdown", False)
                },
                "timestamp": regime_analysis.get("timestamp", "unknown")
            }
            
            # This could be enhanced to log to the enhanced logging system
            print(f"[REGIME DECISION] {reasoning}")
            
        except Exception as e:
            print(f"[ERROR] Failed to log regime decision: {e}")

    @staticmethod
    def get_strategy_performance_by_regime():
        """Get historical strategy performance by market regime (placeholder for future implementation)"""
        # This could be implemented to track and analyze strategy performance
        # in different market regimes for adaptive learning
        return {
            "VOLATILE_TRENDING": {"best_strategy": "scalp", "avg_return": 0.8},
            "STABLE_TRENDING": {"best_strategy": "vwap", "avg_return": 1.2},
            "VOLATILE_RANGING": {"best_strategy": "range_reversal", "avg_return": 0.9},
            "STABLE_RANGING": {"best_strategy": "orb", "avg_return": 0.7},
            "TRANSITIONAL": {"best_strategy": "orb", "avg_return": 0.5}
        }


# ✅ Externally used function - Enhanced for regime-based selection
def select_best_strategy(
    bot_name="stock-trader", market_context=None, sentiment=None
):
    """Enhanced strategy selection with comprehensive market regime analysis"""
    
    bot_type = (
        "stock"
        if "stock" in bot_name
        else ("futures" if "futures" in bot_name else "options")
    )
    
    # Ensure market_context contains all available information
    current_market_context = market_context
    if sentiment and (not market_context or "sentiment" not in market_context):
        if current_market_context is None:
            current_market_context = {}
        current_market_context["sentiment"] = sentiment

    # Enhanced strategy selection with detailed regime analysis
    strategy, direction = StrategySelector.choose_strategy(
        bot_type, sentiment=sentiment, market_context=current_market_context
    )
    
    # Additional context for the caller
    regime_info = {}
    if current_market_context and "regime_analysis" in current_market_context:
        regime_analysis = current_market_context["regime_analysis"]
        regime_info = {
            "overall_regime": regime_analysis.get("overall_regime", {}).get("regime", "UNKNOWN"),
            "confidence": regime_analysis.get("overall_regime", {}).get("confidence", 0.5),
            "trend_classification": regime_analysis.get("trend_classification", {}).get("regime", "UNKNOWN"),
            "adx": regime_analysis.get("trend_classification", {}).get("adx", 0),
            "volatility_1hr": regime_analysis.get("volatility_regimes", {}).get("1hr", {}).get("regime", "UNKNOWN")
        }
    
    return strategy, direction, regime_info

#!/usr/bin/env python3
"""
Trade Manager - Compatibility Module
Provides standalone functions for backward compatibility with existing futures and options pods.
Wraps the newer EnhancedTradeManager and paper_trade_utils functionality.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from runner.enhanced_trade_manager import EnhancedTradeManager, TradeRequest
from runner.utils.paper_trade_utils import simulate_exit as _simulate_exit
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.config import PAPER_TRADE


# Global instances for backward compatibility
_trade_manager_instance = None
_logger_instance = None


def _get_trade_manager() -> EnhancedTradeManager:
    """Get or create the global trade manager instance"""
    global _trade_manager_instance, _logger_instance
    
    if _trade_manager_instance is None:
        # Create logger if not exists
        if _logger_instance is None:
            today_date = datetime.now().strftime("%Y-%m-%d")
            _logger_instance = Logger(today_date)
        
        # Create enhanced trade manager
        _trade_manager_instance = EnhancedTradeManager(logger=_logger_instance)
        
        # Start trading session
        _trade_manager_instance.start_trading_session()
    
    return _trade_manager_instance


def execute_trade(trade_signal: Dict[str, Any], paper_mode: bool = None) -> Optional[Dict[str, Any]]:
    """
    Execute a trade using the enhanced trade manager
    
    Args:
        trade_signal: Dictionary containing trade details
        paper_mode: Whether to execute in paper mode (defaults to PAPER_TRADE config)
        
    Returns:
        Trade result dictionary or None if failed
    """
    try:
        # Use provided paper_mode or default to config
        if paper_mode is None:
            paper_mode = PAPER_TRADE
        
        # Create trade request from signal
        trade_request = TradeRequest(
            symbol=trade_signal.get('symbol', ''),
            strategy=trade_signal.get('strategy', 'unknown'),
            direction=trade_signal.get('direction', 'bullish'),
            quantity=trade_signal.get('quantity', 1),
            entry_price=trade_signal.get('entry_price', 0.0),
            stop_loss=trade_signal.get('stop_loss', 0.0),
            target=trade_signal.get('target', 0.0),
            bot_type=trade_signal.get('bot_type', 'futures'),
            paper_trade=paper_mode,
            trailing_stop_enabled=trade_signal.get('trailing_stop_enabled', False),
            trailing_stop_distance=trade_signal.get('trailing_stop_distance', 0.0),
            time_based_exit_minutes=trade_signal.get('time_based_exit_minutes', 0),
            max_loss_pct=trade_signal.get('max_loss_pct', 5.0),
            confidence_level=trade_signal.get('confidence_level', 0.5),
            metadata=trade_signal.get('metadata', {})
        )
        
        # Get trade manager and execute
        trade_manager = _get_trade_manager()
        position_id = trade_manager.execute_trade(trade_request)
        
        if position_id:
            # Return success response in expected format
            return {
                'status': 'success',
                'position_id': position_id,
                'symbol': trade_request.symbol,
                'direction': trade_request.direction,
                'quantity': trade_request.quantity,
                'entry_price': trade_request.entry_price,
                'stop_loss': trade_request.stop_loss,
                'target': trade_request.target,
                'paper_trade': paper_mode,
                'timestamp': datetime.now().isoformat(),
                'trade_signal': trade_signal
            }
        else:
            return None
            
    except Exception as e:
        if _logger_instance:
            _logger_instance.log_event(f"Trade execution failed: {e}")
        return None


def simulate_exit(trade: Dict[str, Any], exit_candles: list) -> Dict[str, Any]:
    """
    Simulate trade exit using paper trade utilities
    
    Args:
        trade: Trade dictionary with entry details
        exit_candles: List of price candles for simulation
        
    Returns:
        Updated trade dictionary with exit details
    """
    try:
        return _simulate_exit(trade, exit_candles)
    except Exception as e:
        if _logger_instance:
            _logger_instance.log_event(f"Simulate exit failed: {e}")
        
        # Return trade with error status
        return {
            **trade,
            "exit_price": trade.get("entry_price", 0),
            "exit_reason": f"simulation_error_{str(e)}",
            "status": "error",
            "hold_duration": 0,
            "error": str(e)
        }


def get_active_positions() -> list:
    """Get list of active positions"""
    try:
        trade_manager = _get_trade_manager()
        return trade_manager.get_active_positions()
    except Exception as e:
        if _logger_instance:
            _logger_instance.log_event(f"Failed to get active positions: {e}")
        return []


def get_closed_positions() -> list:
    """Get list of closed positions"""
    try:
        trade_manager = _get_trade_manager()
        return trade_manager.get_closed_positions()
    except Exception as e:
        if _logger_instance:
            _logger_instance.log_event(f"Failed to get closed positions: {e}")
        return []


def emergency_exit_all(reason: str = "Emergency exit") -> bool:
    """Emergency exit all open positions"""
    try:
        trade_manager = _get_trade_manager()
        trade_manager.emergency_exit_all_positions(reason)
        return True
    except Exception as e:
        if _logger_instance:
            _logger_instance.log_event(f"Emergency exit failed: {e}")
        return False


def get_trading_stats() -> Dict[str, Any]:
    """Get trading statistics"""
    try:
        trade_manager = _get_trade_manager()
        return trade_manager.get_trading_stats()
    except Exception as e:
        if _logger_instance:
            _logger_instance.log_event(f"Failed to get trading stats: {e}")
        return {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'paper_trades': 0,
            'real_trades': 0,
            'total_pnl': 0.0,
            'error': str(e)
        }


def stop_trading_session():
    """Stop the trading session and cleanup"""
    global _trade_manager_instance
    
    try:
        if _trade_manager_instance:
            _trade_manager_instance.stop_trading_session()
            _trade_manager_instance = None
        
        if _logger_instance:
            _logger_instance.log_event("Trading session stopped via trade_manager compatibility layer")
            
    except Exception as e:
        if _logger_instance:
            _logger_instance.log_event(f"Error stopping trading session: {e}")


# Compatibility aliases for legacy code
execute_futures_trade = execute_trade
execute_options_trade = execute_trade
simulate_futures_exit = simulate_exit
simulate_options_exit = simulate_exit 
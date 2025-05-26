"""
Enterprise Options Pricing Engine
Supports both paper trading (mock pricing) and live trading (real Black-Scholes calculations)
"""

import math
import numpy as np
from config.config_manager import get_trading_config
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from threading import Lock

try:
    from scipy.stats import norm
    from scipy.optimize import brentq
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("WARNING: scipy not available, using approximations for options pricing")


@dataclass
class OptionData:
    symbol: str
    strike: float
    expiry: datetime
    option_type: str  # 'CE' or 'PE'
    spot: float
    market_price: float
    iv: Optional[float] = None
    greeks: Optional[Dict] = None
    is_mock: bool = False
    liquidity_score: float = 0.0


@dataclass
class GreeksData:
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    is_mock: bool = False


class OptionsEngine:
    """Enterprise options pricing and Greeks engine with paper trade support"""
    
    def __init__(self, paper_trade: bool = None, risk_free_rate: float = 0.06):
        # Use configuration file if not explicitly set
        if paper_trade is None:
            config = get_trading_config()
            paper_trade = config.paper_trade
        
        self.paper_trade = paper_trade
        self.rf_rate = risk_free_rate
        self.iv_cache = {}
        self._cache_lock = Lock()
        
        # Mock data for paper trading
        self.mock_iv_base = 0.20  # 20% base IV
        self.mock_greeks_base = {
            'delta': 0.5,
            'gamma': 0.05,
            'theta': -0.01,
            'vega': 0.1,
            'rho': 0.01
        }
        
        if not SCIPY_AVAILABLE and not paper_trade:
            print("WARNING: Running live trading without scipy - falling back to approximations")
    
    def black_scholes_price(self, S: float, K: float, T: float, 
                           r: float, sigma: float, option_type: str) -> float:
        """Black-Scholes option pricing with fallback for paper trading"""
        
        if self.paper_trade:
            return self._mock_option_price(S, K, T, option_type)
        
        # Handle edge cases
        if T <= 0:
            intrinsic = max(0, S - K) if option_type == 'CE' else max(0, K - S)
            return intrinsic
        
        if sigma <= 0:
            sigma = 0.01  # Minimum volatility
        
        try:
            if SCIPY_AVAILABLE:
                # Real Black-Scholes calculation
                d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
                d2 = d1 - sigma*np.sqrt(T)
                
                if option_type == 'CE':
                    return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
                else:
                    return K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)
            else:
                # Approximation without scipy
                return self._approximate_option_price(S, K, T, r, sigma, option_type)
                
        except Exception as e:
            print(f"Black-Scholes calculation error: {e}, using approximation")
            return self._approximate_option_price(S, K, T, r, sigma, option_type)
    
    def implied_volatility(self, market_price: float, S: float, K: float, 
                          T: float, r: float, option_type: str) -> float:
        """Calculate implied volatility with paper trading support"""
        
        if self.paper_trade:
            return self._mock_implied_volatility(S, K, T, option_type)
        
        if T <= 0 or market_price <= 0:
            return self.mock_iv_base
        
        # Check cache first
        cache_key = f"{S}_{K}_{T}_{option_type}_{market_price}"
        with self._cache_lock:
            if cache_key in self.iv_cache:
                return self.iv_cache[cache_key]
        
        try:
            if SCIPY_AVAILABLE:
                # Newton-Raphson method for IV calculation
                def objective(sigma):
                    try:
                        return self.black_scholes_price(S, K, T, r, sigma, option_type) - market_price
                    except:
                        return float('inf')
                
                # Use Brent's method for robust convergence
                iv = brentq(objective, 0.01, 5.0, xtol=1e-6, maxiter=100)
                iv = max(0.01, min(iv, 5.0))  # Cap between 1% and 500%
                
                # Cache the result
                with self._cache_lock:
                    self.iv_cache[cache_key] = iv
                    
                return iv
            else:
                # Approximation method
                return self._approximate_implied_volatility(market_price, S, K, T, r, option_type)
                
        except Exception as e:
            print(f"IV calculation error: {e}, using default IV")
            return self.mock_iv_base
    
    def calculate_greeks(self, S: float, K: float, T: float, 
                        r: float, sigma: float, option_type: str) -> GreeksData:
        """Calculate option Greeks with paper trading support"""
        
        if self.paper_trade:
            return self._mock_greeks(S, K, T, option_type)
        
        if T <= 0:
            return GreeksData(0, 0, 0, 0, 0, is_mock=False)
        
        try:
            if SCIPY_AVAILABLE:
                # Real Greeks calculation
                d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
                d2 = d1 - sigma*np.sqrt(T)
                
                # Delta
                if option_type == 'CE':
                    delta = norm.cdf(d1)
                else:
                    delta = norm.cdf(d1) - 1
                    
                # Gamma (same for calls and puts)
                gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
                
                # Theta
                term1 = -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                if option_type == 'CE':
                    term2 = -r * K * np.exp(-r*T) * norm.cdf(d2)
                else:
                    term2 = r * K * np.exp(-r*T) * norm.cdf(-d2)
                theta = (term1 + term2) / 365  # Per day
                
                # Vega (same for calls and puts)
                vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% change
                
                # Rho
                if option_type == 'CE':
                    rho = K * T * np.exp(-r*T) * norm.cdf(d2) / 100
                else:
                    rho = -K * T * np.exp(-r*T) * norm.cdf(-d2) / 100
                    
                return GreeksData(
                    delta=delta,
                    gamma=gamma,
                    theta=theta,
                    vega=vega,
                    rho=rho,
                    is_mock=False
                )
            else:
                # Approximation method
                return self._approximate_greeks(S, K, T, r, sigma, option_type)
                
        except Exception as e:
            print(f"Greeks calculation error: {e}, using approximation")
            return self._approximate_greeks(S, K, T, r, sigma, option_type)
    
    async def analyze_option_chain(self, kite, symbol: str, 
                                  spot_price: float, expiry_date: str = None) -> List[OptionData]:
        """Analyze complete option chain with real-time or mock pricing"""
        
        if self.paper_trade:
            return self._mock_option_chain(symbol, spot_price, expiry_date)
        
        try:
            # Get instruments from Kite
            instruments = kite.instruments('NFO')
            
            # Determine expiry date
            if not expiry_date:
                expiry_date = self._get_next_expiry()
            
            # Filter options for the symbol and expiry
            options = [inst for inst in instruments 
                      if inst['name'] == symbol.upper() and 
                      inst['expiry'] == expiry_date and
                      inst['instrument_type'] in ['CE', 'PE']]
            
            if not options:
                print(f"No options found for {symbol} expiry {expiry_date}")
                return self._mock_option_chain(symbol, spot_price, expiry_date)
            
            option_data = []
            
            # Get LTP for all options
            symbols_list = [f"NFO:{opt['tradingsymbol']}" for opt in options[:50]]  # Limit to avoid rate limits
            ltp_data = kite.ltp(symbols_list)
            
            expiry_datetime = datetime.strptime(expiry_date, '%Y-%m-%d')
            T = max((expiry_datetime.date() - datetime.now().date()).days / 365.0, 0.001)
            
            for opt in options[:50]:  # Process limited options to avoid timeouts
                symbol_key = f"NFO:{opt['tradingsymbol']}"
                market_price = ltp_data.get(symbol_key, {}).get('last_price', 0)
                
                if market_price > 0.5:  # Only process options with meaningful price
                    try:
                        # Calculate IV
                        iv = self.implied_volatility(
                            market_price, spot_price, opt['strike'], 
                            T, self.rf_rate, opt['instrument_type']
                        )
                        
                        # Calculate Greeks
                        greeks = self.calculate_greeks(
                            spot_price, opt['strike'], T, 
                            self.rf_rate, iv, opt['instrument_type']
                        )
                        
                        # Calculate liquidity score (simplified)
                        liquidity_score = min(market_price / (abs(spot_price - opt['strike']) + 1), 1.0)
                        
                        option_data.append(OptionData(
                            symbol=opt['tradingsymbol'],
                            strike=opt['strike'],
                            expiry=expiry_datetime,
                            option_type=opt['instrument_type'],
                            spot=spot_price,
                            market_price=market_price,
                            iv=iv,
                            greeks=greeks.__dict__,
                            is_mock=False,
                            liquidity_score=liquidity_score
                        ))
                    except Exception as e:
                        print(f"Error processing option {opt['tradingsymbol']}: {e}")
                        continue
            
            return option_data
            
        except Exception as e:
            print(f"Option chain analysis error: {e}, falling back to mock data")
            return self._mock_option_chain(symbol, spot_price, expiry_date)
    
    def select_optimal_strikes(self, option_chain: List[OptionData], 
                             strategy: str, direction: str, capital: float = 100000) -> Dict:
        """Select optimal strikes based on strategy and direction"""
        
        if not option_chain:
            return {}
        
        if strategy == 'scalp':
            return self._select_scalp_strikes(option_chain, direction, capital)
        elif strategy == 'momentum':
            return self._select_momentum_strikes(option_chain, direction, capital)
        elif strategy == 'swing':
            return self._select_swing_strikes(option_chain, direction, capital)
        else:
            return self._select_default_strikes(option_chain, direction, capital)
    
    def _select_scalp_strikes(self, chain: List[OptionData], direction: str, capital: float) -> Dict:
        """Select strikes optimized for scalping"""
        spot = chain[0].spot
        
        if direction == 'bullish':
            # For scalping, prefer ITM/ATM calls with high delta, reasonable theta
            calls = [opt for opt in chain if opt.option_type == 'CE' and opt.strike <= spot * 1.02]
            candidates = sorted(calls, key=lambda x: (
                -x.greeks.get('delta', 0),  # Higher delta preferred
                abs(x.greeks.get('theta', 0)),  # Lower theta decay preferred
                -x.liquidity_score  # Higher liquidity preferred
            ))
        else:
            # For bearish scalping, prefer ITM/ATM puts
            puts = [opt for opt in chain if opt.option_type == 'PE' and opt.strike >= spot * 0.98]
            candidates = sorted(puts, key=lambda x: (
                x.greeks.get('delta', 0),  # More negative delta preferred for puts
                abs(x.greeks.get('theta', 0)),
                -x.liquidity_score
            ))
        
        if candidates:
            best_option = candidates[0]
            max_quantity = int(capital * 0.1 / best_option.market_price)  # 10% of capital
            
            return {
                'primary': best_option,
                'quantity': max_quantity,
                'strategy_params': {
                    'max_loss': best_option.market_price * 0.5 * max_quantity,
                    'target_profit': best_option.market_price * 0.3 * max_quantity,
                    'stop_loss_pct': 0.5,
                    'target_profit_pct': 0.3
                },
                'risk_metrics': {
                    'delta_exposure': best_option.greeks.get('delta', 0) * max_quantity,
                    'gamma_risk': best_option.greeks.get('gamma', 0) * max_quantity,
                    'theta_decay': best_option.greeks.get('theta', 0) * max_quantity
                }
            }
        
        return {}
    
    def _select_momentum_strikes(self, chain: List[OptionData], direction: str, capital: float) -> Dict:
        """Select strikes for momentum trading"""
        spot = chain[0].spot
        
        if direction == 'bullish':
            # Slightly OTM calls for momentum
            calls = [opt for opt in chain 
                    if opt.option_type == 'CE' and 
                    spot * 1.01 <= opt.strike <= spot * 1.05]
        else:
            # Slightly OTM puts for momentum
            puts = [opt for opt in chain 
                   if opt.option_type == 'PE' and 
                   spot * 0.95 <= opt.strike <= spot * 0.99]
            calls = puts
        
        if calls:
            # Select based on best risk-reward
            best_option = max(calls, key=lambda x: x.liquidity_score * abs(x.greeks.get('delta', 0)))
            max_quantity = int(capital * 0.15 / best_option.market_price)  # 15% of capital
            
            return {
                'primary': best_option,
                'quantity': max_quantity,
                'strategy_params': {
                    'max_loss': best_option.market_price * 0.6 * max_quantity,
                    'target_profit': best_option.market_price * 0.8 * max_quantity,
                    'stop_loss_pct': 0.6,
                    'target_profit_pct': 0.8
                }
            }
        
        return {}
    
    def _select_swing_strikes(self, chain: List[OptionData], direction: str, capital: float) -> Dict:
        """Select strikes for swing trading"""
        spot = chain[0].spot
        
        # For swing trading, prefer ATM options with good time value
        if direction == 'bullish':
            options = [opt for opt in chain 
                      if opt.option_type == 'CE' and 
                      spot * 0.98 <= opt.strike <= spot * 1.02]
        else:
            options = [opt for opt in chain 
                      if opt.option_type == 'PE' and 
                      spot * 0.98 <= opt.strike <= spot * 1.02]
        
        if options:
            # Select based on time value and liquidity
            best_option = max(options, key=lambda x: x.liquidity_score * x.market_price)
            max_quantity = int(capital * 0.2 / best_option.market_price)  # 20% of capital
            
            return {
                'primary': best_option,
                'quantity': max_quantity,
                'strategy_params': {
                    'max_loss': best_option.market_price * 0.4 * max_quantity,
                    'target_profit': best_option.market_price * 1.0 * max_quantity,
                    'stop_loss_pct': 0.4,
                    'target_profit_pct': 1.0
                }
            }
        
        return {}
    
    def _select_default_strikes(self, chain: List[OptionData], direction: str, capital: float) -> Dict:
        """Default strike selection"""
        spot = chain[0].spot
        
        # Simple ATM selection
        if direction == 'bullish':
            options = [opt for opt in chain if opt.option_type == 'CE']
        else:
            options = [opt for opt in chain if opt.option_type == 'PE']
        
        if options:
            # Select closest to ATM
            best_option = min(options, key=lambda x: abs(x.strike - spot))
            max_quantity = int(capital * 0.1 / best_option.market_price)
            
            return {
                'primary': best_option,
                'quantity': max_quantity,
                'strategy_params': {
                    'max_loss': best_option.market_price * 0.5 * max_quantity,
                    'target_profit': best_option.market_price * 0.5 * max_quantity
                }
            }
        
        return {}
    
    # Mock methods for paper trading
    def _mock_option_price(self, S: float, K: float, T: float, option_type: str) -> float:
        """Mock option pricing for paper trading"""
        intrinsic = max(0, S - K) if option_type == 'CE' else max(0, K - S)
        time_value = K * 0.01 * np.sqrt(T) * self.mock_iv_base  # Simplified time value
        return intrinsic + time_value
    
    def _mock_implied_volatility(self, S: float, K: float, T: float, option_type: str) -> float:
        """Mock IV calculation"""
        # IV varies based on moneyness
        moneyness = S / K if K > 0 else 1
        
        if option_type == 'CE':
            if moneyness > 1.02:  # ITM call
                return self.mock_iv_base * 0.9
            elif moneyness < 0.98:  # OTM call
                return self.mock_iv_base * 1.2
        else:  # PE
            if moneyness < 0.98:  # ITM put
                return self.mock_iv_base * 0.9
            elif moneyness > 1.02:  # OTM put
                return self.mock_iv_base * 1.2
        
        return self.mock_iv_base  # ATM
    
    def _mock_greeks(self, S: float, K: float, T: float, option_type: str) -> GreeksData:
        """Mock Greeks calculation"""
        moneyness = S / K if K > 0 else 1
        
        if option_type == 'CE':
            delta = max(0.1, min(0.9, 0.5 + (moneyness - 1) * 2))
        else:
            delta = max(-0.9, min(-0.1, -0.5 + (1 - moneyness) * 2))
        
        gamma = self.mock_greeks_base['gamma'] * (1 - abs(moneyness - 1))
        theta = self.mock_greeks_base['theta'] * T
        vega = self.mock_greeks_base['vega'] * np.sqrt(T)
        rho = self.mock_greeks_base['rho'] * T
        
        return GreeksData(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            is_mock=True
        )
    
    def _mock_option_chain(self, symbol: str, spot_price: float, expiry_date: str = None) -> List[OptionData]:
        """Generate mock option chain for paper trading"""
        if not expiry_date:
            expiry_date = self._get_next_expiry()
        
        expiry_datetime = datetime.strptime(expiry_date, '%Y-%m-%d')
        T = max((expiry_datetime.date() - datetime.now().date()).days / 365.0, 0.001)
        
        option_data = []
        
        # Generate strikes around spot price
        base_strike = round(spot_price / 100) * 100
        strikes = [base_strike + i * 100 for i in range(-5, 6)]
        
        for strike in strikes:
            for option_type in ['CE', 'PE']:
                mock_price = self._mock_option_price(spot_price, strike, T, option_type)
                mock_iv = self._mock_implied_volatility(spot_price, strike, T, option_type)
                mock_greeks = self._mock_greeks(spot_price, strike, T, option_type)
                
                option_data.append(OptionData(
                    symbol=f"{symbol}{expiry_date.replace('-', '')}{int(strike)}{option_type}",
                    strike=strike,
                    expiry=expiry_datetime,
                    option_type=option_type,
                    spot=spot_price,
                    market_price=mock_price,
                    iv=mock_iv,
                    greeks=mock_greeks.__dict__,
                    is_mock=True,
                    liquidity_score=0.8
                ))
        
        return option_data
    
    def _get_next_expiry(self) -> str:
        """Get next Thursday expiry date"""
        today = datetime.now().date()
        days_ahead = 3 - today.weekday()  # Thursday = 3
        if days_ahead <= 0:
            days_ahead += 7
        next_expiry = today + timedelta(days=days_ahead)
        return next_expiry.strftime('%Y-%m-%d')
    
    def _approximate_option_price(self, S: float, K: float, T: float, 
                                 r: float, sigma: float, option_type: str) -> float:
        """Approximation method when scipy is not available"""
        # Simple approximation using intrinsic + time value
        intrinsic = max(0, S - K) if option_type == 'CE' else max(0, K - S)
        time_value = K * sigma * np.sqrt(T) * 0.4  # Simplified
        return intrinsic + time_value
    
    def _approximate_implied_volatility(self, market_price: float, S: float, K: float, 
                                       T: float, r: float, option_type: str) -> float:
        """Approximation method for IV when scipy is not available"""
        # Simple iterative approximation
        for iv in np.arange(0.1, 3.0, 0.1):
            approx_price = self._approximate_option_price(S, K, T, r, iv, option_type)
            if abs(approx_price - market_price) < market_price * 0.05:
                return iv
        return self.mock_iv_base
    
    def _approximate_greeks(self, S: float, K: float, T: float, 
                           r: float, sigma: float, option_type: str) -> GreeksData:
        """Approximation method for Greeks when scipy is not available"""
        # Simplified Greeks calculation
        moneyness = S / K
        
        if option_type == 'CE':
            delta = 0.5 if abs(moneyness - 1) < 0.02 else (0.8 if moneyness > 1 else 0.2)
        else:
            delta = -0.5 if abs(moneyness - 1) < 0.02 else (-0.8 if moneyness < 1 else -0.2)
        
        gamma = 0.05 / (sigma * np.sqrt(T))
        theta = -S * sigma / (2 * np.sqrt(T)) / 365
        vega = S * np.sqrt(T) / 100
        rho = K * T * 0.01 if option_type == 'CE' else -K * T * 0.01
        
        return GreeksData(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            is_mock=False
        )
    
    def get_engine_status(self) -> Dict:
        """Get engine status and configuration"""
        return {
            'paper_trade': self.paper_trade,
            'scipy_available': SCIPY_AVAILABLE,
            'risk_free_rate': self.rf_rate,
            'cache_size': len(self.iv_cache),
            'mock_iv_base': self.mock_iv_base if self.paper_trade else None,
            'available_strategies': ['scalp', 'momentum', 'swing', 'default']
        }


# Factory function for backward compatibility
def create_options_engine(paper_trade: bool = None) -> OptionsEngine:
    """Create OptionsEngine instance"""
    return OptionsEngine(paper_trade=paper_trade)


# Backward compatibility functions
def calculate_implied_volatility(option_price: float, strike_price: float,
                               spot_price: float, time_to_expiry: float,
                               interest_rate: float = 0.06, option_type: str = "call",
                               paper_trade: bool = None) -> float:
    """Calculate implied volatility - backward compatible function"""
    engine = OptionsEngine(paper_trade=paper_trade,
                           risk_free_rate=interest_rate)
    option_type_code = 'CE' if option_type.lower() == 'call' else 'PE'
    return engine.implied_volatility(option_price, spot_price, strike_price, 
                                   time_to_expiry, interest_rate, option_type_code)


def calculate_greeks(option_price: float, strike_price: float, spot_price: float,
                    time_to_expiry: float, interest_rate: float = 0.06,
                    volatility: float = 0.2, option_type: str = "call",
                    paper_trade: bool = None) -> Dict:
    """Calculate option Greeks - backward compatible function"""
    engine = OptionsEngine(paper_trade=paper_trade,
                           risk_free_rate=interest_rate)
    option_type_code = 'CE' if option_type.lower() == 'call' else 'PE'
    greeks = engine.calculate_greeks(spot_price, strike_price, time_to_expiry, 
                                   interest_rate, volatility, option_type_code)
    return greeks.__dict__
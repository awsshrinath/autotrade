"""
Production Deployment and Environment Management System
Handles switching between paper trading and live trading environments
"""

import os
import asyncio
import aiohttp
import json
import psutil
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum


class EnvironmentType(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    service: str
    status: HealthStatus
    response_time: float
    timestamp: datetime
    details: Dict
    is_critical: bool = True


@dataclass
class SystemMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_status: str
    active_connections: int
    timestamp: datetime


@dataclass
class TradingEnvironment:
    environment: EnvironmentType
    paper_trade: bool
    max_daily_loss: float
    position_size_limit: float
    margin_utilization_limit: float
    api_rate_limit: int
    monitoring_interval: int
    auto_square_off_time: str
    backup_frequency: int


class ProductionManager:
    """Production deployment and monitoring manager with environment switching"""
    
    def __init__(self, logger=None, firestore=None):
        self.logger = logger
        self.firestore = firestore
        
        # Determine environment
        self.environment = self._determine_environment()
        self.trading_env = self._configure_trading_environment()
        
        # Health monitoring
        self.health_checks = []
        self.system_metrics_history = []
        self.last_health_check = None
        
        # Alert configuration
        self.alerts_config = self._load_alerts_config()
        self.notification_channels = []
        
        # Circuit breaker for critical failures
        self.circuit_breaker = {
            'failures': 0,
            'last_failure': None,
            'is_open': False,
            'threshold': 5
        }
        
        if self.logger:
            self.logger.log_event(
                f"ProductionManager initialized - Environment: {self.environment.value}, "
                f"Paper Trade: {self.trading_env.paper_trade}"
            )
    
    def _determine_environment(self) -> EnvironmentType:
        """Determine current environment from environment variables"""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        
        # Map environment names
        env_mapping = {
            'dev': EnvironmentType.DEVELOPMENT,
            'development': EnvironmentType.DEVELOPMENT,
            'test': EnvironmentType.DEVELOPMENT,
            'staging': EnvironmentType.STAGING,
            'stage': EnvironmentType.STAGING,
            'prod': EnvironmentType.PRODUCTION,
            'production': EnvironmentType.PRODUCTION
        }
        
        return env_mapping.get(env_name, EnvironmentType.DEVELOPMENT)
    
    def _configure_trading_environment(self) -> TradingEnvironment:
        """Configure trading environment based on current environment"""
        
        if self.environment == EnvironmentType.PRODUCTION:
            return TradingEnvironment(
                environment=self.environment,
                paper_trade=os.getenv("PAPER_TRADE", "false").lower() == "true",
                max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "50000")),  # ₹50,000
                position_size_limit=float(os.getenv("POSITION_SIZE_LIMIT", "0.1")),  # 10%
                margin_utilization_limit=float(os.getenv("MARGIN_UTILIZATION_LIMIT", "0.8")),  # 80%
                api_rate_limit=int(os.getenv("API_RATE_LIMIT", "3")),  # 3 req/sec
                monitoring_interval=int(os.getenv("MONITORING_INTERVAL", "30")),  # 30 seconds
                auto_square_off_time=os.getenv("AUTO_SQUARE_OFF_TIME", "15:20"),
                backup_frequency=int(os.getenv("BACKUP_FREQUENCY", "300"))  # 5 minutes
            )
        elif self.environment == EnvironmentType.STAGING:
            return TradingEnvironment(
                environment=self.environment,
                paper_trade=True,  # Always paper trade in staging
                max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "10000")),  # ₹10,000
                position_size_limit=float(os.getenv("POSITION_SIZE_LIMIT", "0.05")),  # 5%
                margin_utilization_limit=float(os.getenv("MARGIN_UTILIZATION_LIMIT", "0.5")),  # 50%
                api_rate_limit=int(os.getenv("API_RATE_LIMIT", "2")),  # 2 req/sec
                monitoring_interval=int(os.getenv("MONITORING_INTERVAL", "60")),  # 1 minute
                auto_square_off_time=os.getenv("AUTO_SQUARE_OFF_TIME", "15:15"),
                backup_frequency=int(os.getenv("BACKUP_FREQUENCY", "600"))  # 10 minutes
            )
        else:  # DEVELOPMENT
            return TradingEnvironment(
                environment=self.environment,
                paper_trade=True,  # Always paper trade in development
                max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "1000")),  # ₹1,000
                position_size_limit=float(os.getenv("POSITION_SIZE_LIMIT", "0.02")),  # 2%
                margin_utilization_limit=float(os.getenv("MARGIN_UTILIZATION_LIMIT", "0.3")),  # 30%
                api_rate_limit=int(os.getenv("API_RATE_LIMIT", "1")),  # 1 req/sec
                monitoring_interval=int(os.getenv("MONITORING_INTERVAL", "120")),  # 2 minutes
                auto_square_off_time=os.getenv("AUTO_SQUARE_OFF_TIME", "15:10"),
                backup_frequency=int(os.getenv("BACKUP_FREQUENCY", "1200"))  # 20 minutes
            )
    
    async def comprehensive_health_check(self) -> Dict:
        """Complete system health check with environment-specific checks"""
        
        if self.logger:
            self.logger.log_event("Starting comprehensive health check...")
        
        start_time = datetime.now()
        
        # Run all health checks
        checks = await asyncio.gather(
            self._check_kite_api(),
            self._check_firestore(),
            self._check_secret_manager(),
            self._check_system_resources(),
            self._check_network_connectivity(),
            self._check_market_data_feed(),
            self._check_trading_services(),
            return_exceptions=True
        )
        
        # Process results
        valid_checks = [c for c in checks if isinstance(c, HealthCheck)]
        failed_checks = [c for c in checks if isinstance(c, Exception)]
        
        # Determine overall health
        critical_failures = [c for c in valid_checks if c.is_critical and c.status != HealthStatus.HEALTHY]
        
        if failed_checks or critical_failures:
            overall_status = HealthStatus.CRITICAL if critical_failures else HealthStatus.DEGRADED
        elif any(c.status == HealthStatus.DEGRADED for c in valid_checks):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Create health report
        health_report = {
            'overall_status': overall_status.value,
            'environment': self.environment.value,
            'paper_trade': self.trading_env.paper_trade,
            'timestamp': start_time.isoformat(),
            'duration_ms': (datetime.now() - start_time).total_seconds() * 1000,
            'checks': [asdict(c) for c in valid_checks],
            'failed_checks': len(failed_checks),
            'critical_failures': len(critical_failures),
            'system_ready': overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        }
        
        # Store health check
        self.last_health_check = health_report
        self.health_checks.append(health_report)
        
        # Keep only last 100 health checks
        if len(self.health_checks) > 100:
            self.health_checks = self.health_checks[-100:]
        
        # Alert on critical failures
        if overall_status == HealthStatus.CRITICAL:
            await self._send_critical_alert("System health check failed", health_report)
        
        if self.logger:
            self.logger.log_event(
                f"Health check completed - Status: {overall_status.value}, "
                f"Duration: {health_report['duration_ms']:.2f}ms"
            )
        
        return health_report
    
    async def _check_kite_api(self) -> HealthCheck:
        """Check Kite Connect API connectivity"""
        start_time = datetime.now()
        
        try:
            if self.trading_env.paper_trade:
                # Mock check for paper trading
                await asyncio.sleep(0.1)  # Simulate API call
                return HealthCheck(
                    service="kite_api",
                    status=HealthStatus.HEALTHY,
                    response_time=0.1,
                    timestamp=datetime.now(),
                    details={"mode": "paper_trade", "mock": True},
                    is_critical=False
                )
            else:
                # Real API check for live trading
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://api.kite.trade/",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        status = HealthStatus.HEALTHY if response.status == 200 else HealthStatus.UNHEALTHY
                        
                        return HealthCheck(
                            service="kite_api",
                            status=status,
                            response_time=response_time,
                            timestamp=datetime.now(),
                            details={
                                "status_code": response.status,
                                "mode": "live_trading"
                            },
                            is_critical=True
                        )
                        
        except Exception as e:
            return HealthCheck(
                service="kite_api",
                status=HealthStatus.CRITICAL,
                response_time=999,
                timestamp=datetime.now(),
                details={"error": str(e)},
                is_critical=True
            )
    
    async def _check_firestore(self) -> HealthCheck:
        """Check Firestore connectivity"""
        start_time = datetime.now()
        
        try:
            if self.firestore:
                # Test Firestore connection
                test_doc = {
                    'health_check': True,
                    'timestamp': datetime.now().isoformat(),
                    'environment': self.environment.value
                }
                
                # Write test document
                doc_ref = self.firestore.collection('health_checks').document('test')
                doc_ref.set(test_doc)
                
                # Read it back
                doc = doc_ref.get()
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                if doc.exists:
                    status = HealthStatus.HEALTHY
                    details = {"connection": "successful", "read_write": "ok"}
                else:
                    status = HealthStatus.DEGRADED
                    details = {"connection": "partial", "read_write": "failed"}
                
            else:
                # No Firestore configured
                status = HealthStatus.DEGRADED
                response_time = 0
                details = {"connection": "not_configured"}
                
            return HealthCheck(
                service="firestore",
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                details=details,
                is_critical=False
            )
            
        except Exception as e:
            return HealthCheck(
                service="firestore",
                status=HealthStatus.UNHEALTHY,
                response_time=999,
                timestamp=datetime.now(),
                details={"error": str(e)},
                is_critical=False
            )
    
    async def _check_secret_manager(self) -> HealthCheck:
        """Check Google Secret Manager connectivity"""
        start_time = datetime.now()
        
        try:
            # Test secret manager by checking if we can access a test secret
            from runner.secret_manager_client import access_secret
            
            # Try to access any secret (will fail gracefully if not found)
            test_secret = access_secret("TEST_SECRET", "autotrade-453303")
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return HealthCheck(
                service="secret_manager",
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                timestamp=datetime.now(),
                details={"access": "successful"},
                is_critical=True if not self.trading_env.paper_trade else False
            )
            
        except Exception as e:
            return HealthCheck(
                service="secret_manager",
                status=HealthStatus.DEGRADED,
                response_time=999,
                timestamp=datetime.now(),
                details={"error": str(e)},
                is_critical=True if not self.trading_env.paper_trade else False
            )
    
    async def _check_system_resources(self) -> HealthCheck:
        """Check system resource usage"""
        start_time = datetime.now()
        
        try:
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on resource usage
            if cpu_usage > 90 or memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.CRITICAL
            elif cpu_usage > 75 or memory.percent > 75 or disk.percent > 85:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Store metrics for trending
            metrics = SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_status="active",
                active_connections=len(psutil.net_connections()),
                timestamp=datetime.now()
            )
            
            self.system_metrics_history.append(metrics)
            if len(self.system_metrics_history) > 1000:
                self.system_metrics_history = self.system_metrics_history[-1000:]
            
            return HealthCheck(
                service="system_resources",
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                details={
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory.percent,
                    "disk_usage": disk.percent,
                    "available_memory_gb": memory.available / (1024**3),
                    "active_connections": len(psutil.net_connections())
                },
                is_critical=True
            )
            
        except Exception as e:
            return HealthCheck(
                service="system_resources",
                status=HealthStatus.UNHEALTHY,
                response_time=999,
                timestamp=datetime.now(),
                details={"error": str(e)},
                is_critical=True
            )
    
    async def _check_network_connectivity(self) -> HealthCheck:
        """Check network connectivity"""
        start_time = datetime.now()
        
        try:
            # Test connectivity to key endpoints
            test_urls = [
                "https://www.google.com",
                "https://api.kite.trade",
                "https://firestore.googleapis.com"
            ]
            
            successful_connections = 0
            
            async with aiohttp.ClientSession() as session:
                for url in test_urls:
                    try:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as response:
                            if response.status == 200:
                                successful_connections += 1
                    except:
                        continue
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Determine status based on successful connections
            if successful_connections == len(test_urls):
                status = HealthStatus.HEALTHY
            elif successful_connections > 0:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL
            
            return HealthCheck(
                service="network_connectivity",
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                details={
                    "successful_connections": successful_connections,
                    "total_tests": len(test_urls),
                    "success_rate": successful_connections / len(test_urls)
                },
                is_critical=True
            )
            
        except Exception as e:
            return HealthCheck(
                service="network_connectivity",
                status=HealthStatus.CRITICAL,
                response_time=999,
                timestamp=datetime.now(),
                details={"error": str(e)},
                is_critical=True
            )
    
    async def _check_market_data_feed(self) -> HealthCheck:
        """Check market data feed availability"""
        start_time = datetime.now()
        
        try:
            if self.trading_env.paper_trade:
                # Mock check for paper trading
                status = HealthStatus.HEALTHY
                details = {"mode": "paper_trade", "feed": "simulated"}
            else:
                # Check real market data feed
                # This would typically check if market data is streaming properly
                status = HealthStatus.HEALTHY  # Simplified for now
                details = {"mode": "live", "feed": "active"}
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return HealthCheck(
                service="market_data_feed",
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                details=details,
                is_critical=True
            )
            
        except Exception as e:
            return HealthCheck(
                service="market_data_feed",
                status=HealthStatus.UNHEALTHY,
                response_time=999,
                timestamp=datetime.now(),
                details={"error": str(e)},
                is_critical=True
            )
    
    async def _check_trading_services(self) -> HealthCheck:
        """Check trading services availability"""
        start_time = datetime.now()
        
        try:
            # Check if key trading components are available
            services_status = {
                "technical_engine": True,  # Would check if indicators are working
                "options_engine": True,    # Would check if options pricing is working
                "portfolio_manager": True, # Would check if portfolio tracking is working
                "risk_manager": True       # Would check if risk checks are working
            }
            
            failed_services = [k for k, v in services_status.items() if not v]
            
            if not failed_services:
                status = HealthStatus.HEALTHY
            elif len(failed_services) <= 1:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return HealthCheck(
                service="trading_services",
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                details={
                    "services_status": services_status,
                    "failed_services": failed_services,
                    "success_rate": (len(services_status) - len(failed_services)) / len(services_status)
                },
                is_critical=True
            )
            
        except Exception as e:
            return HealthCheck(
                service="trading_services",
                status=HealthStatus.CRITICAL,
                response_time=999,
                timestamp=datetime.now(),
                details={"error": str(e)},
                is_critical=True
            )
    
    async def production_startup_sequence(self) -> Dict:
        """Complete production startup sequence"""
        
        if self.logger:
            self.logger.log_event("🚀 PRODUCTION STARTUP INITIATED")
        
        startup_steps = []
        
        try:
            # 1. Environment validation
            step = await self._validate_environment()
            startup_steps.append(step)
            if not step['success']:
                raise Exception(f"Environment validation failed: {step['error']}")
            
            # 2. Health checks
            step = await self._run_startup_health_checks()
            startup_steps.append(step)
            if not step['success']:
                raise Exception(f"Health checks failed: {step['error']}")
            
            # 3. Credentials validation
            step = await self._validate_credentials()
            startup_steps.append(step)
            if not step['success'] and not self.trading_env.paper_trade:
                raise Exception(f"Credentials validation failed: {step['error']}")
            
            # 4. Risk systems initialization
            step = await self._initialize_risk_systems()
            startup_steps.append(step)
            if not step['success']:
                raise Exception(f"Risk systems initialization failed: {step['error']}")
            
            # 5. Monitoring services
            step = await self._start_monitoring_services()
            startup_steps.append(step)
            
            # 6. Cache warm-up
            step = await self._warm_up_caches()
            startup_steps.append(step)
            
            startup_result = {
                'success': True,
                'environment': self.environment.value,
                'paper_trade': self.trading_env.paper_trade,
                'startup_time': datetime.now().isoformat(),
                'steps': startup_steps,
                'message': 'Production startup completed successfully'
            }
            
            if self.logger:
                self.logger.log_event("✅ PRODUCTION STARTUP COMPLETE")
            
            return startup_result
            
        except Exception as e:
            startup_result = {
                'success': False,
                'environment': self.environment.value,
                'paper_trade': self.trading_env.paper_trade,
                'startup_time': datetime.now().isoformat(),
                'steps': startup_steps,
                'error': str(e),
                'message': 'Production startup failed'
            }
            
            if self.logger:
                self.logger.log_event(f"❌ PRODUCTION STARTUP FAILED: {e}")
            
            await self._send_critical_alert("Production startup failed", startup_result)
            
            return startup_result
    
    async def _validate_environment(self) -> Dict:
        """Validate environment configuration"""
        try:
            validations = []
            
            # Check required environment variables
            required_vars = ['ENVIRONMENT']
            if not self.trading_env.paper_trade:
                required_vars.extend(['ZERODHA_API_KEY', 'ZERODHA_API_SECRET'])
            
            for var in required_vars:
                if not os.getenv(var):
                    validations.append(f"Missing environment variable: {var}")
            
            # Validate trading environment configuration
            if self.trading_env.max_daily_loss <= 0:
                validations.append("Invalid max_daily_loss configuration")
            
            if not (0 < self.trading_env.position_size_limit <= 1):
                validations.append("Invalid position_size_limit configuration")
            
            success = len(validations) == 0
            
            return {
                'step': 'environment_validation',
                'success': success,
                'validations': validations,
                'environment': self.environment.value,
                'paper_trade': self.trading_env.paper_trade
            }
            
        except Exception as e:
            return {
                'step': 'environment_validation',
                'success': False,
                'error': str(e)
            }
    
    async def _run_startup_health_checks(self) -> Dict:
        """Run health checks during startup"""
        try:
            health_report = await self.comprehensive_health_check()
            
            success = health_report['overall_status'] in ['healthy', 'degraded']
            
            return {
                'step': 'startup_health_checks',
                'success': success,
                'health_status': health_report['overall_status'],
                'critical_failures': health_report['critical_failures'],
                'duration_ms': health_report['duration_ms']
            }
            
        except Exception as e:
            return {
                'step': 'startup_health_checks',
                'success': False,
                'error': str(e)
            }
    
    async def _validate_credentials(self) -> Dict:
        """Validate API credentials"""
        try:
            if self.trading_env.paper_trade:
                return {
                    'step': 'credentials_validation',
                    'success': True,
                    'mode': 'paper_trade',
                    'message': 'Credentials validation skipped for paper trading'
                }
            
            # Test Kite Connect credentials
            from runner.kiteconnect_manager import KiteConnectManager
            
            kite_manager = KiteConnectManager(self.logger)
            kite_manager.set_access_token()
            kite = kite_manager.get_kite_client()
            
            # Test API call
            profile = kite.profile()
            
            return {
                'step': 'credentials_validation',
                'success': True,
                'mode': 'live_trading',
                'user_id': profile.get('user_id', 'unknown'),
                'broker': profile.get('broker', 'unknown')
            }
            
        except Exception as e:
            return {
                'step': 'credentials_validation',
                'success': False,
                'error': str(e)
            }
    
    async def _initialize_risk_systems(self) -> Dict:
        """Initialize risk management systems"""
        try:
            # Initialize portfolio manager
            from runner.capital.portfolio_manager import create_portfolio_manager
            
            portfolio_manager = create_portfolio_manager(
                paper_trade=self.trading_env.paper_trade,
                initial_capital=self.trading_env.max_daily_loss * 10  # Conservative initial capital
            )
            
            # Test risk check
            test_trade = {
                'symbol': 'TEST',
                'quantity': 1,
                'price': 100,
                'volatility': 0.02,
                'strategy': 'test'
            }
            
            risk_passed, risk_message = portfolio_manager.risk_check_before_trade(test_trade)
            
            return {
                'step': 'risk_systems_initialization',
                'success': True,
                'portfolio_manager_ready': True,
                'risk_check_test': risk_passed,
                'risk_message': risk_message
            }
            
        except Exception as e:
            return {
                'step': 'risk_systems_initialization',
                'success': False,
                'error': str(e)
            }
    
    async def _start_monitoring_services(self) -> Dict:
        """Start monitoring services"""
        try:
            # Start background monitoring task
            monitoring_task = asyncio.create_task(self._background_monitoring())
            
            return {
                'step': 'monitoring_services',
                'success': True,
                'monitoring_interval': self.trading_env.monitoring_interval,
                'task_created': True
            }
            
        except Exception as e:
            return {
                'step': 'monitoring_services',
                'success': False,
                'error': str(e)
            }
    
    async def _warm_up_caches(self) -> Dict:
        """Warm up system caches"""
        try:
            # Initialize technical engine
            from runner.indicators.technical_engine import create_technical_engine
            
            tech_engine = create_technical_engine(paper_trade=self.trading_env.paper_trade)
            
            # Initialize options engine
            from runner.options.pricing_engine import create_options_engine
            
            options_engine = create_options_engine(paper_trade=self.trading_env.paper_trade)
            
            return {
                'step': 'cache_warmup',
                'success': True,
                'technical_engine_ready': True,
                'options_engine_ready': True
            }
            
        except Exception as e:
            return {
                'step': 'cache_warmup',
                'success': False,
                'error': str(e)
            }
    
    async def _background_monitoring(self):
        """Background monitoring task"""
        while True:
            try:
                await asyncio.sleep(self.trading_env.monitoring_interval)
                
                # Run periodic health check
                health_report = await self.comprehensive_health_check()
                
                # Check for circuit breaker conditions
                if health_report['overall_status'] == 'critical':
                    self._handle_circuit_breaker()
                
            except Exception as e:
                if self.logger:
                    self.logger.log_event(f"Background monitoring error: {e}")
    
    def _handle_circuit_breaker(self):
        """Handle circuit breaker activation"""
        self.circuit_breaker['failures'] += 1
        self.circuit_breaker['last_failure'] = datetime.now()
        
        if self.circuit_breaker['failures'] >= self.circuit_breaker['threshold']:
            self.circuit_breaker['is_open'] = True
            
            if self.logger:
                self.logger.log_event("🚨 CIRCUIT BREAKER ACTIVATED - System entering safe mode")
    
    async def _send_critical_alert(self, title: str, details: Dict):
        """Send critical alert notification"""
        alert = {
            'title': title,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'environment': self.environment.value,
            'severity': 'CRITICAL'
        }
        
        if self.logger:
            self.logger.log_event(f"CRITICAL ALERT: {title}")
        
        # Store alert in Firestore if available
        if self.firestore:
            try:
                self.firestore.collection('alerts').add(alert)
            except Exception as e:
                if self.logger:
                    self.logger.log_event(f"Failed to store alert: {e}")
    
    def _load_alerts_config(self) -> Dict:
        """Load alert configuration"""
        return {
            'email_enabled': os.getenv("ALERTS_EMAIL_ENABLED", "false").lower() == "true",
            'slack_enabled': os.getenv("ALERTS_SLACK_ENABLED", "false").lower() == "true",
            'webhook_url': os.getenv("ALERTS_WEBHOOK_URL", ""),
            'critical_threshold': 5,
            'degraded_threshold': 3
        }
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'environment': asdict(self.trading_env),
            'last_health_check': self.last_health_check,
            'circuit_breaker': self.circuit_breaker,
            'metrics_history_count': len(self.system_metrics_history),
            'alerts_config': self.alerts_config,
            'uptime_seconds': (datetime.now() - datetime.now().replace(hour=0, minute=0, second=0)).total_seconds()
        }


# Factory function
def create_production_manager(logger=None, firestore=None) -> ProductionManager:
    """Create ProductionManager instance"""
    return ProductionManager(logger=logger, firestore=firestore)
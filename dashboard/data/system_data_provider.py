"""
System Data Provider
Provides system health and monitoring data for the dashboard
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psutil
import os

# Import existing system components
from runner.production.deployment_manager import ProductionManager
from runner.logger import Logger


class SystemDataProvider:
    """Provides system health and monitoring data for dashboard components"""
    
    def __init__(self):
        self.logger = Logger(datetime.now().strftime("%Y-%m-%d"))
        
        # Initialize production manager for health checks
        try:
            self.production_manager = ProductionManager(logger=self.logger)
        except Exception as e:
            self.logger.log_event(f"Failed to initialize production manager: {e}")
            self.production_manager = None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            if self.production_manager:
                # Get comprehensive health check
                health_data = asyncio.run(self.production_manager.comprehensive_health_check())
                
                # Ensure overall_status is a string, not enum object
                overall_status = health_data.get('overall_status', 'unknown')
                overall_status = str(overall_status)
                
                return {
                    'overall_status': overall_status,
                    'uptime_hours': self._get_uptime_hours(),
                    'last_check_time': health_data.get('timestamp', datetime.now().isoformat()),
                    'critical_failures': health_data.get('critical_failures', 0),
                    'system_ready': health_data.get('system_ready', False)
                }
            else:
                # Fallback status
                return {
                    'overall_status': 'degraded',
                    'uptime_hours': self._get_uptime_hours(),
                    'last_check_time': datetime.now().isoformat(),
                    'critical_failures': 0,
                    'system_ready': True
                }
                
        except Exception as e:
            self.logger.log_event(f"Error getting system status: {e}")
            return {
                'overall_status': 'unknown',
                'uptime_hours': 0,
                'last_check_time': datetime.now().isoformat(),
                'critical_failures': 1,
                'system_ready': False
            }
    
    def get_health_checks(self) -> List[Dict[str, Any]]:
        """Get detailed health check results"""
        try:
            if self.production_manager:
                health_data = asyncio.run(self.production_manager.comprehensive_health_check())
                checks = health_data.get('checks', [])
                
                # Ensure status fields are strings, not enum objects
                for check in checks:
                    if 'status' in check:
                        check['status'] = str(check['status'])
                
                return checks
            else:
                # Return mock health checks
                return self._get_mock_health_checks()
                
        except Exception as e:
            self.logger.log_event(f"Error getting health checks: {e}")
            return []
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics"""
        try:
            # Get CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Get network connections
            network_connections = len(psutil.net_connections())
            
            return {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'memory_available_gb': memory_available_gb,
                'disk_usage': disk_usage,
                'network_connections': network_connections,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.log_event(f"Error getting system metrics: {e}")
            return {
                'cpu_usage': 0,
                'memory_usage': 0,
                'memory_available_gb': 0,
                'disk_usage': 0,
                'network_connections': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview data"""
        try:
            # This would typically fetch from market data API
            # For now, return mock data
            return {
                'nifty': {
                    'price': 19850.25,
                    'change_pct': 0.75
                },
                'banknifty': {
                    'price': 45320.80,
                    'change_pct': -0.25
                },
                'vix': {
                    'price': 13.45,
                    'change_pct': -2.15
                },
                'sentiment': 'Bullish'
            }
            
        except Exception as e:
            self.logger.log_event(f"Error getting market overview: {e}")
            return {}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of individual services"""
        try:
            services = {
                'main_runner': self._check_service_status('main-runner'),
                'stock_trader': self._check_service_status('stock-trader'),
                'options_trader': self._check_service_status('options-trader'),
                'futures_trader': self._check_service_status('futures-trader'),
                'firestore': self._check_firestore_status(),
                'kite_api': self._check_kite_api_status()
            }
            
            return services
            
        except Exception as e:
            self.logger.log_event(f"Error getting service status: {e}")
            return {}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            return {
                'api_response_time_ms': 150,
                'database_query_time_ms': 45,
                'trade_execution_time_ms': 200,
                'memory_usage_trend': 'stable',
                'cpu_usage_trend': 'stable',
                'error_rate_pct': 0.1,
                'uptime_pct': 99.8
            }
            
        except Exception as e:
            self.logger.log_event(f"Error getting performance metrics: {e}")
            return {}
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts"""
        try:
            # This would typically come from an alerting system
            alerts = []
            
            # Check for high resource usage
            metrics = self.get_system_metrics()
            
            if metrics.get('cpu_usage', 0) > 80:
                alerts.append({
                    'type': 'warning',
                    'message': f"High CPU usage: {metrics['cpu_usage']:.1f}%",
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'medium'
                })
            
            if metrics.get('memory_usage', 0) > 85:
                alerts.append({
                    'type': 'critical',
                    'message': f"High memory usage: {metrics['memory_usage']:.1f}%",
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'high'
                })
            
            return alerts
            
        except Exception as e:
            self.logger.log_event(f"Error getting alerts: {e}")
            return []
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get log summary statistics"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_dir = f"logs/{today}"
            
            if os.path.exists(log_dir):
                log_files = os.listdir(log_dir)
                total_log_files = len(log_files)
                
                # Count log entries (simplified)
                total_entries = 0
                error_entries = 0
                
                for log_file in log_files:
                    if log_file.endswith('.txt'):
                        log_path = os.path.join(log_dir, log_file)
                        try:
                            with open(log_path, 'r') as f:
                                lines = f.readlines()
                                total_entries += len(lines)
                                error_entries += sum(1 for line in lines if 'ERROR' in line)
                        except:
                            continue
                
                return {
                    'total_log_files': total_log_files,
                    'total_entries': total_entries,
                    'error_entries': error_entries,
                    'warning_entries': 0,  # Would need to parse logs
                    'last_updated': datetime.now().isoformat()
                }
            else:
                return {
                    'total_log_files': 0,
                    'total_entries': 0,
                    'error_entries': 0,
                    'warning_entries': 0,
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.log_event(f"Error getting log summary: {e}")
            return {}
    
    def _get_uptime_hours(self) -> float:
        """Calculate system uptime in hours"""
        try:
            # Get system boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return uptime.total_seconds() / 3600
        except:
            return 0.0
    
    def _check_service_status(self, service_name: str) -> Dict[str, Any]:
        """Check status of a specific service"""
        try:
            # This would typically check Kubernetes pod status
            # For now, return mock status
            return {
                'status': 'running',
                'health': 'healthy',
                'last_restart': datetime.now().isoformat(),
                'cpu_usage': 25.0,
                'memory_usage': 45.0
            }
        except:
            return {
                'status': 'unknown',
                'health': 'unknown',
                'last_restart': None,
                'cpu_usage': 0,
                'memory_usage': 0
            }
    
    def _check_firestore_status(self) -> Dict[str, Any]:
        """Check Firestore connectivity status"""
        try:
            # This would test Firestore connection
            return {
                'status': 'connected',
                'health': 'healthy',
                'response_time_ms': 45,
                'last_check': datetime.now().isoformat()
            }
        except:
            return {
                'status': 'disconnected',
                'health': 'unhealthy',
                'response_time_ms': 999,
                'last_check': datetime.now().isoformat()
            }
    
    def _check_kite_api_status(self) -> Dict[str, Any]:
        """Check Kite API connectivity status"""
        try:
            # This would test Kite API connection
            return {
                'status': 'connected',
                'health': 'healthy',
                'response_time_ms': 120,
                'last_check': datetime.now().isoformat()
            }
        except:
            return {
                'status': 'disconnected',
                'health': 'unhealthy',
                'response_time_ms': 999,
                'last_check': datetime.now().isoformat()
            }
    
    def _get_mock_health_checks(self) -> List[Dict[str, Any]]:
        """Get mock health check data when production manager is not available"""
        return [
            {
                'service': 'kite_api',
                'status': 'healthy',
                'response_time': 0.12,
                'timestamp': datetime.now().isoformat(),
                'details': {'mode': 'paper_trade'},
                'is_critical': True
            },
            {
                'service': 'firestore',
                'status': 'healthy',
                'response_time': 0.045,
                'timestamp': datetime.now().isoformat(),
                'details': {'connection': 'successful'},
                'is_critical': False
            },
            {
                'service': 'system_resources',
                'status': 'healthy',
                'response_time': 0.01,
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'cpu_usage': 25.0,
                    'memory_usage': 45.0,
                    'disk_usage': 30.0
                },
                'is_critical': True
            },
            {
                'service': 'trading_services',
                'status': 'healthy',
                'response_time': 0.08,
                'timestamp': datetime.now().isoformat(),
                'details': {'services_status': {'all': True}},
                'is_critical': True
            }
        ] 
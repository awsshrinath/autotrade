"""
This file will contain the business logic for the system health endpoints.
We will migrate the logic from the old SystemDataProvider here.
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import psutil

# We need to import the ProductionManager and Logger from the existing `runner` module.
# This requires adjusting the Python path, which is best handled by the application's entry point
# or a shared configuration. For now, we assume it's available.
from runner.production.deployment_manager import ProductionManager
from runner.logger import Logger

class SystemService:
    """
    Service layer for handling system health and monitoring logic.
    """
    def __init__(self, logger: Logger, production_manager: ProductionManager):
        self.logger = logger
        self.production_manager = production_manager

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        try:
            status_data = await self.get_system_status()
            
            # This logic is simplified; we can add back the detailed counts later.
            return {
                'status': status_data.get('overall_status', 'unknown'),
                'uptime_hours': self._get_uptime_hours(),
                'last_check': datetime.now().isoformat(),
                **status_data
            }
        except Exception as e:
            self.logger.log_event(f"Error getting system health: {e}")
            return {'status': 'error', 'message': str(e)}

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status from ProductionManager."""
        try:
            if self.production_manager:
                health_data = await self.production_manager.comprehensive_health_check()
                # Ensure enum is converted to string for JSON serialization
                health_data['overall_status'] = str(health_data.get('overall_status', 'unknown'))
                return health_data
            return {'overall_status': 'degraded', 'message': 'ProductionManager not available.'}
        except Exception as e:
            self.logger.log_event(f"Error getting system status: {e}")
            return {'overall_status': 'unknown', 'message': str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return {
                'cpu_usage': psutil.cpu_percent(interval=None),
                'memory_usage': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_usage': disk.percent,
                'network_connections': len(psutil.net_connections()),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.log_event(f"Error getting system metrics: {e}")
            return {'error': str(e)}

    def _get_uptime_hours(self) -> float:
        """Calculate system uptime."""
        # This should ideally be the process uptime of the main runner
        # For now, we use psutil's boot time as an approximation.
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return round(uptime.total_seconds() / 3600, 2)
        except:
            return 0

# Dependency Injection setup
# This makes the service testable and manages its lifecycle.
_logger_instance = None
_production_manager_instance = None
_system_service_instance = None

def get_logger():
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger(datetime.now().strftime("%Y-%m-%d"))
    return _logger_instance

def get_production_manager(logger: Logger = get_logger()):
    global _production_manager_instance
    if _production_manager_instance is None:
        try:
            _production_manager_instance = ProductionManager(logger=logger)
        except Exception as e:
            logger.log_event(f"FATAL: Could not initialize ProductionManager for API: {e}")
            # In a real app, you might have a fallback or raise an exception
            _production_manager_instance = None 
    return _production_manager_instance

def get_system_service():
    global _system_service_instance
    if _system_service_instance is None:
        _system_service_instance = SystemService(
            logger=get_logger(),
            production_manager=get_production_manager()
        )
    return _system_service_instance 
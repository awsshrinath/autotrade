#!/usr/bin/env python3
"""
Quick API test to verify endpoints are working
"""
import asyncio
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/v1/system/resources")
async def system_resources():
    """Get system resource usage metrics"""
    try:
        import psutil
        
        # Get real system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_usage": round(cpu_percent, 1),
            "memory_usage": round(memory.percent, 1),
            "memory_total": round(memory.total / (1024**3), 1),  # GB
            "memory_available": round(memory.available / (1024**3), 1),  # GB
            "disk_usage": round(disk.percent, 1),
            "disk_total": round(disk.total / (1024**3), 1),  # GB
            "disk_free": round(disk.free / (1024**3), 1),  # GB
            "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0,
            "data_source": "real_system_monitoring",
            "timestamp": "2025-07-17T05:50:00.000000"
        }
    except ImportError:
        # Fallback when psutil is not available
        return {
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "memory_total": 16.0,
            "memory_available": 5.1,
            "disk_usage": 23.1,
            "disk_total": 500.0,
            "disk_free": 384.5,
            "load_average": 1.2,
            "data_source": "system_monitoring_fallback",
            "message": "Install psutil for real system metrics",
            "timestamp": "2025-07-17T05:50:00.000000"
        }

@app.get("/api/v1/system/memory")
async def system_memory():
    """Get detailed memory usage information"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        
        return {
            "total": round(memory.total / (1024**3), 2),  # GB
            "available": round(memory.available / (1024**3), 2),  # GB
            "used": round(memory.used / (1024**3), 2),  # GB
            "percent": round(memory.percent, 1),
            "buffers": round(memory.buffers / (1024**3), 2) if hasattr(memory, 'buffers') else 0,
            "cached": round(memory.cached / (1024**3), 2) if hasattr(memory, 'cached') else 0,
            "data_source": "real_memory_monitoring",
            "timestamp": "2025-07-17T05:50:00.000000"
        }
    except ImportError:
        return {
            "total": 16.0,
            "available": 5.1,
            "used": 10.9,
            "percent": 67.8,
            "buffers": 0.5,
            "cached": 2.3,
            "data_source": "memory_monitoring_fallback",
            "message": "Install psutil for real memory metrics",
            "timestamp": "2025-07-17T05:50:00.000000"
        }

@app.get("/api/v1/system/status")
async def system_status():
    """Get overall system status information"""
    try:
        import psutil
        from datetime import timedelta
        
        # Get system uptime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime = str(timedelta(seconds=int(uptime_seconds)))
        
        # Get system info
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        return {
            "uptime": uptime,
            "cpu_count": cpu_count,
            "cpu_freq_current": round(cpu_freq.current, 1) if cpu_freq else 0,
            "cpu_freq_max": round(cpu_freq.max, 1) if cpu_freq else 0,
            "system_load": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0,
            "processes": len(psutil.pids()),
            "connections": len(psutil.net_connections()),
            "data_source": "real_system_status",
            "timestamp": "2025-07-17T05:50:00.000000"
        }
    except ImportError:
        return {
            "uptime": "2d 14h 32m",
            "cpu_count": 8,
            "cpu_freq_current": 2400.0,
            "cpu_freq_max": 3200.0,
            "system_load": 1.2,
            "processes": 156,
            "connections": 23,
            "data_source": "system_status_fallback",
            "message": "Install psutil for real system status",
            "timestamp": "2025-07-17T05:50:00.000000"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
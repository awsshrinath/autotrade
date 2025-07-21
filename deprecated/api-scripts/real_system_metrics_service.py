#!/usr/bin/env python3
"""
Real System Metrics Service - Provides actual system resource data
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import time
import logging
import subprocess
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Real System Metrics API",
    description="Provides actual system resource and status data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_cpu_usage():
    """Get real CPU usage percentage"""
    try:
        # Try using /proc/stat first
        with open('/proc/stat', 'r') as f:
            line = f.readline()
            cpu_times = [int(x) for x in line.split()[1:]]
            idle_time = cpu_times[3]
            total_time = sum(cpu_times)
            cpu_usage = 100 * (1 - idle_time / total_time)
            return round(cpu_usage, 1)
    except:
        try:
            # Fallback to top command
            result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if 'Cpu(s)' in line:
                    # Extract CPU usage from top output
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'us' in part:
                            return round(float(parts[i-1]), 1)
        except:
            pass
    return 0.0

def get_memory_info():
    """Get real memory usage information"""
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = {}
            for line in f:
                key, value = line.split(':')
                meminfo[key.strip()] = int(value.strip().split()[0]) * 1024  # Convert KB to bytes
            
            total = meminfo.get('MemTotal', 0)
            available = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))
            used = total - available
            percent = round((used / total) * 100, 1) if total > 0 else 0
            
            return {
                'total_bytes': total,
                'available_bytes': available,
                'used_bytes': used,
                'percent': percent,
                'buffers_bytes': meminfo.get('Buffers', 0),
                'cached_bytes': meminfo.get('Cached', 0)
            }
    except:
        return {
            'total_bytes': 0,
            'available_bytes': 0,
            'used_bytes': 0,
            'percent': 0,
            'buffers_bytes': 0,
            'cached_bytes': 0
        }

def get_disk_usage():
    """Get real disk usage information"""
    try:
        result = subprocess.run(['df', '/'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            total = int(parts[1]) * 1024  # Convert KB to bytes
            used = int(parts[2]) * 1024
            available = int(parts[3]) * 1024
            percent = round((used / total) * 100, 1) if total > 0 else 0
            
            return {
                'total_bytes': total,
                'used_bytes': used,
                'available_bytes': available,
                'percent': percent
            }
    except:
        pass
    return {
        'total_bytes': 0,
        'used_bytes': 0,
        'available_bytes': 0,
        'percent': 0
    }

def get_system_load():
    """Get real system load average"""
    try:
        with open('/proc/loadavg', 'r') as f:
            return float(f.read().split()[0])
    except:
        return 0.0

def get_system_uptime():
    """Get real system uptime"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
            return str(timedelta(seconds=int(uptime_seconds)))
    except:
        return "Unknown"

def get_cpu_info():
    """Get real CPU information"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpu_count = 0
            cpu_freq = 0
            for line in f:
                if line.startswith('processor'):
                    cpu_count += 1
                elif line.startswith('cpu MHz'):
                    cpu_freq = float(line.split(':')[1].strip())
            
            return {
                'cpu_count': cpu_count,
                'cpu_freq_current': cpu_freq,
                'cpu_freq_max': cpu_freq  # Approximate, real max would need other sources
            }
    except:
        return {
            'cpu_count': 1,
            'cpu_freq_current': 0,
            'cpu_freq_max': 0
        }

def get_process_count():
    """Get real process count"""
    try:
        return len(os.listdir('/proc')) - len([name for name in os.listdir('/proc') if not name.isdigit()])
    except:
        return 0

def get_network_connections():
    """Get real network connection count"""
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
        return len([line for line in result.stdout.split('\n') if 'ESTABLISHED' in line])
    except:
        try:
            result = subprocess.run(['ss', '-an'], capture_output=True, text=True, timeout=5)
            return len([line for line in result.stdout.split('\n') if 'ESTAB' in line])
        except:
            return 0

@app.get("/api/v1/system/resources")
async def system_resources():
    """Get real system resource usage metrics"""
    try:
        cpu_usage = get_cpu_usage()
        memory_info = get_memory_info()
        disk_info = get_disk_usage()
        load_avg = get_system_load()
        
        return {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_info['percent'],
            "memory_total": round(memory_info['total_bytes'] / (1024**3), 1),  # GB
            "memory_available": round(memory_info['available_bytes'] / (1024**3), 1),  # GB
            "disk_usage": disk_info['percent'],
            "disk_total": round(disk_info['total_bytes'] / (1024**3), 1),  # GB
            "disk_free": round(disk_info['available_bytes'] / (1024**3), 1),  # GB
            "load_average": load_avg,
            "data_source": "real_system_monitoring",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ System resources error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/system/memory")
async def system_memory():
    """Get real detailed memory usage information"""
    try:
        memory_info = get_memory_info()
        
        return {
            "total": round(memory_info['total_bytes'] / (1024**3), 2),  # GB
            "available": round(memory_info['available_bytes'] / (1024**3), 2),  # GB
            "used": round(memory_info['used_bytes'] / (1024**3), 2),  # GB
            "percent": memory_info['percent'],
            "buffers": round(memory_info['buffers_bytes'] / (1024**3), 2),  # GB
            "cached": round(memory_info['cached_bytes'] / (1024**3), 2),  # GB
            "data_source": "real_memory_monitoring",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ System memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/system/status")
async def system_status():
    """Get real overall system status information"""
    try:
        uptime = get_system_uptime()
        cpu_info = get_cpu_info()
        load_avg = get_system_load()
        process_count = get_process_count()
        connections = get_network_connections()
        
        return {
            "uptime": uptime,
            "cpu_count": cpu_info['cpu_count'],
            "cpu_freq_current": round(cpu_info['cpu_freq_current'], 1),
            "cpu_freq_max": round(cpu_info['cpu_freq_max'], 1),
            "system_load": load_avg,
            "processes": process_count,
            "connections": connections,
            "data_source": "real_system_status",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ System status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "real-system-metrics-api",
        "timestamp": datetime.now().isoformat()
    }

def main():
    """Start the real system metrics API server"""
    print("🚀 Starting Real System Metrics API Server...")
    print("📊 Providing actual system resource data")
    print("🔍 Reading from /proc filesystem and system commands")
    print("🌐 API will be available at: http://localhost:8002")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
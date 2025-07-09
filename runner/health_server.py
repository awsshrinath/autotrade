#!/usr/bin/env python3
"""
Health Server Wrapper for Trading Services

This module provides a simple HTTP health endpoint for trading services
that need to be monitored by Kubernetes health checks while running
long-running trading logic in the background.
"""

import os
import sys
import threading
import time
import json
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
import logging

class HealthStatus:
    """Tracks the health status of the service"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.last_heartbeat = datetime.now()
        self.status = "starting"
        self.message = "Service is starting up"
        self.errors = []
        self.script_process: Optional[subprocess.Popen] = None
        self.script_exit_code: Optional[int] = None
        
    def update_heartbeat(self):
        """Update the last heartbeat timestamp"""
        self.last_heartbeat = datetime.now()
        
    def set_running(self):
        """Mark service as running"""
        self.status = "healthy"
        self.message = "Service is running normally"
        self.update_heartbeat()
        
    def set_error(self, error_msg: str):
        """Mark service as having an error"""
        self.status = "error"
        self.message = error_msg
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "message": error_msg
        })
        # Keep only last 10 errors
        self.errors = self.errors[-10:]
        
    def set_completed(self, exit_code: int):
        """Mark script as completed"""
        self.script_exit_code = exit_code
        if exit_code == 0:
            self.status = "completed"
            self.message = "Script completed successfully"
        else:
            self.status = "error"
            self.message = f"Script exited with code {exit_code}"
            
    def get_status(self) -> Dict[str, Any]:
        """Get current status as dict"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        heartbeat_age = (datetime.now() - self.last_heartbeat).total_seconds()
        
        return {
            "status": self.status,
            "message": self.message,
            "uptime_seconds": uptime,
            "heartbeat_age_seconds": heartbeat_age,
            "start_time": self.start_time.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "script_exit_code": self.script_exit_code,
            "error_count": len(self.errors),
            "recent_errors": self.errors[-3:] if self.errors else []
        }

# Global health status
health_status = HealthStatus()

class HealthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self.send_health_response()
        elif self.path == "/status":
            self.send_detailed_status()
        else:
            self.send_error(404, "Not Found")
            
    def send_health_response(self):
        """Send basic health response for Kubernetes probes"""
        status_data = health_status.get_status()
        
        # Simple health check - return 200 if status is healthy, starting, or completed
        if status_data["status"] in ["healthy", "starting", "completed"]:
            response_code = 200
            response = {
                "status": "ok",
                "message": status_data["message"],
                "uptime": status_data["uptime_seconds"]
            }
        else:
            response_code = 503  # Service Unavailable
            response = {
                "status": "error", 
                "message": status_data["message"],
                "uptime": status_data["uptime_seconds"]
            }
            
        self.send_json_response(response_code, response)
        
    def send_detailed_status(self):
        """Send detailed status information"""
        status_data = health_status.get_status()
        self.send_json_response(200, status_data)
        
    def send_json_response(self, code: int, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
        
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass

def run_script_with_monitoring(script_path: str):
    """Run the trading script with monitoring"""
    logger = logging.getLogger(__name__)
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Starting script: {script_path} (attempt {retry_count + 1})")
            health_status.set_running()
            
            # Start the script as a subprocess with timeout
            process = subprocess.Popen(
                [sys.executable, "-u", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            health_status.script_process = process
            
            # Monitor the process with timeout
            start_time = time.time()
            last_output_time = time.time()
            
            while True:
                # Check if process is still running
                if process.poll() is not None:
                    break
                    
                # Read output with timeout
                try:
                    output = process.stdout.readline()
                    if output:
                        print(output.strip())  # Forward output to container logs
                        health_status.update_heartbeat()
                        last_output_time = time.time()
                except:
                    pass
                
                # Check for stuck process (no output for 10 minutes)
                if time.time() - last_output_time > 600:
                    logger.warning("Script appears stuck, will restart")
                    process.terminate()
                    time.sleep(5)
                    if process.poll() is None:
                        process.kill()
                    break
                    
                time.sleep(1)
                
            # Process has finished
            exit_code = process.poll()
            health_status.set_completed(exit_code)
            logger.info(f"Script completed with exit code: {exit_code}")
            
            # If script completed successfully, keep running
            if exit_code == 0:
                # Keep health server running
                while True:
                    time.sleep(60)
                    health_status.update_heartbeat()
            else:
                # Script failed, retry
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Script failed, retrying in 30 seconds...")
                    time.sleep(30)
                else:
                    health_status.set_error(f"Script failed after {max_retries} attempts")
                    break
                
        except Exception as e:
            error_msg = f"Error running script: {str(e)}"
            logger.exception(f"Exception in monitored script: {script_path}")
            retry_count += 1
            if retry_count < max_retries:
                logger.info(f"Exception occurred, retrying in 30 seconds...")
                time.sleep(30)
            else:
                health_status.set_error(error_msg)
                break
    
    # Keep health server running even if all retries failed
    logger.info("Keeping health server running...")
    while True:
        time.sleep(60)
        health_status.update_heartbeat()

def start_health_server(port: int = 8080):
    """Start the health check HTTP server"""
    logger = logging.getLogger(__name__)
    
    try:
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        logger.info(f"Health server starting on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health server error: {e}")
        health_status.set_error(f"Health server failed: {e}")

def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Get script path from environment variable
    script_path = os.environ.get('RUNNER_SCRIPT')
    if not script_path:
        logger.error("RUNNER_SCRIPT environment variable not set")
        sys.exit(1)
        
    # Get port from environment variable
    port = int(os.environ.get('SERVICE_PORT', '8080'))
    
    logger.info(f"Health server wrapper starting - script: {script_path}, port: {port}")
    
    # Start the health server in a separate thread
    health_thread = threading.Thread(
        target=start_health_server,
        args=(port,),
        daemon=True
    )
    health_thread.start()
    
    # Run the actual trading script
    run_script_with_monitoring(script_path)

if __name__ == "__main__":
    main()
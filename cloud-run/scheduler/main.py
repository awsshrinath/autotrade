#!/usr/bin/env python3
"""
TRON Trading System - Daily Cluster Scheduler
Cloud Run service triggered by Cloud Scheduler for daily cluster operations
"""

import os
import logging
import requests
from datetime import datetime, timezone
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
CLUSTER_MANAGER_URL = os.environ.get('CLUSTER_MANAGER_URL', 'https://cluster-manager-service-url')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')  # Optional webhook for notifications
TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Kolkata')

def send_notification(message, status="info"):
    """Send notification to webhook if configured"""
    if WEBHOOK_URL:
        try:
            payload = {
                "text": f"🤖 TRON Trading System: {message}",
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            requests.post(WEBHOOK_URL, json=payload, timeout=10)
        except Exception as e:
            logger.warning(f"Failed to send notification: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route('/morning-setup', methods=['POST'])
def morning_setup():
    """Morning cluster creation and deployment (triggered by Cloud Scheduler)"""
    logger.info("Starting morning cluster setup")
    
    try:
        # Verify this is coming from Cloud Scheduler
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Unauthorized"}), 401
        
        send_notification("🌅 Starting daily cluster setup", "info")
        
        # Create cluster and deploy trading system
        response = requests.post(
            f"{CLUSTER_MANAGER_URL}/create-cluster",
            json={},
            timeout=1200  # 20 minutes timeout for cluster creation
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Morning setup completed successfully")
            send_notification("✅ Daily cluster setup completed successfully", "success")
            
            return jsonify({
                "status": "success",
                "message": "Morning cluster setup completed",
                "details": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            error_msg = f"Cluster setup failed: {response.text}"
            logger.error(error_msg)
            send_notification(f"❌ Daily cluster setup failed: {response.text}", "error")
            
            return jsonify({
                "status": "error",
                "message": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500
            
    except Exception as e:
        error_msg = f"Morning setup failed: {str(e)}"
        logger.error(error_msg)
        send_notification(f"❌ Daily cluster setup failed: {str(e)}", "error")
        
        return jsonify({
            "status": "error",
            "message": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/evening-cleanup', methods=['POST'])
def evening_cleanup():
    """Evening cluster backup and deletion (triggered by Cloud Scheduler)"""
    logger.info("Starting evening cluster cleanup")
    
    try:
        # Verify this is coming from Cloud Scheduler
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Unauthorized"}), 401
        
        send_notification("🌆 Starting daily cluster cleanup", "info")
        
        # Backup and delete cluster
        response = requests.post(
            f"{CLUSTER_MANAGER_URL}/delete-cluster",
            json={"backup_data": True},
            timeout=600  # 10 minutes timeout for cleanup
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Evening cleanup completed successfully")
            send_notification("✅ Daily cluster cleanup completed successfully", "success")
            
            return jsonify({
                "status": "success",
                "message": "Evening cluster cleanup completed",
                "details": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            error_msg = f"Cluster cleanup failed: {response.text}"
            logger.error(error_msg)
            send_notification(f"❌ Daily cluster cleanup failed: {response.text}", "error")
            
            return jsonify({
                "status": "error",
                "message": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500
            
    except Exception as e:
        error_msg = f"Evening cleanup failed: {str(e)}"
        logger.error(error_msg)
        send_notification(f"❌ Daily cluster cleanup failed: {str(e)}", "error")
        
        return jsonify({
            "status": "error",
            "message": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/health-check', methods=['POST'])
def system_health_check():
    """Periodic health check of the trading system (triggered by Cloud Scheduler)"""
    logger.info("Performing system health check")
    
    try:
        # Verify this is coming from Cloud Scheduler
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Unauthorized"}), 401
        
        # Check cluster status
        response = requests.get(
            f"{CLUSTER_MANAGER_URL}/status",
            timeout=30
        )
        
        if response.status_code == 200:
            status = response.json()
            
            if status.get("status") == "running":
                logger.info("System health check passed")
                return jsonify({
                    "status": "healthy",
                    "cluster_status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            else:
                logger.warning(f"System health check warning: {status}")
                send_notification(f"⚠️ System health check warning: Cluster status is {status.get('status')}", "warning")
                
                return jsonify({
                    "status": "warning",
                    "cluster_status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        else:
            logger.error(f"Health check failed: {response.text}")
            send_notification(f"❌ System health check failed: {response.text}", "error")
            
            return jsonify({
                "status": "error",
                "message": response.text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500
            
    except Exception as e:
        error_msg = f"Health check failed: {str(e)}"
        logger.error(error_msg)
        send_notification(f"❌ System health check failed: {str(e)}", "error")
        
        return jsonify({
            "status": "error",
            "message": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/emergency-deploy', methods=['POST'])
def emergency_deploy():
    """Emergency deployment endpoint for manual intervention"""
    logger.info("Emergency deployment requested")
    
    try:
        # This endpoint requires proper authentication
        data = request.get_json() or {}
        auth_key = data.get('auth_key', '')
        
        # Add your authentication logic here
        if not auth_key:
            return jsonify({"error": "Authentication required"}), 401
        
        send_notification("🚨 Emergency deployment initiated", "warning")
        
        # Deploy to existing cluster
        response = requests.post(
            f"{CLUSTER_MANAGER_URL}/deploy",
            json={},
            timeout=900  # 15 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            send_notification("✅ Emergency deployment completed", "success")
            
            return jsonify({
                "status": "success",
                "message": "Emergency deployment completed",
                "details": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            send_notification(f"❌ Emergency deployment failed: {response.text}", "error")
            
            return jsonify({
                "status": "error",
                "message": response.text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500
            
    except Exception as e:
        error_msg = f"Emergency deployment failed: {str(e)}"
        logger.error(error_msg)
        send_notification(f"❌ Emergency deployment failed: {str(e)}", "error")
        
        return jsonify({
            "status": "error",
            "message": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
#!/usr/bin/env python3
"""
TRON Migration Test Script
Validates the migration from Kubernetes to Docker deployment
"""

import os
import sys
import yaml
import json
import subprocess
from pathlib import Path

def test_config_files():
    """Test configuration files exist and are valid"""
    print("🔍 Testing configuration files...")
    
    # Test docker-compose.yml
    if not os.path.exists('docker-compose.yml'):
        print("❌ docker-compose.yml not found")
        return False
    
    # Test .env.docker
    if not os.path.exists('.env.docker'):
        print("❌ .env.docker not found") 
        return False
    
    # Test nginx.conf
    if not os.path.exists('nginx.conf'):
        print("❌ nginx.conf not found")
        return False
    
    # Test docker config
    if not os.path.exists('config/docker.yaml'):
        print("❌ config/docker.yaml not found")
        return False
    
    try:
        with open('config/docker.yaml', 'r') as f:
            yaml.safe_load(f)
        print("✅ YAML configuration valid")
    except Exception as e:
        print(f"❌ YAML configuration invalid: {e}")
        return False
    
    print("✅ Configuration files test passed")
    return True

def test_docker_compose():
    """Test docker-compose configuration"""
    print("🔍 Testing docker-compose configuration...")
    
    try:
        result = subprocess.run(['docker-compose', 'config', '--quiet'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("✅ docker-compose configuration valid")
            return True
        else:
            print(f"❌ docker-compose configuration invalid: {result.stderr}")
            return False
    except FileNotFoundError:
        print("⚠️ docker-compose not found, skipping validation")
        return True

def test_required_files():
    """Test that required files exist"""
    print("🔍 Testing required files...")
    
    required_files = [
        'Dockerfile',
        'entrypoint.sh',
        'docker-healthcheck.sh',
        'requirements.txt',
        'runner/config.py',
        'runner/health_server.py',
        'config/config_manager.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ Required files test passed")
    return True

def test_service_configuration():
    """Test service configuration in docker-compose"""
    print("🔍 Testing service configuration...")
    
    try:
        result = subprocess.run(['docker-compose', 'config'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode != 0:
            print(f"❌ Failed to parse docker-compose: {result.stderr}")
            return False
        
        config = yaml.safe_load(result.stdout)
        services = config.get('services', {})
        
        expected_services = [
            'main-runner', 'stock-trader', 'options-trader', 
            'futures-trader', 'dashboard-api', 'frontend', 
            'nginx', 'log-aggregator'
        ]
        
        missing_services = []
        for service in expected_services:
            if service not in services:
                missing_services.append(service)
        
        if missing_services:
            print(f"❌ Missing services: {missing_services}")
            return False
        
        print(f"✅ All {len(services)} services configured correctly")
        return True
        
    except Exception as e:
        print(f"❌ Service configuration test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable configuration"""
    print("🔍 Testing environment variables...")
    
    if not os.path.exists('.env.docker'):
        print("❌ .env.docker file not found")
        return False
    
    required_vars = [
        'ENVIRONMENT', 'PAPER_TRADE', 'GCP_PROJECT_ID',
        'DEFAULT_CAPITAL', 'HEALTH_CHECK_ENABLED'
    ]
    
    with open('.env.docker', 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ Environment variables test passed")
    return True

def test_scripts_executable():
    """Test that scripts are executable"""
    print("🔍 Testing script permissions...")
    
    scripts = ['entrypoint.sh', 'docker-healthcheck.sh', 'deploy-docker.sh']
    
    for script in scripts:
        if os.path.exists(script):
            if not os.access(script, os.X_OK):
                print(f"❌ Script {script} is not executable")
                return False
        else:
            print(f"⚠️ Script {script} not found")
    
    print("✅ Script permissions test passed")
    return True

def test_directory_structure():
    """Test directory structure for deployment"""
    print("🔍 Testing directory structure...")
    
    required_dirs = [
        'runner', 'config', 'dashboard_api', 'frontend',
        'gpt_runner', 'stock_trading', 'options_trading', 'futures_trading'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    
    # Test that logs and data directories can be created
    try:
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        print("✅ Directory structure test passed")
        return True
    except Exception as e:
        print(f"❌ Failed to create directories: {e}")
        return False

def test_migration_completeness():
    """Test that migration is complete"""
    print("🔍 Testing migration completeness...")
    
    # Check that old files are removed or marked for removal
    old_k8s_files = [
        'k8s/deployments/main-runner.yaml',
        'k8s/services.yaml'
    ]
    
    # These should still exist but will be removed later
    for file_path in old_k8s_files:
        if os.path.exists(file_path):
            print(f"ℹ️ Kubernetes file still exists (will be cleaned up): {file_path}")
    
    # Check that new Docker files exist
    new_docker_files = [
        'docker-compose.yml',
        '.env.docker',
        'nginx.conf',
        'docker-healthcheck.sh',
        'deploy-docker.sh'
    ]
    
    missing_docker_files = []
    for file_path in new_docker_files:
        if not os.path.exists(file_path):
            missing_docker_files.append(file_path)
    
    if missing_docker_files:
        print(f"❌ Missing Docker files: {missing_docker_files}")
        return False
    
    print("✅ Migration completeness test passed")
    return True

def run_all_tests():
    """Run all migration tests"""
    print("🚀 Running TRON migration tests...\n")
    
    tests = [
        test_config_files,
        test_docker_compose,
        test_required_files,
        test_service_configuration,
        test_environment_variables,
        test_scripts_executable,
        test_directory_structure,
        test_migration_completeness
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test failed with exception: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All migration tests passed! Ready for deployment.")
        return True
    else:
        print("⚠️ Some tests failed. Please fix issues before deployment.")
        return False

if __name__ == '__main__':
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
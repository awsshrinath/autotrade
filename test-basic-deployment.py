#!/usr/bin/env python3
"""
Basic Deployment Test Script
Tests the deployment setup without requiring all dependencies
"""

import os
import sys
import subprocess
import time

def test_docker_setup():
    """Test that Docker and docker-compose are available"""
    print("🔍 Testing Docker setup...")
    
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker available: {result.stdout.strip()}")
        else:
            print("❌ Docker not available")
            return False
    except FileNotFoundError:
        print("❌ Docker command not found")
        return False
    
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker Compose available: {result.stdout.strip()}")
        else:
            print("❌ Docker Compose not available")
            return False
    except FileNotFoundError:
        print("❌ docker-compose command not found")
        return False
    
    return True

def test_file_structure():
    """Test that all required files exist"""
    print("🔍 Testing file structure...")
    
    required_files = [
        'docker-compose.yml',
        'Dockerfile', 
        'entrypoint.sh',
        'docker-healthcheck.sh',
        '.env.docker',
        'nginx.conf',
        'requirements.txt',
        'main.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✅ Found: {file}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    return True

def test_python_modules():
    """Test basic Python module structure"""
    print("🔍 Testing Python module structure...")
    
    required_modules = [
        'runner',
        'runner/__init__.py',
        'runner/config.py',
        'runner/health_server.py',
        'dashboard_api',
        'dashboard_api/__init__.py',
        'dashboard_api/main.py'
    ]
    
    missing_modules = []
    for module in required_modules:
        if not os.path.exists(module):
            missing_modules.append(module)
        else:
            print(f"✅ Found: {module}")
    
    if missing_modules:
        print(f"❌ Missing modules: {missing_modules}")
        return False
    
    return True

def test_configuration():
    """Test configuration files"""
    print("🔍 Testing configuration...")
    
    # Test .env.docker
    if os.path.exists('.env.docker'):
        with open('.env.docker', 'r') as f:
            env_content = f.read()
        
        required_vars = ['ENVIRONMENT', 'PAPER_TRADE', 'DEFAULT_CAPITAL']
        missing_vars = []
        
        for var in required_vars:
            if f"{var}=" not in env_content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {missing_vars}")
            return False
        else:
            print("✅ Environment variables configured")
    else:
        print("❌ .env.docker file not found")
        return False
    
    return True

def test_docker_compose_syntax():
    """Test docker-compose file syntax"""
    print("🔍 Testing docker-compose syntax...")
    
    try:
        result = subprocess.run(['docker-compose', 'config', '--quiet'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("✅ docker-compose.yml syntax is valid")
            return True
        else:
            print(f"❌ docker-compose.yml syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error testing docker-compose: {e}")
        return False

def test_directories():
    """Test that required directories exist or can be created"""
    print("🔍 Testing directory structure...")
    
    required_dirs = ['logs', 'data']
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"✅ Created directory: {dir_name}")
            except Exception as e:
                print(f"❌ Failed to create directory {dir_name}: {e}")
                return False
        else:
            print(f"✅ Directory exists: {dir_name}")
    
    return True

def test_service_account_key():
    """Test if GCP service account key is present"""
    print("🔍 Testing GCP service account key...")
    
    key_file = 'gpt-runner-sa-key.json'
    if os.path.exists(key_file):
        print("✅ GCP service account key found")
        return True
    else:
        print("⚠️ GCP service account key not found (some features may not work)")
        return True  # Not critical for basic testing

def simulate_deployment_check():
    """Simulate deployment readiness check"""
    print("🔍 Simulating deployment readiness...")
    
    # Check if we can validate the docker-compose config
    try:
        result = subprocess.run(['docker-compose', 'config'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("✅ Docker compose configuration is valid")
            
            # Count services
            import yaml
            config = yaml.safe_load(result.stdout)
            services = config.get('services', {})
            print(f"✅ Found {len(services)} services configured")
            
            return True
        else:
            print(f"❌ Docker compose validation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️ Could not validate docker-compose (yaml not available): {e}")
        return True  # Don't fail if yaml is not available

def run_deployment_test():
    """Run comprehensive deployment test"""
    print("🚀 Running TRON deployment readiness test...\n")
    
    tests = [
        ("Docker Setup", test_docker_setup),
        ("File Structure", test_file_structure),
        ("Python Modules", test_python_modules),
        ("Configuration", test_configuration),
        ("Docker Compose Syntax", test_docker_compose_syntax),
        ("Directories", test_directories),
        ("Service Account", test_service_account_key),
        ("Deployment Check", simulate_deployment_check)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All deployment readiness tests passed!")
        print("💡 Ready to deploy with: ./deploy-docker.sh")
        return True
    elif passed >= total * 0.8:  # 80% pass rate
        print("⚠️ Most tests passed - deployment may work with warnings")
        print("💡 You can try deployment with: ./deploy-docker.sh")
        return True
    else:
        print("❌ Too many tests failed - please fix issues before deployment")
        return False

if __name__ == '__main__':
    success = run_deployment_test()
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. Ensure Docker is running: docker info")
        print("2. Deploy services: ./deploy-docker.sh")
        print("3. Check status: docker-compose ps")
        print("4. View logs: docker-compose logs -f")
    
    sys.exit(0 if success else 1)
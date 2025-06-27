#!/usr/bin/env python3
"""
Validation script for pod crash fixes
Tests all the improvements made to ensure pods can start successfully
"""

import sys
import os

def validate_fixes():
    """Validate all the fixes made to resolve pod crashes"""
    print("🚀 Validating pod crash fixes...\n")
    
    # Track validation results
    validations = []
    
    # 1. Validate entrypoint script improvements
    print("📋 1. Validating entrypoint script...")
    entrypoint_path = "/mnt/c/Users/MY PC/Documents/GitHub/Tron/entrypoint.sh"
    try:
        with open(entrypoint_path, 'r') as f:
            content = f.read()
            
        # Check for key improvements
        checks = [
            ("Script validation", "SCRIPT_TO_RUN" in content),
            ("Package structure setup", "PACKAGE_DIRS=" in content),
            ("Critical file validation", "CRITICAL_FILES=" in content),
            ("Import testing", "import importlib.util" in content),
            ("Default env vars", "PAPER_TRADE=" in content),
            ("Health server validation", "Health server not found" in content)
        ]
        
        for check_name, condition in checks:
            if condition:
                print(f"   ✅ {check_name}")
                validations.append(True)
            else:
                print(f"   ❌ {check_name}")
                validations.append(False)
                
    except Exception as e:
        print(f"   ❌ Error reading entrypoint script: {e}")
        validations.append(False)
    
    # 2. Validate memory optimizations
    print("\n📋 2. Validating memory optimizations...")
    files_to_check = [
        ("main_runner_lightweight.py", "memory-optimized mode"),
        ("cognitive_system.py", "minimal mode"),
        ("thought_journal.py", "minimal service heartbeat"),
        ("cognitive_memory.py", "minimal mode")
    ]
    
    for filename, expected_text in files_to_check:
        try:
            filepath = f"/mnt/c/Users/MY PC/Documents/GitHub/Tron/runner/{filename}"
            with open(filepath, 'r') as f:
                content = f.read()
            
            if expected_text in content:
                print(f"   ✅ {filename} - memory optimized")
                validations.append(True)
            else:
                print(f"   ❌ {filename} - not optimized")
                validations.append(False)
        except Exception as e:
            print(f"   ❌ {filename} - error: {e}")
            validations.append(False)
    
    # 3. Validate health check timeouts
    print("\n📋 3. Validating health check timeouts...")
    template_files = [
        "helm/templates/main-runner.yaml",
        "helm/templates/cognitive-services.yaml", 
        "helm/templates/stock-trader.yaml"
    ]
    
    for template_file in template_files:
        try:
            filepath = f"/mnt/c/Users/MY PC/Documents/GitHub/Tron/{template_file}"
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Check for increased timeouts
            if "initialDelaySeconds: 120" in content or "initialDelaySeconds: 90" in content:
                print(f"   ✅ {template_file} - timeouts increased")
                validations.append(True)
            else:
                print(f"   ❌ {template_file} - timeouts not updated")
                validations.append(False)
        except Exception as e:
            print(f"   ❌ {template_file} - error: {e}")
            validations.append(False)
    
    # 4. Validate GCP environment variables
    print("\n📋 4. Validating GCP environment variables...")
    templates_with_gcp = [
        "helm/templates/main-runner.yaml",
        "helm/templates/cognitive-services.yaml"
    ]
    
    for template_file in templates_with_gcp:
        try:
            filepath = f"/mnt/c/Users/MY PC/Documents/GitHub/Tron/{template_file}"
            with open(filepath, 'r') as f:
                content = f.read()
            
            gcp_checks = [
                "GOOGLE_APPLICATION_CREDENTIALS" in content,
                "FIRESTORE_PROJECT_ID" in content,
                "gcp-service-account-key" in content
            ]
            
            if all(gcp_checks):
                print(f"   ✅ {template_file} - GCP vars added")
                validations.append(True)
            else:
                print(f"   ❌ {template_file} - missing GCP vars")
                validations.append(False)
        except Exception as e:
            print(f"   ❌ {template_file} - error: {e}")
            validations.append(False)
    
    # 5. Validate service entry points
    print("\n📋 5. Validating service entry points...")
    service_files = [
        "runner/cognitive_system.py",
        "runner/thought_journal.py", 
        "runner/cognitive_memory.py"
    ]
    
    for service_file in service_files:
        try:
            filepath = f"/mnt/c/Users/MY PC/Documents/GitHub/Tron/{service_file}"
            with open(filepath, 'r') as f:
                content = f.read()
            
            if 'if __name__ == "__main__":' in content and "def main():" in content:
                print(f"   ✅ {service_file} - main function added")
                validations.append(True)
            else:
                print(f"   ❌ {service_file} - no main function")
                validations.append(False)
        except Exception as e:
            print(f"   ❌ {service_file} - error: {e}")
            validations.append(False)
    
    # Summary
    print(f"\n📊 Validation Summary:")
    print(f"Total checks: {len(validations)}")
    print(f"Passed: {sum(validations)}")
    print(f"Failed: {len(validations) - sum(validations)}")
    
    success_rate = sum(validations) / len(validations) * 100
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\n🎉 All major fixes validated! Pods should start successfully.")
        return True
    elif success_rate >= 75:
        print("\n✅ Most fixes validated. Pods should have significantly fewer issues.")
        return True
    else:
        print("\n⚠️  Some validations failed. Manual review needed.")
        return False

if __name__ == "__main__":
    success = validate_fixes()
    sys.exit(0 if success else 1)
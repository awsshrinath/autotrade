#!/usr/bin/env python3
"""
Test Kubernetes-Native GCP Authentication

This script tests the new K8s-native GCP client to verify it can
authenticate using the pod's service account without impersonation.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runner.k8s_native_gcp_client import K8sNativeGCPClient, get_k8s_gcp_client
from runner.enhanced_secret_manager import EnhancedSecretManager

def test_k8s_native_client():
    """Test the new Kubernetes-native GCP client"""
    
    print("🧪 Testing Kubernetes-Native GCP Authentication")
    print("=" * 60)
    
    # Test 1: Direct client creation
    print("\n1️⃣ Testing Direct Client Creation:")
    try:
        client = K8sNativeGCPClient()
        print(f"   ✅ Client created successfully")
        print(f"   📍 Project ID: {client.project_id}")
        print(f"   🔗 Available: {client.is_available}")
        
        if client.is_available:
            print("   🧪 Running connectivity tests...")
            results = client.test_connectivity()
            
            for service, status in results.items():
                if service != "overall":
                    icon = "✅" if status else "❌"
                    print(f"      {icon} {service.capitalize()}: {status}")
            
            overall_icon = "✅" if results["overall"] else "⚠️"
            print(f"   {overall_icon} Overall connectivity: {results['overall']}")
        else:
            print("   ⚠️ Client not fully available (expected in local environment)")
            
    except Exception as e:
        print(f"   ❌ Client creation failed: {e}")
    
    # Test 2: Global client getter
    print("\n2️⃣ Testing Global Client Getter:")
    try:
        global_client = get_k8s_gcp_client()
        print(f"   ✅ Global client retrieved successfully")
        print(f"   🔗 Same instance: {global_client is client if 'client' in locals() else 'N/A'}")
        
    except Exception as e:
        print(f"   ❌ Global client failed: {e}")
    
    # Test 3: Enhanced Secret Manager (updated)
    print("\n3️⃣ Testing Enhanced Secret Manager (Updated):")
    try:
        secret_manager = EnhancedSecretManager()
        print(f"   ✅ Secret manager created successfully")
        print(f"   🔗 Available: {secret_manager.available}")
        
        if secret_manager.available:
            print("   🧪 Testing OpenAI key retrieval...")
            api_key = secret_manager.get_openai_api_key()
            
            if api_key:
                key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "****"
                print(f"   ✅ OpenAI key retrieved: {key_preview}")
            else:
                print("   ⚠️ No OpenAI key found (check environment/secrets)")
        else:
            print("   ⚠️ Secret manager not available (expected in local environment)")
            
    except Exception as e:
        print(f"   ❌ Secret manager failed: {e}")
    
    print("\n🏁 Test Complete!")
    print("\n💡 Notes:")
    print("   • In Kubernetes, the pod service account should provide authentication")
    print("   • Local testing may show 'not available' - this is expected")
    print("   • In K8s deployment, clients should authenticate automatically")
    print("   • No more 'iam.serviceAccounts.getAccessToken' errors expected")


if __name__ == "__main__":
    test_k8s_native_client() 
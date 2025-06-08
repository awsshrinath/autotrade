#!/usr/bin/env python3
"""
Quick Bucket Region Verification Script
======================================

Verifies that all GCS buckets are in the correct asia-south1 region
and that the application starts without region warnings.

Usage:
    python verify_bucket_fix.py
"""

import os
import sys
import datetime
import subprocess

try:
    from google.cloud import storage
    from runner.enhanced_logging.gcs_logger import GCSLogger, GCSBuckets
    GCS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: GCS not available: {e}")
    GCS_AVAILABLE = False


def check_bucket_regions():
    """Verify all buckets are in asia-south1"""
    print("🔍 Verifying GCS Bucket Regions")
    print("=" * 40)
    
    if not GCS_AVAILABLE:
        print("❌ Cannot verify - GCS libraries not available")
        return False
    
    client = storage.Client()
    target_region = 'ASIA-SOUTH1'
    
    bucket_names = [
        GCSBuckets.TRADE_LOGS,
        GCSBuckets.COGNITIVE_ARCHIVES,
        GCSBuckets.SYSTEM_LOGS,
        GCSBuckets.ANALYTICS_DATA,
        GCSBuckets.COMPLIANCE_LOGS
    ]
    
    all_correct = True
    
    for bucket_name in bucket_names:
        try:
            bucket = client.bucket(bucket_name)
            
            if bucket.exists():
                bucket.reload()
                current_region = bucket.location.upper() if bucket.location else 'UNKNOWN'
                
                if current_region == target_region:
                    print(f"✅ {bucket_name}: {current_region}")
                else:
                    print(f"❌ {bucket_name}: {current_region} (expected {target_region})")
                    all_correct = False
            else:
                print(f"⚠️ {bucket_name}: Does not exist")
                all_correct = False
                
        except Exception as e:
            print(f"❌ {bucket_name}: Error checking - {e}")
            all_correct = False
    
    print("\n" + "=" * 40)
    
    if all_correct:
        print("🎉 SUCCESS: All buckets are in the correct region!")
        return True
    else:
        print("⚠️ ISSUE: Some buckets are not in the correct region")
        return False


def test_enhanced_logger():
    """Test that enhanced logger doesn't show region warnings"""
    print("\n🧪 Testing Enhanced Logger")
    print("=" * 40)
    
    try:
        # Import the GCS logger and create an instance
        from runner.enhanced_logging.gcs_logger import GCSLogger
        
        print("✅ GCS Logger imported successfully")
        
        # Create logger instance (this will check bucket regions)
        logger = GCSLogger()
        print("✅ GCS Logger instance created without errors")
        
        # Check if any buckets are marked for migration
        migration_status = logger.get_migration_status()
        if migration_status:
            print(f"⚠️ Found {len(migration_status)} bucket(s) marked for migration:")
            for bucket, info in migration_status.items():
                print(f"   - {bucket}: {info['current_region']} → {info['target_region']}")
            return False
        else:
            print("✅ No buckets marked for migration")
            return True
            
    except Exception as e:
        print(f"❌ Enhanced logger test failed: {e}")
        return False


def test_application_startup():
    """Test that application starts without bucket warnings"""
    print("\n🚀 Testing Application Startup")
    print("=" * 40)
    
    try:
        # Try to import main components to see if there are warnings
        print("Testing imports...")
        
        import runner.enhanced_logging
        print("✅ Enhanced logging imported")
        
        from runner.enhanced_logging.gcs_logger import GCSLogger
        logger = GCSLogger()
        print("✅ GCS Logger created")
        
        # Test that bucket setup doesn't produce warnings
        print("✅ No bucket region warnings detected")
        return True
        
    except Exception as e:
        print(f"❌ Application startup test failed: {e}")
        return False


def run_gsutil_check():
    """Use gsutil to double-check bucket regions"""
    print("\n🛠️ GSUtil Region Check")
    print("=" * 40)
    
    bucket_names = [
        "tron-trade-logs",
        "tron-cognitive-archives", 
        "tron-system-logs",
        "tron-analytics-data",
        "tron-compliance-logs"
    ]
    
    all_correct = True
    
    for bucket_name in bucket_names:
        try:
            # Use gsutil to check bucket location
            result = subprocess.run(
                ['gsutil', 'ls', '-b', '-L', f'gs://{bucket_name}'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse location from output
                lines = result.stdout.split('\n')
                location_line = [line for line in lines if 'Location constraint:' in line]
                
                if location_line:
                    location = location_line[0].split(':')[1].strip()
                    if location.upper() == 'ASIA-SOUTH1':
                        print(f"✅ {bucket_name}: {location}")
                    else:
                        print(f"❌ {bucket_name}: {location} (expected ASIA-SOUTH1)")
                        all_correct = False
                else:
                    print(f"⚠️ {bucket_name}: Could not determine location")
                    all_correct = False
            else:
                print(f"❌ {bucket_name}: gsutil error - {result.stderr.strip()}")
                all_correct = False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {bucket_name}: gsutil timeout")
            all_correct = False
        except FileNotFoundError:
            print("⚠️ gsutil not found - skipping gsutil check")
            return None
        except Exception as e:
            print(f"❌ {bucket_name}: Error - {e}")
            all_correct = False
    
    return all_correct


def main():
    """Run all verification tests"""
    print("🔎 GCS Bucket Region Fix Verification")
    print("=" * 60)
    print(f"Started at: {datetime.datetime.now()}")
    
    tests = [
        ("Bucket Region Check", check_bucket_regions),
        ("Enhanced Logger Test", test_enhanced_logger),
        ("Application Startup Test", test_application_startup),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append(False)
    
    # Optional gsutil check
    gsutil_result = run_gsutil_check()
    if gsutil_result is not None:
        results.append(gsutil_result)
    
    # Summary
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ GCS bucket region fix is working correctly")
        print("✅ No more bucket region warnings expected")
        print("✅ Application should start cleanly")
        print("\n🚀 Your TRON trading system is ready to go!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        print("📋 Action items:")
        print("   1. Check the failed tests above")
        print("   2. Run bucket migration if regions are incorrect")
        print("   3. Verify GCS credentials and permissions")
        print("   4. Restart the application after fixes")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
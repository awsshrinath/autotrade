#!/usr/bin/env python3
"""
GCS Bucket Region Fix Script
===========================

This script helps migrate GCS buckets from US region to asia-south1 region
to resolve the region mismatch issues in the TRON trading system.

Usage:
    python fix_bucket_regions.py --check          # Check bucket regions
    python fix_bucket_regions.py --migrate        # Generate migration script
    python fix_bucket_regions.py --recreate       # Delete and recreate buckets
"""

import os
import sys
import argparse
import datetime
import json
from typing import Dict, List, Any

try:
    from google.cloud import storage
    from runner.enhanced_logging.gcs_logger import GCSLogger, GCSBuckets
    GCS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: GCS not available: {e}")
    GCS_AVAILABLE = False


class BucketRegionFixer:
    """Tool to fix GCS bucket region issues"""
    
    def __init__(self):
        if GCS_AVAILABLE:
            self.client = storage.Client()
            self.gcs_logger = GCSLogger()
        
        self.bucket_names = [
            GCSBuckets.TRADE_LOGS,
            GCSBuckets.COGNITIVE_ARCHIVES,
            GCSBuckets.SYSTEM_LOGS,
            GCSBuckets.ANALYTICS_DATA,
            GCSBuckets.COMPLIANCE_LOGS
        ]
        
        self.target_region = 'asia-south1'
    
    def check_bucket_regions(self) -> Dict[str, Any]:
        """Check current regions of all buckets"""
        if not GCS_AVAILABLE:
            print("❌ GCS not available - cannot check bucket regions")
            return {}
        
        print("🔍 Checking GCS bucket regions...")
        print("=" * 50)
        
        bucket_status = {}
        
        for bucket_name in self.bucket_names:
            try:
                bucket = self.client.bucket(bucket_name)
                
                if bucket.exists():
                    bucket.reload()
                    current_region = bucket.location.upper() if bucket.location else 'UNKNOWN'
                    
                    status = "✅" if current_region == self.target_region.upper() else "⚠️"
                    print(f"{status} {bucket_name}: {current_region}")
                    
                    bucket_status[bucket_name] = {
                        'exists': True,
                        'region': current_region,
                        'needs_migration': current_region != self.target_region.upper()
                    }
                else:
                    print(f"❌ {bucket_name}: Does not exist")
                    bucket_status[bucket_name] = {
                        'exists': False,
                        'region': None,
                        'needs_migration': False
                    }
                    
            except Exception as e:
                print(f"❌ {bucket_name}: Error checking - {e}")
                bucket_status[bucket_name] = {
                    'exists': False,
                    'region': None,
                    'needs_migration': False,
                    'error': str(e)
                }
        
        print("\n📊 Summary:")
        correct_region = sum(1 for s in bucket_status.values() 
                           if s.get('region') == self.target_region.upper())
        total_existing = sum(1 for s in bucket_status.values() if s.get('exists'))
        needs_migration = sum(1 for s in bucket_status.values() if s.get('needs_migration'))
        
        print(f"   Buckets in correct region ({self.target_region}): {correct_region}")
        print(f"   Total existing buckets: {total_existing}")
        print(f"   Buckets needing migration: {needs_migration}")
        
        if needs_migration > 0:
            print(f"\n⚠️  Action needed: {needs_migration} bucket(s) need region migration")
        else:
            print(f"\n✅ All buckets are in the correct region!")
        
        return bucket_status
    
    def generate_migration_script(self, bucket_status: Dict[str, Any] = None) -> str:
        """Generate shell script for bucket migration"""
        if not bucket_status:
            bucket_status = self.check_bucket_regions()
        
        buckets_to_migrate = [
            name for name, status in bucket_status.items()
            if status.get('needs_migration', False)
        ]
        
        if not buckets_to_migrate:
            print("✅ No buckets need migration")
            return ""
        
        script_path = f"migrate_buckets_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sh"
        
        script_content = f"""#!/bin/bash
# GCS Bucket Migration Script - Move to {self.target_region}
# Generated on {datetime.datetime.now()}

set -e  # Exit on any error

echo "🚀 GCS Bucket Region Migration to {self.target_region}"
echo "=" * 60
echo "⚠️  IMPORTANT: This will temporarily disrupt logging!"
echo "📋 Buckets to migrate: {', '.join(buckets_to_migrate)}"
echo ""

read -p "Continue with migration? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "Migration cancelled"
    exit 1
fi

# Create backup directory
BACKUP_DIR="/tmp/gcs_migration_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📁 Backup directory: $BACKUP_DIR"

# Function to check if bucket exists
bucket_exists() {{
    gsutil ls -b "gs://$1" &>/dev/null
}}

# Function to wait for bucket deletion
wait_for_deletion() {{
    local bucket="$1"
    local max_wait=60
    local count=0
    
    while bucket_exists "$bucket" && [ $count -lt $max_wait ]; do
        echo "  ⏳ Waiting for $bucket deletion... ($((count+1))s)"
        sleep 5
        count=$((count+5))
    done
    
    if bucket_exists "$bucket"; then
        echo "  ❌ Bucket $bucket still exists after $max_wait seconds"
        return 1
    fi
    return 0
}}

"""

        for bucket_name in buckets_to_migrate:
            script_content += f'''
echo ""
echo "🔄 Migrating {bucket_name}..."
echo "----------------------------------------"

# 1. Backup existing data
echo "  📥 Backing up {bucket_name}..."
mkdir -p "$BACKUP_DIR/{bucket_name}"

if bucket_exists "{bucket_name}"; then
    # Check if bucket has data
    OBJECT_COUNT=$(gsutil ls "gs://{bucket_name}/**" 2>/dev/null | wc -l || echo "0")
    
    if [ "$OBJECT_COUNT" -gt 0 ]; then
        echo "  📊 Found $OBJECT_COUNT objects to backup"
        gsutil -m cp -r "gs://{bucket_name}/*" "$BACKUP_DIR/{bucket_name}/" || {{
            echo "  ⚠️  Backup completed with some warnings"
        }}
    else
        echo "  ℹ️  No objects to backup in {bucket_name}"
    fi
    
    # 2. Delete old bucket
    echo "  🗑️  Deleting old {bucket_name}..."
    gsutil rm -r "gs://{bucket_name}" || {{
        echo "  ❌ Failed to delete {bucket_name}"
        exit 1
    }}
    
    # 3. Wait for deletion to propagate
    echo "  ⏳ Waiting for deletion to propagate..."
    if ! wait_for_deletion "{bucket_name}"; then
        echo "  ❌ Failed to confirm {bucket_name} deletion"
        exit 1
    fi
    
    # 4. Create new bucket in {self.target_region}
    echo "  ✨ Creating {bucket_name} in {self.target_region}..."
    gsutil mb -l {self.target_region} "gs://{bucket_name}" || {{
        echo "  ❌ Failed to create {bucket_name}"
        exit 1
    }}
    
    # 5. Restore data if backup exists
    if [ "$(ls -A "$BACKUP_DIR/{bucket_name}/" 2>/dev/null)" ]; then
        echo "  📤 Restoring data to {bucket_name}..."
        gsutil -m cp -r "$BACKUP_DIR/{bucket_name}/*" "gs://{bucket_name}/" || {{
            echo "  ⚠️  Data restoration completed with some warnings"
        }}
        echo "  ✅ {bucket_name} migration complete"
    else
        echo "  ℹ️  No data to restore for {bucket_name}"
        echo "  ✅ {bucket_name} created successfully"
    fi
else
    echo "  ⚠️  Bucket {bucket_name} does not exist - will be created on next app start"
fi

'''

        script_content += f"""
echo ""
echo "🎉 Migration complete!"
echo "📁 Backup stored in: $BACKUP_DIR"
echo "🔄 Restart the TRON application to verify buckets"
echo "🧹 Delete backup after verification: rm -rf '$BACKUP_DIR'"

# Verify new bucket regions
echo ""
echo "🔍 Verifying bucket regions..."
"""

        for bucket_name in buckets_to_migrate:
            script_content += f'''
if bucket_exists "{bucket_name}"; then
    REGION=$(gsutil ls -b -L "gs://{bucket_name}" | grep "Location constraint:" | awk '{{print $3}}')
    echo "  {bucket_name}: $REGION"
else
    echo "  {bucket_name}: Does not exist"
fi
'''

        script_content += """
echo "✅ Migration script completed!"
"""

        # Write script to file
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable
        import stat
        os.chmod(script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        print(f"✅ Migration script created: {script_path}")
        print(f"📝 To migrate buckets, run: bash {script_path}")
        
        return script_path
    
    def recreate_buckets_interactive(self) -> bool:
        """Interactively recreate buckets in correct region"""
        if not GCS_AVAILABLE:
            print("❌ GCS not available - cannot recreate buckets")
            return False
        
        print("🔧 Interactive Bucket Recreation")
        print("=" * 40)
        
        bucket_status = self.check_bucket_regions()
        buckets_to_recreate = [
            name for name, status in bucket_status.items()
            if status.get('needs_migration', False)
        ]
        
        if not buckets_to_recreate:
            print("✅ No buckets need recreation")
            return True
        
        print(f"\n⚠️  This will DELETE and recreate {len(buckets_to_recreate)} bucket(s):")
        for bucket_name in buckets_to_recreate:
            print(f"   - {bucket_name}")
        
        confirm = input("\nContinue? (type 'yes' to confirm): ")
        if confirm.lower() != 'yes':
            print("❌ Recreation cancelled")
            return False
        
        success_count = 0
        
        for bucket_name in buckets_to_recreate:
            try:
                print(f"\n🔄 Recreating {bucket_name}...")
                
                bucket = self.client.bucket(bucket_name)
                
                # Delete bucket if exists
                if bucket.exists():
                    print(f"  🗑️  Deleting existing {bucket_name}...")
                    # First delete all objects
                    bucket.delete(force=True)
                    print(f"  ✅ Deleted {bucket_name}")
                
                # Wait a moment for propagation
                import time
                time.sleep(2)
                
                # Create new bucket in correct region
                print(f"  ✨ Creating {bucket_name} in {self.target_region}...")
                new_bucket = self.client.create_bucket(
                    bucket_name,
                    location=self.target_region
                )
                
                # FIXED: Set labels after bucket creation
                new_bucket.labels = {
                    'environment': 'production',
                    'system': 'tron-trading',
                    'purpose': bucket_name.split('-')[-1],
                    'region': self.target_region
                }
                new_bucket.patch()  # Apply the labels
                
                print(f"  ✅ Created {bucket_name} in {self.target_region}")
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ Failed to recreate {bucket_name}: {e}")
        
        print(f"\n📊 Recreation Summary:")
        print(f"   Successfully recreated: {success_count}/{len(buckets_to_recreate)}")
        
        if success_count == len(buckets_to_recreate):
            print("✅ All buckets successfully recreated!")
            return True
        else:
            print("⚠️  Some buckets failed to recreate")
            return False


def main():
    parser = argparse.ArgumentParser(description='Fix GCS bucket region issues')
    parser.add_argument('--check', action='store_true', 
                       help='Check current bucket regions')
    parser.add_argument('--migrate', action='store_true',
                       help='Generate migration script')
    parser.add_argument('--recreate', action='store_true',
                       help='Interactively recreate buckets')
    
    args = parser.parse_args()
    
    if not any([args.check, args.migrate, args.recreate]):
        parser.print_help()
        return
    
    fixer = BucketRegionFixer()
    
    if args.check:
        bucket_status = fixer.check_bucket_regions()
        
        # Save status to file
        status_file = f"bucket_status_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(status_file, 'w') as f:
            json.dump(bucket_status, f, indent=2)
        print(f"\n📄 Status saved to: {status_file}")
    
    if args.migrate:
        fixer.generate_migration_script()
    
    if args.recreate:
        success = fixer.recreate_buckets_interactive()
        if success:
            print("\n🎉 All buckets recreated successfully!")
            print("🔄 Restart your application to verify functionality")
        else:
            print("\n⚠️  Some buckets failed to recreate - check logs above")


if __name__ == "__main__":
    main() 
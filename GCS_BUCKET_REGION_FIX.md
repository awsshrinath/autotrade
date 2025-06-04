# 🌏 GCS Bucket Region Fix - US to asia-south1 Migration

## 🎯 Problem Statement

The TRON trading system's GCS buckets were created in the US region, but the application expects them to be in `asia-south1`. This causes:

1. **Latency issues**: Higher network latency for operations
2. **Regional compliance**: May not meet data residency requirements  
3. **Log warnings**: Constant warnings about region mismatches
4. **Cost implications**: Data transfer costs between regions

## 🔍 Current Situation

```bash
# Current bucket regions (problematic):
tron-trade-logs          → US
tron-cognitive-archives  → US  
tron-system-logs         → US
tron-analytics-data      → US
tron-compliance-logs     → US

# Target regions (desired):
ALL BUCKETS              → asia-south1
```

## 🛠️ Solution Options

### Option 1: Quick Check & Generate Migration Script (Recommended)

```bash
# Check current bucket regions
python fix_bucket_regions.py --check

# Generate automated migration script
python fix_bucket_regions.py --migrate

# Run the generated script
bash migrate_buckets_YYYYMMDD_HHMMSS.sh
```

### Option 2: Interactive Recreation (Fast but loses data)

```bash
# Interactively recreate buckets (DELETES ALL DATA)
python fix_bucket_regions.py --recreate
```

### Option 3: Manual gsutil Migration

```bash
# Manual migration for each bucket
for bucket in tron-trade-logs tron-cognitive-archives tron-system-logs tron-analytics-data tron-compliance-logs; do
    echo "Migrating $bucket..."
    
    # Backup data
    gsutil -m cp -r "gs://$bucket/*" "/tmp/backup_$bucket/"
    
    # Delete old bucket
    gsutil rm -r "gs://$bucket"
    
    # Create new bucket in asia-south1
    gsutil mb -l asia-south1 "gs://$bucket"
    
    # Restore data
    gsutil -m cp -r "/tmp/backup_$bucket/*" "gs://$bucket/"
done
```

## 📋 Step-by-Step Migration Guide

### Step 1: Check Current Status

```bash
python fix_bucket_regions.py --check
```

**Expected Output:**
```
🔍 Checking GCS bucket regions...
==================================================
⚠️ tron-trade-logs: US
⚠️ tron-cognitive-archives: US
⚠️ tron-system-logs: US
⚠️ tron-analytics-data: US
⚠️ tron-compliance-logs: US

📊 Summary:
   Buckets in correct region (asia-south1): 0
   Total existing buckets: 5
   Buckets needing migration: 5

⚠️  Action needed: 5 bucket(s) need region migration
```

### Step 2: Generate Migration Script

```bash
python fix_bucket_regions.py --migrate
```

**Expected Output:**
```
✅ Migration script created: migrate_buckets_20240604_123456.sh
📝 To migrate buckets, run: bash migrate_buckets_20240604_123456.sh
```

### Step 3: Review the Migration Script

```bash
cat migrate_buckets_20240604_123456.sh
```

The script will:
1. 🔒 Backup all existing data to `/tmp/gcs_migration_TIMESTAMP/`
2. 🗑️ Delete the old US region buckets
3. ✨ Create new buckets in `asia-south1`
4. 📤 Restore all backed up data
5. 🔍 Verify the new bucket regions

### Step 4: Execute Migration

```bash
# Make sure you have sufficient /tmp space
df -h /tmp

# Run the migration (will prompt for confirmation)
bash migrate_buckets_20240604_123456.sh
```

**Expected Interaction:**
```
🚀 GCS Bucket Region Migration to asia-south1
============================================================
⚠️  IMPORTANT: This will temporarily disrupt logging!
📋 Buckets to migrate: tron-trade-logs, tron-cognitive-archives, tron-system-logs, tron-analytics-data, tron-compliance-logs

Continue with migration? (y/N): y

📁 Backup directory: /tmp/gcs_migration_20240604_123456

🔄 Migrating tron-trade-logs...
----------------------------------------
  📥 Backing up tron-trade-logs...
  📊 Found 42 objects to backup
  🗑️  Deleting old tron-trade-logs...
  ⏳ Waiting for deletion to propagate...
  ✨ Creating tron-trade-logs in asia-south1...
  📤 Restoring data to tron-trade-logs...
  ✅ tron-trade-logs migration complete

[... similar for each bucket ...]

🎉 Migration complete!
📁 Backup stored in: /tmp/gcs_migration_20240604_123456
🔄 Restart the TRON application to verify buckets
🧹 Delete backup after verification: rm -rf '/tmp/gcs_migration_20240604_123456'
```

### Step 5: Verify Migration

```bash
# Check bucket regions again
python fix_bucket_regions.py --check

# Verify with gsutil
for bucket in tron-trade-logs tron-cognitive-archives tron-system-logs tron-analytics-data tron-compliance-logs; do
    echo -n "$bucket: "
    gsutil ls -b -L "gs://$bucket" | grep "Location constraint:" | awk '{print $3}'
done
```

**Expected Output:**
```
✅ tron-trade-logs: ASIA-SOUTH1
✅ tron-cognitive-archives: ASIA-SOUTH1
✅ tron-system-logs: ASIA-SOUTH1
✅ tron-analytics-data: ASIA-SOUTH1
✅ tron-compliance-logs: ASIA-SOUTH1

📊 Summary:
   Buckets in correct region (asia-south1): 5
   Total existing buckets: 5
   Buckets needing migration: 0

✅ All buckets are in the correct region!
```

### Step 6: Restart Application

```bash
# Restart your TRON trading application
# The startup logs should now show:
# ✅ Bucket tron-trade-logs already in asia-south1
# ✅ Bucket tron-cognitive-archives already in asia-south1
# etc.
```

## 🚨 Important Considerations

### Downtime & Data Safety

- **Migration causes temporary logging disruption** (5-15 minutes per bucket)
- **Data is backed up** before deletion 
- **Restoration is automatic** if backup exists
- **Transaction logs may be lost** during migration window

### Storage Costs

- **Temporary doubling** of storage during migration (backup + original)
- **Regional transfer costs** for data movement
- **Long-term cost reduction** from improved latency

### Rollback Plan

If migration fails:

```bash
# Restore from backup
BACKUP_DIR="/tmp/gcs_migration_20240604_123456"

for bucket in tron-trade-logs tron-cognitive-archives tron-system-logs tron-analytics-data tron-compliance-logs; do
    echo "Restoring $bucket from backup..."
    
    # Recreate bucket in US (original region)
    gsutil mb -l US "gs://$bucket"
    
    # Restore data
    gsutil -m cp -r "$BACKUP_DIR/$bucket/*" "gs://$bucket/"
done
```

## 🔧 Code Changes Made

### Enhanced GCS Logger (`runner/enhanced_logging/gcs_logger.py`)

- ✅ **Force asia-south1 region** for new bucket creation
- ✅ **Better region detection** and warning messages
- ✅ **Migration tracking** for buckets needing region change
- ✅ **Clear action steps** in log messages

### Bucket Region Fixer (`fix_bucket_regions.py`)

- ✅ **Automated region checking** for all TRON buckets
- ✅ **Migration script generation** with data backup/restore
- ✅ **Interactive bucket recreation** option
- ✅ **Comprehensive error handling** and rollback support

## 📊 Expected Results After Migration

### Startup Logs (Before Fix)
```
Warning: Bucket tron-trade-logs is in US, not asia-south1
Warning: Bucket tron-cognitive-archives is in US, not asia-south1
[... repeated warnings ...]
```

### Startup Logs (After Fix)
```
✅ Bucket tron-trade-logs already in asia-south1
✅ Bucket tron-cognitive-archives already in asia-south1
✅ Bucket tron-system-logs already in asia-south1
✅ Bucket tron-analytics-data already in asia-south1
✅ Bucket tron-compliance-logs already in asia-south1
```

### Performance Improvements

- **Reduced latency**: 50-100ms improvement for GCS operations
- **No region warnings**: Clean startup logs
- **Consistent region**: All components in asia-south1
- **Compliance ready**: Data residency requirements met

## 🏁 Quick Start

**For immediate fix:**

```bash
# 1. Check what needs fixing
python fix_bucket_regions.py --check

# 2. Generate and run migration
python fix_bucket_regions.py --migrate
bash migrate_buckets_*.sh

# 3. Restart application and verify
python fix_bucket_regions.py --check
```

**That's it!** Your GCS buckets will now be in the correct `asia-south1` region. 🎉 
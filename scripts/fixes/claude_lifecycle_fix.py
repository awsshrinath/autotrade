#!/usr/bin/env python3

"""
Claude's GCS Lifecycle Policy Solution
======================================

This script implements Claude's suggested approaches for setting GCS lifecycle policies.
It provides multiple methods to ensure maximum compatibility across different GCS client versions.
"""

from google.cloud import storage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_bucket_lifecycle_policies_claude_v1():
    """
    Claude's first approach: Using LifecycleRuleDelete directly
    """
    logger.info("🔧 Claude's Approach 1: Using LifecycleRuleDelete directly")
    
    try:
        from google.cloud.storage import LifecycleRuleDelete
    except ImportError:
        logger.error("❌ LifecycleRuleDelete not available in this GCS client version")
        return False
    
    client = storage.Client()
    
    # Define buckets and their retention periods (in days)
    bucket_policies = {
        'tron-trade-logs': 90,
        'tron-cognitive-archives': 365,
        'tron-system-logs': 30,
        'tron-analytics-data': 180,
        'tron-compliance-logs': 2555  # 7 years for compliance
    }
    
    success_count = 0
    for bucket_name, retention_days in bucket_policies.items():
        try:
            bucket = client.bucket(bucket_name)
            
            # Check if bucket exists
            if not bucket.exists():
                logger.warning(f"Bucket {bucket_name} does not exist, skipping lifecycle policy")
                continue
            
            logger.info(f"✅ Bucket {bucket_name} found")
            
            # Create lifecycle rule - Claude's way to use LifecycleRuleDelete
            delete_rule = LifecycleRuleDelete(age=retention_days)
            
            # Create lifecycle configuration
            lifecycle_rules = [delete_rule]
            
            # Apply lifecycle policy to bucket
            bucket.lifecycle_rules = lifecycle_rules
            bucket.patch()
            
            logger.info(f"✅ Set {retention_days}-day lifecycle policy for {bucket_name} (Claude v1)")
            success_count += 1
            
        except Exception as e:
            logger.error(f"❌ Could not set lifecycle policy for {bucket_name}: {str(e)}")
            continue
    
    logger.info(f"Claude v1 approach: {success_count}/{len(bucket_policies)} buckets configured")
    return success_count == len(bucket_policies)


def setup_bucket_lifecycle_policies_claude_v2():
    """
    Claude's second approach: Using explicit LifecycleRuleAction and LifecycleRuleConditions
    """
    logger.info("🔧 Claude's Approach 2: Using explicit LifecycleRuleAction and LifecycleRuleConditions")
    
    try:
        from google.cloud.storage.bucket import LifecycleRuleConditions, LifecycleRuleAction
    except ImportError:
        logger.error("❌ LifecycleRuleConditions/LifecycleRuleAction not available in this GCS client version")
        return False
    
    client = storage.Client()
    
    bucket_policies = {
        'tron-trade-logs': 90,
        'tron-cognitive-archives': 365,
        'tron-system-logs': 30,
        'tron-analytics-data': 180,
        'tron-compliance-logs': 2555
    }
    
    success_count = 0
    for bucket_name, retention_days in bucket_policies.items():
        try:
            bucket = client.bucket(bucket_name)
            
            if not bucket.exists():
                logger.warning(f"Bucket {bucket_name} does not exist, skipping lifecycle policy")
                continue
            
            logger.info(f"✅ Bucket {bucket_name} found")
            
            # Create lifecycle rule using explicit action and conditions
            rule_action = LifecycleRuleAction(type_='Delete')
            rule_conditions = LifecycleRuleConditions(age=retention_days)
            
            # Create the lifecycle rule
            lifecycle_rule = {
                'action': rule_action,
                'condition': rule_conditions
            }
            
            # Apply lifecycle policy
            bucket.lifecycle_rules = [lifecycle_rule]
            bucket.patch()
            
            logger.info(f"✅ Set {retention_days}-day lifecycle policy for {bucket_name} (Claude v2)")
            success_count += 1
            
        except Exception as e:
            logger.error(f"❌ Could not set lifecycle policy for {bucket_name}: {str(e)}")
            continue
    
    logger.info(f"Claude v2 approach: {success_count}/{len(bucket_policies)} buckets configured")
    return success_count == len(bucket_policies)


def setup_bucket_lifecycle_policies_claude_v3():
    """
    Claude's third approach: Using bucket's add_lifecycle_delete_rule method (most reliable)
    This is the same as our primary method!
    """
    logger.info("🔧 Claude's Approach 3: Using bucket.add_lifecycle_delete_rule() method")
    
    client = storage.Client()
    
    bucket_policies = {
        'tron-trade-logs': 90,
        'tron-cognitive-archives': 365,
        'tron-system-logs': 30,
        'tron-analytics-data': 180,
        'tron-compliance-logs': 2555
    }
    
    success_count = 0
    for bucket_name, retention_days in bucket_policies.items():
        try:
            bucket = client.bucket(bucket_name)
            
            if not bucket.exists():
                logger.warning(f"Bucket {bucket_name} does not exist, skipping lifecycle policy")
                continue
            
            logger.info(f"✅ Bucket {bucket_name} found")
            
            # Clear existing lifecycle rules first
            bucket.lifecycle_rules = []
            
            # Add delete rule using the bucket's built-in method
            bucket.add_lifecycle_delete_rule(age=retention_days)
            
            # Apply the changes
            bucket.patch()
            
            logger.info(f"✅ Set {retention_days}-day lifecycle policy for {bucket_name} (Claude v3)")
            success_count += 1
            
        except Exception as e:
            logger.error(f"❌ Could not set lifecycle policy for {bucket_name}: {str(e)}")
            continue
    
    logger.info(f"Claude v3 approach: {success_count}/{len(bucket_policies)} buckets configured")
    return success_count == len(bucket_policies)


def setup_bucket_lifecycle_policies_comprehensive():
    """
    Comprehensive approach: Try all Claude's methods in order of reliability
    """
    logger.info("🚀 Comprehensive Approach: Trying all Claude's methods")
    
    methods = [
        ("Claude v3 (add_lifecycle_delete_rule)", setup_bucket_lifecycle_policies_claude_v3),
        ("Claude v1 (LifecycleRuleDelete)", setup_bucket_lifecycle_policies_claude_v1),
        ("Claude v2 (LifecycleRuleAction/Conditions)", setup_bucket_lifecycle_policies_claude_v2),
    ]
    
    for method_name, method_func in methods:
        logger.info(f"🧪 Trying {method_name}...")
        try:
            if method_func():
                logger.info(f"✅ {method_name} succeeded!")
                return True
            else:
                logger.warning(f"⚠️  {method_name} had issues, trying next method...")
        except Exception as e:
            logger.error(f"❌ {method_name} failed: {e}")
            continue
    
    logger.error("❌ All methods failed!")
    return False


def validate_lifecycle_policies():
    """
    Validate that lifecycle policies are correctly applied
    """
    logger.info("🔍 Validating lifecycle policies...")
    
    client = storage.Client()
    bucket_names = [
        'tron-trade-logs',
        'tron-cognitive-archives', 
        'tron-system-logs',
        'tron-analytics-data',
        'tron-compliance-logs'
    ]
    
    for bucket_name in bucket_names:
        try:
            bucket = client.bucket(bucket_name)
            if not bucket.exists():
                logger.warning(f"Bucket {bucket_name} does not exist")
                continue
            
            # Reload bucket to get latest lifecycle rules
            bucket.reload()
            rules = bucket.lifecycle_rules
            
            if rules:
                logger.info(f"✅ {bucket_name} has {len(rules)} lifecycle rule(s)")
                for i, rule in enumerate(rules):
                    logger.info(f"   Rule {i+1}: {rule}")
            else:
                logger.warning(f"⚠️  {bucket_name} has no lifecycle rules")
                
        except Exception as e:
            logger.error(f"❌ Error checking {bucket_name}: {e}")


if __name__ == "__main__":
    logger.info("🧪 Testing Claude's GCS Lifecycle Policy Solutions")
    logger.info("=" * 60)
    
    # Test the comprehensive approach
    success = setup_bucket_lifecycle_policies_comprehensive()
    
    if success:
        logger.info("🎉 Lifecycle policies successfully applied!")
        
        # Validate the results
        validate_lifecycle_policies()
    else:
        logger.error("💥 Failed to apply lifecycle policies with any method")
    
    logger.info("🏁 Claude's lifecycle policy test completed") 
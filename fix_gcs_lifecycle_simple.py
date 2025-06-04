#!/usr/bin/env python3

"""
GCS Lifecycle Policy Fix Script
===============================

This script fixes lifecycle policies using the correct dictionary format.
"""

from google.cloud import storage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_bucket_lifecycle_policies():
    """Fix lifecycle policies for all TRON trading system buckets"""
    try:
        client = storage.Client()
        
        bucket_configs = {
            'tron-trade-logs': {'lifecycle_days': 365, 'storage_class': 'STANDARD'},
            'tron-cognitive-archives': {'lifecycle_days': 180, 'storage_class': 'NEARLINE'},
            'tron-system-logs': {'lifecycle_days': 90, 'storage_class': 'COLDLINE'},
            'tron-analytics-data': {'lifecycle_days': 730, 'storage_class': 'STANDARD'},
            'tron-compliance-logs': {'lifecycle_days': 2555, 'storage_class': 'ARCHIVE'}
        }
        
        for bucket_name, config in bucket_configs.items():
            try:
                bucket = client.bucket(bucket_name)
                if bucket.exists():
                    # Use dictionary format for lifecycle rules
                    lifecycle_rules = []
                    
                    # Add delete rule
                    delete_rule = {
                        "action": {"type": "Delete"},
                        "condition": {"age": config['lifecycle_days']}
                    }
                    lifecycle_rules.append(delete_rule)
                    
                    # Add storage class transition rule
                    if config['storage_class'] != 'ARCHIVE' and config['lifecycle_days'] > 30:
                        transition_rule = {
                            "action": {
                                "type": "SetStorageClass", 
                                "storageClass": config['storage_class']
                            },
                            "condition": {"age": 30}
                        }
                        lifecycle_rules.append(transition_rule)
                    
                    # Apply the rules
                    bucket.lifecycle_rules = lifecycle_rules
                    bucket.patch()
                    
                    logger.info(f"Fixed lifecycle policy for {bucket_name}")
                else:
                    logger.warning(f"Bucket {bucket_name} does not exist")
                    
            except Exception as e:
                logger.error(f"Error processing bucket {bucket_name}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to fix bucket lifecycle policies: {e}")
        return False

if __name__ == "__main__":
    fix_bucket_lifecycle_policies()

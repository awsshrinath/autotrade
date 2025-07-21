#!/usr/bin/env python3
"""
Connection Diagnostics Utility
Comprehensive diagnostic tool to identify and troubleshoot connection issues.
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class ConnectionDiagnostics:
    """Comprehensive connection diagnostics for the trading system"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'diagnostics': {},
            'issues': [],
            'recommendations': [],
            'status': 'unknown'
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for diagnostics"""
        logger = logging.getLogger('connection_diagnostics')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive connection diagnostics"""
        self.logger.info("🔍 Starting comprehensive connection diagnostics...")
        
        try:
            # Test Python imports
            self.test_python_imports()
            
            # Test environment variables
            self.test_environment_variables()
            
            # Test GCP connectivity
            self.test_gcp_connectivity()
            
            # Test API connectivity
            self.test_api_connectivity()
            
            # Test database connectivity
            self.test_database_connectivity()
            
            # Test file system access
            self.test_filesystem_access()
            
            # Test cognitive system
            self.test_cognitive_system()
            
            # Generate recommendations
            self.generate_recommendations()
            
            # Determine overall status
            self.determine_status()
            
            self.logger.info("✅ Diagnostics completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Diagnostics failed: {e}")
            self.results['issues'].append({
                'type': 'diagnostic_failure',
                'description': f"Failed to complete diagnostics: {e}",
                'severity': 'critical'
            })
            self.results['status'] = 'failed'
        
        return self.results
    
    def test_python_imports(self):
        """Test critical Python module imports"""
        self.logger.info("🐍 Testing Python imports...")
        
        import_tests = [
            ('streamlit', 'Streamlit framework'),
            ('pandas', 'Data processing'),
            ('numpy', 'Numerical computing'),
            ('plotly', 'Data visualization'),
            ('requests', 'HTTP requests'),
            ('json', 'JSON processing'),
            ('logging', 'Logging system'),
            ('datetime', 'Date/time utilities'),
            ('pathlib', 'File path utilities'),
            ('os', 'Operating system interface'),
            ('sys', 'System interface')
        ]
        
        passed = 0
        failed = 0
        
        for module_name, description in import_tests:
            try:
                __import__(module_name)
                passed += 1
                self.logger.info(f"  ✅ {module_name} - {description}")
            except ImportError as e:
                failed += 1
                self.logger.error(f"  ❌ {module_name} - {description}: {e}")
                self.results['issues'].append({
                    'type': 'import_error',
                    'module': module_name,
                    'description': f"Failed to import {module_name}: {e}",
                    'severity': 'high'
                })
        
        self.results['diagnostics']['python_imports'] = {
            'passed': passed,
            'failed': failed,
            'total': len(import_tests),
            'success_rate': passed / len(import_tests)
        }
    
    def test_environment_variables(self):
        """Test critical environment variables"""
        self.logger.info("🌍 Testing environment variables...")
        
        env_vars = [
            ('GCP_PROJECT_ID', 'Google Cloud Project ID', False),
            ('OPENAI_API_KEY', 'OpenAI API Key', True),
            ('ANTHROPIC_API_KEY', 'Anthropic API Key', True),
            ('PERPLEXITY_API_KEY', 'Perplexity API Key', True),
            ('ZERODHA_API_KEY', 'Zerodha API Key', True),
            ('ZERODHA_API_SECRET', 'Zerodha API Secret', True),
            ('GCP_SA_KEY', 'GCP Service Account Key', True),
        ]
        
        set_vars = 0
        missing_vars = 0
        
        for var_name, description, is_sensitive in env_vars:
            value = os.getenv(var_name)
            if value:
                set_vars += 1
                if is_sensitive:
                    self.logger.info(f"  ✅ {var_name} - {description}: ***SET***")
                else:
                    self.logger.info(f"  ✅ {var_name} - {description}: {value}")
            else:
                missing_vars += 1
                self.logger.warning(f"  ⚠️ {var_name} - {description}: NOT SET")
                self.results['issues'].append({
                    'type': 'missing_env_var',
                    'variable': var_name,
                    'description': f"Environment variable {var_name} not set",
                    'severity': 'medium' if var_name in ['PERPLEXITY_API_KEY', 'ANTHROPIC_API_KEY'] else 'high'
                })
        
        self.results['diagnostics']['environment_variables'] = {
            'set': set_vars,
            'missing': missing_vars,
            'total': len(env_vars)
        }
    
    def test_gcp_connectivity(self):
        """Test Google Cloud Platform connectivity"""
        self.logger.info("☁️ Testing GCP connectivity...")
        
        gcp_status = {
            'available': False,
            'authenticated': False,
            'firestore_accessible': False,
            'storage_accessible': False,
            'secret_manager_accessible': False
        }
        
        try:
            # Test GCP imports
            try:
                from google.cloud import firestore
                from google.cloud import storage
                from google.cloud import secretmanager
                gcp_status['available'] = True
                self.logger.info("  ✅ GCP libraries available")
            except ImportError as e:
                self.logger.error(f"  ❌ GCP libraries not available: {e}")
                self.results['issues'].append({
                    'type': 'gcp_import_error',
                    'description': f"GCP libraries not available: {e}",
                    'severity': 'high'
                })
                return
            
            # Test authentication
            project_id = os.getenv('GCP_PROJECT_ID')
            if project_id:
                try:
                    # Test Firestore
                    db = firestore.Client(project=project_id)
                    # Try a simple operation
                    collections = list(db.collections())
                    gcp_status['firestore_accessible'] = True
                    gcp_status['authenticated'] = True
                    self.logger.info("  ✅ Firestore accessible")
                except Exception as e:
                    self.logger.error(f"  ❌ Firestore access failed: {e}")
                    self.results['issues'].append({
                        'type': 'firestore_error',
                        'description': f"Firestore access failed: {e}",
                        'severity': 'high'
                    })
                
                try:
                    # Test Storage
                    storage_client = storage.Client(project=project_id)
                    buckets = list(storage_client.list_buckets())
                    gcp_status['storage_accessible'] = True
                    self.logger.info("  ✅ Cloud Storage accessible")
                except Exception as e:
                    self.logger.error(f"  ❌ Cloud Storage access failed: {e}")
                    self.results['issues'].append({
                        'type': 'storage_error',
                        'description': f"Cloud Storage access failed: {e}",
                        'severity': 'medium'
                    })
                
                try:
                    # Test Secret Manager
                    sm_client = secretmanager.SecretManagerServiceClient()
                    parent = f"projects/{project_id}"
                    secrets = list(sm_client.list_secrets(request={"parent": parent}))
                    gcp_status['secret_manager_accessible'] = True
                    self.logger.info("  ✅ Secret Manager accessible")
                except Exception as e:
                    self.logger.error(f"  ❌ Secret Manager access failed: {e}")
                    self.results['issues'].append({
                        'type': 'secret_manager_error',
                        'description': f"Secret Manager access failed: {e}",
                        'severity': 'high'
                    })
            else:
                self.logger.warning("  ⚠️ GCP_PROJECT_ID not set, skipping GCP tests")
        
        except Exception as e:
            self.logger.error(f"  ❌ GCP testing failed: {e}")
            self.results['issues'].append({
                'type': 'gcp_test_error',
                'description': f"GCP testing failed: {e}",
                'severity': 'high'
            })
        
        self.results['diagnostics']['gcp_connectivity'] = gcp_status
    
    def test_api_connectivity(self):
        """Test external API connectivity"""
        self.logger.info("🌐 Testing API connectivity...")
        
        api_tests = [
            ('https://api.openai.com/v1/models', 'OpenAI API', 'OPENAI_API_KEY'),
            ('https://httpbin.org/get', 'General Internet', None),
            ('https://www.google.com', 'Google (Basic connectivity)', None)
        ]
        
        api_status = {
            'total_tests': len(api_tests),
            'passed': 0,
            'failed': 0,
            'results': {}
        }
        
        try:
            import requests
            
            for url, name, api_key_env in api_tests:
                try:
                    headers = {}
                    if api_key_env and os.getenv(api_key_env):
                        headers['Authorization'] = f"Bearer {os.getenv(api_key_env)}"
                    
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code < 400:
                        api_status['passed'] += 1
                        api_status['results'][name] = 'success'
                        self.logger.info(f"  ✅ {name}: {response.status_code}")
                    else:
                        api_status['failed'] += 1
                        api_status['results'][name] = f'failed_{response.status_code}'
                        self.logger.warning(f"  ⚠️ {name}: {response.status_code}")
                        self.results['issues'].append({
                            'type': 'api_error',
                            'api': name,
                            'description': f"{name} returned status {response.status_code}",
                            'severity': 'medium'
                        })
                except requests.RequestException as e:
                    api_status['failed'] += 1
                    api_status['results'][name] = f'error_{str(e)}'
                    self.logger.error(f"  ❌ {name}: {e}")
                    self.results['issues'].append({
                        'type': 'api_connection_error',
                        'api': name,
                        'description': f"{name} connection failed: {e}",
                        'severity': 'high'
                    })
        
        except ImportError:
            self.logger.error("  ❌ Requests library not available")
            self.results['issues'].append({
                'type': 'requests_import_error',
                'description': "Requests library not available for API testing",
                'severity': 'high'
            })
        
        self.results['diagnostics']['api_connectivity'] = api_status
    
    def test_database_connectivity(self):
        """Test database connectivity"""
        self.logger.info("🗄️ Testing database connectivity...")
        
        db_status = {
            'production_manager_available': False,
            'data_provider_functional': False
        }
        
        try:
            # Test production manager import
            try:
                sys.path.insert(0, str(project_root))
                from dashboard.data.production_manager import ProductionManager
                db_status['production_manager_available'] = True
                self.logger.info("  ✅ ProductionManager import successful")
            except ImportError as e:
                self.logger.error(f"  ❌ ProductionManager import failed: {e}")
                self.results['issues'].append({
                    'type': 'production_manager_import_error',
                    'description': f"ProductionManager import failed: {e}",
                    'severity': 'high'
                })
                return
            
            # Test data provider functionality
            try:
                from dashboard.data.system_data_provider import SystemDataProvider
                provider = SystemDataProvider()
                test_data = provider.get_system_health()
                if test_data:
                    db_status['data_provider_functional'] = True
                    self.logger.info("  ✅ SystemDataProvider functional")
                else:
                    self.logger.warning("  ⚠️ SystemDataProvider returned empty data")
            except Exception as e:
                self.logger.error(f"  ❌ SystemDataProvider test failed: {e}")
                self.results['issues'].append({
                    'type': 'data_provider_error',
                    'description': f"SystemDataProvider test failed: {e}",
                    'severity': 'medium'
                })
        
        except Exception as e:
            self.logger.error(f"  ❌ Database testing failed: {e}")
            self.results['issues'].append({
                'type': 'database_test_error',
                'description': f"Database testing failed: {e}",
                'severity': 'high'
            })
        
        self.results['diagnostics']['database_connectivity'] = db_status
    
    def test_filesystem_access(self):
        """Test file system access and permissions"""
        self.logger.info("📁 Testing filesystem access...")
        
        fs_status = {
            'project_root_accessible': False,
            'dashboard_directory_accessible': False,
            'write_permissions': False,
            'read_permissions': False
        }
        
        try:
            # Test project root access
            if project_root.exists() and project_root.is_dir():
                fs_status['project_root_accessible'] = True
                self.logger.info(f"  ✅ Project root accessible: {project_root}")
            else:
                self.logger.error(f"  ❌ Project root not accessible: {project_root}")
                self.results['issues'].append({
                    'type': 'filesystem_error',
                    'description': f"Project root not accessible: {project_root}",
                    'severity': 'critical'
                })
            
            # Test dashboard directory
            dashboard_dir = project_root / 'dashboard'
            if dashboard_dir.exists() and dashboard_dir.is_dir():
                fs_status['dashboard_directory_accessible'] = True
                self.logger.info(f"  ✅ Dashboard directory accessible: {dashboard_dir}")
            else:
                self.logger.error(f"  ❌ Dashboard directory not accessible: {dashboard_dir}")
                self.results['issues'].append({
                    'type': 'filesystem_error',
                    'description': f"Dashboard directory not accessible: {dashboard_dir}",
                    'severity': 'high'
                })
            
            # Test write permissions
            test_file = project_root / 'dashboard' / 'temp_test_file.txt'
            try:
                test_file.write_text('test')
                test_file.unlink()  # Delete the test file
                fs_status['write_permissions'] = True
                self.logger.info("  ✅ Write permissions available")
            except Exception as e:
                self.logger.error(f"  ❌ Write permissions failed: {e}")
                self.results['issues'].append({
                    'type': 'permission_error',
                    'description': f"Write permissions failed: {e}",
                    'severity': 'medium'
                })
            
            # Test read permissions on key files
            key_files = [
                'dashboard/main.py',
                'dashboard/components/cognitive_insights.py',
                'dashboard/data/cognitive_data_provider.py'
            ]
            
            readable_files = 0
            for file_path in key_files:
                full_path = project_root / file_path
                try:
                    content = full_path.read_text()
                    if content:
                        readable_files += 1
                except Exception as e:
                    self.logger.error(f"  ❌ Cannot read {file_path}: {e}")
                    self.results['issues'].append({
                        'type': 'file_read_error',
                        'file': file_path,
                        'description': f"Cannot read {file_path}: {e}",
                        'severity': 'medium'
                    })
            
            if readable_files == len(key_files):
                fs_status['read_permissions'] = True
                self.logger.info("  ✅ Read permissions for key files available")
            else:
                self.logger.warning(f"  ⚠️ Only {readable_files}/{len(key_files)} key files readable")
        
        except Exception as e:
            self.logger.error(f"  ❌ Filesystem testing failed: {e}")
            self.results['issues'].append({
                'type': 'filesystem_test_error',
                'description': f"Filesystem testing failed: {e}",
                'severity': 'high'
            })
        
        self.results['diagnostics']['filesystem_access'] = fs_status
    
    def test_cognitive_system(self):
        """Test cognitive system connectivity"""
        self.logger.info("🧠 Testing cognitive system...")
        
        cognitive_status = {
            'imports_successful': False,
            'system_available': False,
            'gcp_client_functional': False,
            'data_provider_functional': False
        }
        
        try:
            # Test cognitive system imports
            try:
                from dashboard.data.cognitive_data_provider import CognitiveDataProvider
                cognitive_status['imports_successful'] = True
                self.logger.info("  ✅ Cognitive system imports successful")
            except ImportError as e:
                self.logger.error(f"  ❌ Cognitive system imports failed: {e}")
                self.results['issues'].append({
                    'type': 'cognitive_import_error',
                    'description': f"Cognitive system imports failed: {e}",
                    'severity': 'high'
                })
                return
            
            # Test cognitive data provider
            try:
                provider = CognitiveDataProvider()
                if hasattr(provider, 'cognitive_system') and provider.cognitive_system:
                    cognitive_status['system_available'] = True
                    self.logger.info("  ✅ Cognitive system available")
                    
                    # Test basic functionality
                    summary = provider.get_cognitive_summary()
                    if summary:
                        cognitive_status['data_provider_functional'] = True
                        self.logger.info("  ✅ Cognitive data provider functional")
                    else:
                        self.logger.warning("  ⚠️ Cognitive data provider returned empty summary")
                else:
                    self.logger.warning("  ⚠️ Cognitive system not available, using fallback mode")
                    cognitive_status['system_available'] = False
            except Exception as e:
                self.logger.error(f"  ❌ Cognitive system test failed: {e}")
                self.results['issues'].append({
                    'type': 'cognitive_system_error',
                    'description': f"Cognitive system test failed: {e}",
                    'severity': 'medium'
                })
        
        except Exception as e:
            self.logger.error(f"  ❌ Cognitive system testing failed: {e}")
            self.results['issues'].append({
                'type': 'cognitive_test_error',
                'description': f"Cognitive system testing failed: {e}",
                'severity': 'high'
            })
        
        self.results['diagnostics']['cognitive_system'] = cognitive_status
    
    def generate_recommendations(self):
        """Generate recommendations based on diagnostic results"""
        self.logger.info("💡 Generating recommendations...")
        
        recommendations = []
        
        # High priority issues
        critical_issues = [issue for issue in self.results['issues'] if issue['severity'] == 'critical']
        high_issues = [issue for issue in self.results['issues'] if issue['severity'] == 'high']
        
        if critical_issues:
            recommendations.append({
                'priority': 'critical',
                'title': 'Critical Issues Detected',
                'description': 'Fix critical issues immediately to restore functionality',
                'actions': [issue['description'] for issue in critical_issues]
            })
        
        if high_issues:
            recommendations.append({
                'priority': 'high',
                'title': 'High Priority Issues',
                'description': 'Address these issues to improve system reliability',
                'actions': [issue['description'] for issue in high_issues]
            })
        
        # Specific recommendations
        if not os.getenv('GCP_PROJECT_ID'):
            recommendations.append({
                'priority': 'high',
                'title': 'Set Up GCP Project ID',
                'description': 'Configure GCP_PROJECT_ID environment variable',
                'actions': [
                    'Set GCP_PROJECT_ID environment variable',
                    'Ensure GCP service account has proper permissions',
                    'Verify GCP authentication is working'
                ]
            })
        
        if not os.getenv('OPENAI_API_KEY'):
            recommendations.append({
                'priority': 'high',
                'title': 'Configure OpenAI API Key',
                'description': 'Set up OpenAI API key for AI functionality',
                'actions': [
                    'Set OPENAI_API_KEY environment variable',
                    'Or configure OpenAI key in GCP Secret Manager',
                    'Verify API key has proper permissions'
                ]
            })
        
        # Performance recommendations
        if len(self.results['issues']) > 5:
            recommendations.append({
                'priority': 'medium',
                'title': 'Multiple Issues Detected',
                'description': 'Consider systematic troubleshooting approach',
                'actions': [
                    'Review all environment variables',
                    'Check network connectivity',
                    'Verify all dependencies are installed',
                    'Review log files for additional context'
                ]
            })
        
        self.results['recommendations'] = recommendations
    
    def determine_status(self):
        """Determine overall system status"""
        critical_count = len([i for i in self.results['issues'] if i['severity'] == 'critical'])
        high_count = len([i for i in self.results['issues'] if i['severity'] == 'high'])
        medium_count = len([i for i in self.results['issues'] if i['severity'] == 'medium'])
        
        if critical_count > 0:
            self.results['status'] = 'critical'
        elif high_count > 2:
            self.results['status'] = 'degraded'
        elif high_count > 0 or medium_count > 3:
            self.results['status'] = 'warning'
        else:
            self.results['status'] = 'healthy'
        
        self.logger.info(f"📊 Overall status: {self.results['status'].upper()}")
        self.logger.info(f"📊 Issues found: {critical_count} critical, {high_count} high, {medium_count} medium")
    
    def save_results(self, filename: str = None) -> str:
        """Save diagnostic results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"connection_diagnostics_{timestamp}.json"
        
        results_path = project_root / 'dashboard' / filename
        
        try:
            with open(results_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            self.logger.info(f"📝 Results saved to: {results_path}")
            return str(results_path)
        except Exception as e:
            self.logger.error(f"❌ Failed to save results: {e}")
            return None
    
    def print_summary(self):
        """Print a summary of diagnostic results"""
        print("\n" + "="*60)
        print("🔍 CONNECTION DIAGNOSTICS SUMMARY")
        print("="*60)
        
        print(f"📅 Timestamp: {self.results['timestamp']}")
        print(f"📊 Overall Status: {self.results['status'].upper()}")
        
        if self.results['issues']:
            print(f"\n⚠️ Issues Found ({len(self.results['issues'])}):")
            for i, issue in enumerate(self.results['issues'], 1):
                severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
                emoji = severity_emoji.get(issue['severity'], '⚪')
                print(f"  {i}. {emoji} [{issue['severity'].upper()}] {issue['description']}")
        
        if self.results['recommendations']:
            print(f"\n💡 Recommendations ({len(self.results['recommendations'])}):")
            for i, rec in enumerate(self.results['recommendations'], 1):
                priority_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
                emoji = priority_emoji.get(rec['priority'], '⚪')
                print(f"  {i}. {emoji} {rec['title']}: {rec['description']}")
        
        print("\n" + "="*60)


def main():
    """Main function to run diagnostics"""
    print("🚀 Starting Connection Diagnostics...")
    
    diagnostics = ConnectionDiagnostics()
    results = diagnostics.run_full_diagnostics()
    
    # Print summary
    diagnostics.print_summary()
    
    # Save results
    results_file = diagnostics.save_results()
    if results_file:
        print(f"\n📁 Detailed results saved to: {results_file}")
    
    # Return appropriate exit code
    if results['status'] in ['critical', 'degraded']:
        return 1
    else:
        return 0


if __name__ == "__main__":
    exit(main())
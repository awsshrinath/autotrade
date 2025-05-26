"""
Configuration Validation and Testing Module
Provides comprehensive validation for TRON trading configurations
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import asdict
from config.config_manager import ConfigManager, TradingConfig


class ConfigValidator:
    """Validates trading configuration for safety and consistency"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules"""
        return {
            "capital": {
                "default_capital": {"min": 1000, "max": 100000000, "type": "float"},
                "max_daily_loss": {"min": 100, "max": 1000000, "type": "float"},
                "max_daily_loss_pct": {"min": 0.1, "max": 20.0, "type": "float"},
                "min_trade_value": {"min": 100, "max": 100000, "type": "float"}
            },
            "position_limits": {
                "stock_position_limit": {"min": 0.01, "max": 0.5, "type": "float"},
                "option_position_limit": {"min": 0.005, "max": 0.3, "type": "float"},
                "future_position_limit": {"min": 0.01, "max": 0.8, "type": "float"}
            },
            "risk": {
                "margin_utilization_limit": {"min": 0.1, "max": 0.95, "type": "float"},
                "max_volatility_threshold": {"min": 0.01, "max": 0.2, "type": "float"}
            },
            "api": {
                "api_rate_limit": {"min": 1, "max": 10, "type": "int"},
                "api_timeout": {"min": 1, "max": 60, "type": "int"}
            },
            "monitoring": {
                "monitoring_interval": {"min": 10, "max": 3600, "type": "int"},
                "backup_frequency": {"min": 60, "max": 86400, "type": "int"}
            }
        }
    
    def validate_config(self, config: TradingConfig) -> Dict[str, Any]:
        """Comprehensive validation of trading configuration"""
        issues = []
        warnings = []
        critical_issues = []
        
        # Convert config to dict for easier validation
        config_dict = asdict(config)
        
        # Validate each category
        for category, rules in self.validation_rules.items():
            category_issues = self._validate_category(config_dict, category, rules)
            issues.extend(category_issues)
        
        # Business logic validations
        business_issues, business_warnings = self._validate_business_logic(config)
        issues.extend(business_issues)
        warnings.extend(business_warnings)
        
        # Environment-specific validations
        env_issues, env_warnings = self._validate_environment_specific(config)
        issues.extend(env_issues)
        warnings.extend(env_warnings)
        
        # Critical validations
        critical_issues = self._validate_critical_settings(config)
        
        return {
            "valid": len(issues) == 0 and len(critical_issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "critical_issues": critical_issues,
            "environment": config.environment,
            "paper_trade": config.paper_trade,
            "total_issues": len(issues) + len(critical_issues),
            "recommendations": self._generate_recommendations(config, issues, warnings)
        }
    
    def _validate_category(self, config_dict: Dict, category: str, rules: Dict) -> List[str]:
        """Validate a specific category of configuration"""
        issues = []
        
        for field, rule in rules.items():
            if field in config_dict:
                value = config_dict[field]
                
                # Type validation
                expected_type = rule.get("type", "float")
                if expected_type == "float" and not isinstance(value, (int, float)):
                    issues.append(f"{field}: Expected float, got {type(value).__name__}")
                elif expected_type == "int" and not isinstance(value, int):
                    issues.append(f"{field}: Expected int, got {type(value).__name__}")
                
                # Range validation
                if isinstance(value, (int, float)):
                    min_val = rule.get("min")
                    max_val = rule.get("max")
                    
                    if min_val is not None and value < min_val:
                        issues.append(f"{field}: Value {value} below minimum {min_val}")
                    
                    if max_val is not None and value > max_val:
                        issues.append(f"{field}: Value {value} above maximum {max_val}")
        
        return issues
    
    def _validate_business_logic(self, config: TradingConfig) -> Tuple[List[str], List[str]]:
        """Validate business logic and relationships between settings"""
        issues = []
        warnings = []
        
        # Capital consistency
        if config.max_daily_loss > config.default_capital:
            issues.append("max_daily_loss cannot exceed default_capital")
        
        if config.max_daily_loss > config.default_capital * 0.5:
            warnings.append("max_daily_loss is more than 50% of capital - very risky")
        
        # Position limit consistency
        total_position_limit = (config.stock_position_limit + 
                               config.option_position_limit + 
                               config.future_position_limit)
        if total_position_limit > 1.0:
            warnings.append(f"Total position limits ({total_position_limit:.1%}) exceed 100%")
        
        # Risk consistency
        if config.margin_utilization_limit > 0.9:
            warnings.append("Margin utilization limit above 90% is very risky")
        
        # Environment consistency
        if config.environment == "production" and config.paper_trade:
            warnings.append("Running production environment with paper trading")
        
        if config.environment != "production" and not config.paper_trade:
            warnings.append("Running non-production environment with live trading")
        
        return issues, warnings
    
    def _validate_environment_specific(self, config: TradingConfig) -> Tuple[List[str], List[str]]:
        """Validate environment-specific requirements"""
        issues = []
        warnings = []
        
        if config.environment == "production":
            # Production-specific validations
            if config.default_capital < 100000:
                warnings.append("Production capital below ₹1 lakh may limit trading opportunities")
            
            if config.max_daily_loss_pct > 5.0:
                warnings.append("Production daily loss limit above 5% is very aggressive")
            
            if config.monitoring_interval > 60:
                warnings.append("Production monitoring interval above 1 minute may miss issues")
            
        elif config.environment == "development":
            # Development-specific validations
            if config.default_capital > 500000:
                warnings.append("Development capital above ₹5 lakh is unnecessary")
            
            if not config.paper_trade:
                issues.append("Development environment should use paper trading")
        
        return issues, warnings
    
    def _validate_critical_settings(self, config: TradingConfig) -> List[str]:
        """Validate critical settings that could cause system failure"""
        critical_issues = []
        
        # Zero or negative values that would break the system
        if config.default_capital <= 0:
            critical_issues.append("default_capital must be positive")
        
        if config.max_daily_loss <= 0:
            critical_issues.append("max_daily_loss must be positive")
        
        # Extreme values that could cause system instability
        if config.api_rate_limit <= 0:
            critical_issues.append("api_rate_limit must be positive")
        
        if config.monitoring_interval <= 0:
            critical_issues.append("monitoring_interval must be positive")
        
        # Position limits that could prevent trading
        if config.stock_position_limit <= 0:
            critical_issues.append("stock_position_limit must be positive")
        
        return critical_issues
    
    def _generate_recommendations(self, config: TradingConfig, issues: List[str], warnings: List[str]) -> List[str]:
        """Generate recommendations based on configuration"""
        recommendations = []
        
        # Environment-based recommendations
        if config.environment == "production":
            recommendations.append("Ensure all API credentials are properly configured")
            recommendations.append("Set up monitoring and alerting systems")
            recommendations.append("Test with paper trading first")
        
        # Capital-based recommendations
        if config.default_capital < 50000:
            recommendations.append("Consider increasing capital for better diversification")
        
        # Risk-based recommendations
        if config.max_daily_loss_pct > 3.0:
            recommendations.append("Consider reducing daily loss limit for better capital preservation")
        
        if config.margin_utilization_limit > 0.8:
            recommendations.append("High margin utilization increases risk - consider reducing")
        
        return recommendations
    
    def validate_config_file(self, config_path: str) -> Dict[str, Any]:
        """Validate configuration directly from file"""
        try:
            config_manager = ConfigManager(config_dir=Path(config_path).parent)
            return self.validate_config(config_manager.config)
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Failed to load configuration: {str(e)}"],
                "warnings": [],
                "critical_issues": ["Configuration file could not be loaded"],
                "total_issues": 1
            }
    
    def compare_configs(self, config1: TradingConfig, config2: TradingConfig) -> Dict[str, Any]:
        """Compare two configurations and highlight differences"""
        dict1 = asdict(config1)
        dict2 = asdict(config2)
        
        differences = []
        for key in dict1.keys():
            if key in dict2:
                if dict1[key] != dict2[key]:
                    differences.append({
                        "field": key,
                        "config1_value": dict1[key],
                        "config2_value": dict2[key]
                    })
        
        return {
            "identical": len(differences) == 0,
            "differences": differences,
            "config1_env": config1.environment,
            "config2_env": config2.environment
        }


def validate_current_config() -> Dict[str, Any]:
    """Validate the currently loaded configuration"""
    from config.config_manager import get_trading_config
    
    validator = ConfigValidator()
    config = get_trading_config()
    return validator.validate_config(config)


def run_config_tests() -> Dict[str, Any]:
    """Run comprehensive configuration tests"""
    validator = ConfigValidator()
    results = {}
    
    # Test each environment configuration
    for environment in ["development", "staging", "production"]:
        try:
            config_manager = ConfigManager(environment=environment)
            validation = validator.validate_config(config_manager.config)
            results[environment] = validation
        except Exception as e:
            results[environment] = {
                "valid": False,
                "error": str(e)
            }
    
    return results


if __name__ == "__main__":
    # Run validation on current configuration
    print("🔍 Validating Current Configuration...")
    validation = validate_current_config()
    
    print(f"Valid: {validation['valid']}")
    if validation['issues']:
        print(f"Issues: {validation['issues']}")
    if validation['warnings']:
        print(f"Warnings: {validation['warnings']}")
    if validation['critical_issues']:
        print(f"Critical Issues: {validation['critical_issues']}")
    
    print("\n🧪 Running All Environment Tests...")
    test_results = run_config_tests()
    
    for env, result in test_results.items():
        print(f"{env}: {'✅ Valid' if result.get('valid', False) else '❌ Invalid'}")
        if 'error' in result:
            print(f"  Error: {result['error']}")
        elif result.get('total_issues', 0) > 0:
            print(f"  Issues: {result['total_issues']}")
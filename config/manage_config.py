#!/usr/bin/env python3
"""
TRON Configuration Management Script
Provides command-line interface for managing configurations
"""

import argparse
import json
import yaml
from pathlib import Path
from config.config_manager import ConfigManager, init_config
from config.config_validator import (
    ConfigValidator,
    validate_current_config,
    run_config_tests,
)


def show_current_config():
    """Display current configuration"""
    config_manager = ConfigManager()
    config = config_manager.config

    print("📊 Current TRON Configuration")
    print("=" * 50)
    print(f"Environment: {config.environment}")
    print(f"Paper Trade: {config.paper_trade}")
    print(f"Default Capital: ₹{config.default_capital:,}")
    print(f"Max Daily Loss: ₹{config.max_daily_loss:,} ({config.max_daily_loss_pct}%)")
    print(f"Log Level: {config.log_level}")
    print()

    print("Position Limits:")
    print(f"  Stock: {config.stock_position_limit:.1%}")
    print(f"  Option: {config.option_position_limit:.1%}")
    print(f"  Future: {config.future_position_limit:.1%}")
    print()

    print("Risk Settings:")
    print(f"  Margin Limit: {config.margin_utilization_limit:.1%}")
    print(f"  Volatility Threshold: {config.max_volatility_threshold:.1%}")
    print(f"  Min Trade Value: ₹{config.min_trade_value:,}")
    print()

    print("API Settings:")
    print(f"  Rate Limit: {config.api_rate_limit} req/sec")
    print(f"  Timeout: {config.api_timeout} seconds")
    print()

    print("Monitoring:")
    print(f"  Interval: {config.monitoring_interval} seconds")
    print(f"  Auto Square Off: {config.auto_square_off_time}")


def validate_config(environment=None):
    """Validate configuration"""
    print("🔍 Validating Configuration...")

    if environment:
        config_manager = ConfigManager(environment=environment)
        validator = ConfigValidator()
        validation = validator.validate_config(config_manager.config)
    else:
        validation = validate_current_config()

    print(f"Environment: {validation['environment']}")
    print(f"Paper Trade: {validation['paper_trade']}")
    print(f"Valid: {'✅ Yes' if validation['valid'] else '❌ No'}")

    if validation["critical_issues"]:
        print("\n🚨 Critical Issues:")
        for issue in validation["critical_issues"]:
            print(f"  - {issue}")

    if validation["issues"]:
        print("\n⚠️  Issues:")
        for issue in validation["issues"]:
            print(f"  - {issue}")

    if validation["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")

    if validation.get("recommendations"):
        print("\n💡 Recommendations:")
        for rec in validation["recommendations"]:
            print(f"  - {rec}")


def test_all_environments():
    """Test all environment configurations"""
    print("🧪 Testing All Environment Configurations...")
    print("=" * 50)

    results = run_config_tests()

    for env, result in results.items():
        print(f"\n{env.upper()} Environment:")
        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
        else:
            print(f"  Status: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
            if result.get("total_issues", 0) > 0:
                print(f"  Total Issues: {result['total_issues']}")
                if result.get("critical_issues"):
                    print(f"  Critical: {len(result['critical_issues'])}")
                if result.get("issues"):
                    print(f"  Issues: {len(result['issues'])}")
                if result.get("warnings"):
                    print(f"  Warnings: {len(result['warnings'])}")


def switch_environment(environment):
    """Switch to a different environment"""
    valid_envs = ["development", "staging", "production"]

    if environment not in valid_envs:
        print(f"❌ Invalid environment. Choose from: {valid_envs}")
        return

    print(f"🔄 Switching to {environment} environment...")

    try:
        # Initialize with new environment
        config_manager = init_config(environment=environment)

        print(f"✅ Successfully switched to {environment}")
        print(f"Paper Trade: {config_manager.config.paper_trade}")
        print(f"Capital: ₹{config_manager.config.default_capital:,}")
        print(f"Max Loss: ₹{config_manager.config.max_daily_loss:,}")

        # Validate new configuration
        print("\nValidating new configuration...")
        validator = ConfigValidator()
        validation = validator.validate_config(config_manager.config)

        if not validation["valid"]:
            print("⚠️  Warning: New configuration has issues!")
            if validation["critical_issues"]:
                print("Critical issues found - review before using!")
        else:
            print("✅ Configuration is valid")

    except Exception as e:
        print(f"❌ Failed to switch environment: {e}")


def create_local_config():
    """Create a local configuration file"""
    local_config_path = Path("config/local.yaml")
    example_path = Path("config/local.yaml.example")

    if local_config_path.exists():
        response = input("local.yaml already exists. Overwrite? (y/N): ")
        if response.lower() != "y":
            print("❌ Cancelled")
            return

    if example_path.exists():
        # Copy from example
        with open(example_path, "r") as f:
            content = f.read()

        with open(local_config_path, "w") as f:
            f.write(content)

        print(f"✅ Created {local_config_path} from example")
        print("Edit this file to customize your local settings")
    else:
        # Create basic local config
        local_config = {
            "paper_trade": True,
            "default_capital": 50000,
            "max_daily_loss": 500,
            "log_level": "DEBUG",
        }

        with open(local_config_path, "w") as f:
            yaml.dump(local_config, f, default_flow_style=False, indent=2)

        print(f"✅ Created basic {local_config_path}")


def export_config(environment, format_type="yaml"):
    """Export configuration to file"""
    try:
        config_manager = ConfigManager(environment=environment)
        config_dict = {
            "environment": config_manager.config.environment,
            "paper_trade": config_manager.config.paper_trade,
            "default_capital": config_manager.config.default_capital,
            "max_daily_loss": config_manager.config.max_daily_loss,
            "max_daily_loss_pct": config_manager.config.max_daily_loss_pct,
            "stock_position_limit": config_manager.config.stock_position_limit,
            "option_position_limit": config_manager.config.option_position_limit,
            "future_position_limit": config_manager.config.future_position_limit,
            "margin_utilization_limit": config_manager.config.margin_utilization_limit,
            "max_volatility_threshold": config_manager.config.max_volatility_threshold,
            "min_trade_value": config_manager.config.min_trade_value,
            "api_rate_limit": config_manager.config.api_rate_limit,
            "api_timeout": config_manager.config.api_timeout,
            "monitoring_interval": config_manager.config.monitoring_interval,
            "backup_frequency": config_manager.config.backup_frequency,
            "auto_square_off_time": config_manager.config.auto_square_off_time,
            "log_level": config_manager.config.log_level,
            "scalp_config": config_manager.config.scalp_config,
        }

        filename = f"exported_{environment}_config.{format_type}"

        if format_type == "json":
            with open(filename, "w") as f:
                json.dump(config_dict, f, indent=2)
        else:  # yaml
            with open(filename, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)

        print(f"✅ Configuration exported to {filename}")

    except Exception as e:
        print(f"❌ Export failed: {e}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="TRON Configuration Management")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Show current config
    subparsers.add_parser("show", help="Show current configuration")

    # Validate config
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument(
        "--env",
        choices=["development", "staging", "production"],
        help="Environment to validate",
    )

    # Test all environments
    subparsers.add_parser("test", help="Test all environment configurations")

    # Switch environment
    switch_parser = subparsers.add_parser("switch", help="Switch environment")
    switch_parser.add_argument(
        "environment",
        choices=["development", "staging", "production"],
        help="Environment to switch to",
    )

    # Create local config
    subparsers.add_parser("init-local", help="Create local configuration file")

    # Export config
    export_parser = subparsers.add_parser("export", help="Export configuration")
    export_parser.add_argument(
        "environment",
        choices=["development", "staging", "production"],
        help="Environment to export",
    )
    export_parser.add_argument(
        "--format", choices=["yaml", "json"], default="yaml", help="Export format"
    )

    args = parser.parse_args()

    if args.command == "show":
        show_current_config()
    elif args.command == "validate":
        validate_config(args.env)
    elif args.command == "test":
        test_all_environments()
    elif args.command == "switch":
        switch_environment(args.environment)
    elif args.command == "init-local":
        create_local_config()
    elif args.command == "export":
        export_config(args.environment, args.format)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

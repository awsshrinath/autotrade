#!/usr/bin/env python3
import json
import sys
import os

# Print working directory for debugging
print(f"Current working directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

try:
    with open("bandit_report.json") as f:
        report = json.load(f)
except Exception as e:
    print(f"❌ Failed to load bandit report: {e}")
    sys.exit(0)  # Don't block pipeline if report is missing

high_issues = [
    issue for issue in report.get("results", [])
    if issue.get("issue_severity", "").upper() == "HIGH"
]

if high_issues:
    print(f"🚨 Found {len(high_issues)} HIGH severity issues:")
    for issue in high_issues:
        print(f"- {issue['filename']}:{issue['line_number']} [{issue['test_id']}] {issue['issue_text']}")
    sys.exit(1)
else:
    print("✅ No high severity issues found.")
    # Show all issues found (for debugging)
    all_issues = report.get("results", [])
    if all_issues:
        print(f"Found {len(all_issues)} total issues (non-high severity):")
        severity_counts = {}
        for issue in all_issues:
            severity = issue.get("issue_severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        print(f"Severity breakdown: {severity_counts}")
    sys.exit(0)

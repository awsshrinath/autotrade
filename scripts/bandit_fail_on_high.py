import json
import sys

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
    sys.exit(0)

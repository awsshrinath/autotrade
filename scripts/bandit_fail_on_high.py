import json
import sys

with open("bandit_report.json") as f:
    report = json.load(f)

high_issues = [
    issue for issue in report.get("results", [])
    if issue.get("issue_severity", "").upper() == "HIGH"
]

if high_issues:
    print(f"❌ Found {len(high_issues)} HIGH severity issues:")
    for issue in high_issues:
        print(f"{issue['filename']}:{issue['line_number']} - {issue['issue_text']}")
    sys.exit(1)
else:
    print("✅ No HIGH severity issues found.")
    sys.exit(0)

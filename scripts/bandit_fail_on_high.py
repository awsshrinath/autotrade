import json

with open("bandit_report.json") as f:
    report = json.load(f)

high_issues = [
    issue for issue in report.get("results", [])
    if issue.get("issue_severity", "") == "HIGH"
]

if high_issues:
    print(f"❌ Found {len(high_issues)} HIGH severity Bandit issues:")
    for issue in high_issues:
        print(f"{issue['filename']}:{issue['line_number']} - {issue['issue_text']}")
    exit(1)
else:
    print("✅ No HIGH severity Bandit issues found.")

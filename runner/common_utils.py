# runner/utils.py

import os


def create_daily_folders(today_date):
    log_dir = os.path.join("logs", today_date)
    report_dir = os.path.join("reports", today_date)

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

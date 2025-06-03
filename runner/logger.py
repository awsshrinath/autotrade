# runner/logger.py

import datetime
import os


class Logger:
    def __init__(self, today_date):
        self.today_date = today_date
        self.log_folder = f"logs/{today_date}"
        self.log_file_path = f"{self.log_folder}/runner_log.txt"

        # Ensure the log folder exists
        os.makedirs(self.log_folder, exist_ok=True)

    def log_event(self, event_text):
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {event_text}\n")

        print(
            f"{timestamp} {event_text}"
        )  # Also print to console for real-time monitoring

    def error(self, message):
        """Log error message - compatible with standard logging"""
        self.log_event(f"❌ [ERROR] {message}")

    def warning(self, message):
        """Log warning message - compatible with standard logging"""
        self.log_event(f"⚠️ [WARNING] {message}")

    def info(self, message):
        """Log info message - compatible with standard logging"""
        self.log_event(f"ℹ️ [INFO] {message}")

    def critical(self, message):
        """Log critical message - compatible with standard logging"""
        self.log_event(f"🚨 [CRITICAL] {message}")

    def debug(self, message):
        """Log debug message - compatible with standard logging"""
        self.log_event(f"🔍 [DEBUG] {message}")

import sys
sys.path.insert(0, ".")

print("🧪 Running Full Bot Runner Integration Tests...\n")

def safe_run(label, import_path):
    try:
        __import__(import_path)
        print(f"✅ {label} passed.")
    except Exception as e:
        print(f"❌ {label} failed: {e}")

# Individual runner tests
safe_run("stock_runner.py", "stock_trading.stock_runner")
safe_run("options_runner.py", "options_trading.options_runner")
safe_run("futures_runner.py", "futures_trading.futures_runner")
safe_run("main_runner.py", "runner.main_runner")
safe_run("main.py", "main")

print("\n🎯 Runner Test Complete.")

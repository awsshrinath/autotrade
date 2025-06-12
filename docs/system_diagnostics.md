
# ðŸ§  Full System Diagnostic: Autotrade Bot (Cursor Fix Mode)

## ðŸŽ¯ Target Issues
1. **Paper trades are not being executed**
2. **Logs are not reaching Google Cloud Storage (GCS)**

---

## === FILE: `main.py` ===  
**Role**: Entrypoint for orchestrating the trading system

**Key Functions**:
- `main()`: initializes and launches cognitive engine and strategy runners

**[ISSUE: Paper Trade Not Triggered]**  
- **Diagnosis**: No reference to `PAPER_TRADE` flag in `main.py`. No call to `simulate_trade()` or `paper_trade_order()`.
- **Root Cause**: `main.py` appears oriented for full production execution only. Paper trading logic appears siloed in `standalone_paper_trader.py`.
- **Dependencies to Check**: `config.PAPER_TRADE` or equivalent is not loaded or evaluated here.

---

## === FILE: `standalone_paper_trader.py` ===  
**Role**: Separate runner script designed specifically for paper trading simulation

**Key Functions**:
- `simulate_trade()`: core function for placing trades in paper mode
- `main()`: orchestrates mock environment and strategy run

**[ISSUE: Paper Trade Logic Isolated and Not Wired Into Main System]**
- **Diagnosis**: Paper trading code exists but is disconnected from production path.
- **Root Cause**: `standalone_paper_trader.py` is never called from `main.py`, `run_fixed_main.py`, or central orchestrator.
- **Dependencies to Check**:
  - Environment var or config toggle for `PAPER_TRADE`
  - Whether GKE pods or `main_runner.py` ever trigger this file

---

## === FILE: `runner/config.py` ===  
**Role**: System configuration (e.g., flags, toggles, environment variables)

**Key Items**:
- Looks for `PAPER_TRADE` using `os.getenv("PAPER_TRADE", "True") == "True"`

**[ISSUE: Flag Not Propagated Across System]**
- **Diagnosis**: `PAPER_TRADE` is correctly read, but is not passed to most strategy execution paths.
- **Root Cause**: Strategy runners (e.g., `stock_runner.py`, `futures_runner.py`) ignore this flag or have hardcoded behavior.
- **Fix Target**: All runners and `trade_manager` should obey this config flag consistently.

---

## === FILE: `runner/trade_manager.py` ===  
**Role**: Core execution module for trades (entry, exit, paper/live control)

**Key Functions**:
- `execute_trade()`
- `simulate_trade()`

**[ISSUE: simulate_trade() Defined But Not Used]**
- **Diagnosis**: The function is defined but not called in production flow.
- **Root Cause**: Execution path invokes only `execute_trade()` without checking the mode.
- **Dependencies to Check**:
  - Is `PAPER_TRADE` passed to `execute_trade()` or checked inside it?
  - Do strategies call correct version?

---

## === FILE: `runner/enhanced_logger.py` ===  
**Role**: Advanced logging system (including GCS targets)

**Key Functions**:
- `upload_to_gcs(log_file_path)`
- `log_event(event_type, message)`

**[ISSUE: GCS Log Upload Not Triggered]**
- **Diagnosis**: While GCS upload logic exists, actual calls to `upload_to_gcs()` are missing in runners.
- **Root Cause**: Logging flow remains local or in-memory.
- **Dependencies to Check**:
  - `GOOGLE_APPLICATION_CREDENTIALS` presence
  - GCS bucket name or path config

---

## === FILE: `runner/capital_manager.py` ===  
**Role**: Manages capital allocation per trade

**Key Functions**:
- `get_allocation(strategy, capital, total_strategies)`
- `record_profit_loss()`

**[Issue: Paper Trade Impact Not Logged]**
- **Diagnosis**: Itâ€™s unclear if simulated trades are fed back into capital tracking.
- **Root Cause**: Live trades update capital; simulated may not.
- **Fix Suggestion**: Ensure `record_profit_loss()` handles both paper/live modes.

---

## === FILE: `*_runner.py` (Stock, Options, Futures) ===  
**Role**: Per-asset class trade execution orchestrators

**[ISSUE: Execution Ignores PAPER_TRADE Flag]**
- **Diagnosis**: Hardcoded or defaults to live logic via `execute_trade()` instead of checking mode.
- **Root Cause**: These files never conditionally invoke `simulate_trade()`.

---

## === FILE: `tools/gcs_logger.py` ===  
**Role**: GCS log uploader utility (if used)

**[ISSUE: Likely Not Imported Anywhere]**
- **Diagnosis**: GCS utility code may exist but is unused.
- **Root Cause**: Missing import and integration into log dispatching logic.

---

## âœ… CURSOR TODOs (For Fix Phase)

- [ ] Ensure PAPER_TRADE flag is passed from config to trade_manager and all strategy runners
- [ ] In trade_manager.py, switch between simulate_trade() and execute_trade() based on flag
- [ ] In enhanced_logger.py or trade_manager, invoke upload_to_gcs() on trade completion
- [ ] Add debug logging if GCS upload fails (log to console and continue)
- [ ] Confirm GOOGLE_APPLICATION_CREDENTIALS is loaded in pod or VM (and valid)
- [ ] Validate paper trades still affect capital_managerâ€™s tracking functions

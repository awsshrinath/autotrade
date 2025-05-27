# Additional Kubernetes Pod Errors - Fixes Applied

## Summary of Additional Issues and Fixes

### 1. TypeError: access_secret() missing 1 required positional argument: 'project_id'

**Error Locations:** 
- `/app/runner/utils/instrument_utils.py:8`
- `/app/runner/secret_manager_client.py:33`

**Root Cause:** The `access_secret` function requires `project_id` parameter but some calls were missing it

**Fix Applied:**
- Added default value `"autotrade-453303"` to `project_id` parameter in `access_secret` function
- This maintains backward compatibility while fixing the missing parameter issue

**Files Modified:**
- `runner/secret_manager_client.py` - Added default project_id parameter

### 2. TypeError: get_kite_client() got an unexpected keyword argument 'project_id'

**Error Location:** `/app/stock_trading/stock_runner.py:39`

**Root Cause:** Some code was calling `get_kite_client()` with `project_id` parameter but the method didn't accept it

**Fix Applied:**
- Added optional `project_id` parameter to `KiteConnectManager.get_kite_client()` method for backward compatibility
- Parameter is accepted but not used since project_id is set during initialization

**Files Modified:**
- `runner/kiteconnect_manager.py` - Added optional project_id parameter

### 3. ModuleNotFoundError: No module named 'runner'

**Error Locations:**
- `/app/futures_trading/futures_runner.py:7`
- `/app/stock_trading/stock_runner.py:7`
- `/app/options_trading/options_runner.py:7`
- `/app/runner/main_runner.py:3`

**Root Cause:** Python path not configured before imports, causing module resolution failures

**Fix Applied:**
- Moved `sys.path.append()` to the very top of each file, before any other imports
- This ensures the project root is in the Python path before attempting to import runner modules

**Files Modified:**
- `futures_trading/futures_runner.py` - Moved path configuration to top
- `stock_trading/stock_runner.py` - Moved path configuration to top
- `options_trading/options_runner.py` - Moved path configuration to top
- `runner/main_runner.py` - Added path configuration

### 4. ModuleNotFoundError: No module named 'runner.utils.strategy_helpers'

**Error Location:** `/app/options_trading/strategies/scalp_strategy.py:1`

**Root Cause:** Missing path configuration in strategy files

**Fix Applied:**
- Added path configuration to strategy files to ensure proper module resolution
- Added `sys.path.append()` with correct relative path for strategy subdirectories

**Files Modified:**
- `options_trading/strategies/scalp_strategy.py` - Added path configuration

### 5. Dependency Version Conflicts

**Error Locations:**
- `ImportError: numpy.core.multiarray failed to import`
- `ImportError: cannot import name 'cached_download' from 'huggingface_hub'`

**Root Cause:** Incompatible dependency versions causing import failures

**Fix Applied:**
- Updated `requirements.txt` with compatible version ranges
- Changed from exact versions to minimum versions with compatibility ranges
- Added explicit pandas version requirement

**Files Modified:**
- `requirements.txt` - Updated dependency versions

### 6. Infrastructure and Permission Issues

**Note:** The following errors are infrastructure/configuration related and cannot be fixed with code changes:

- **Network Plugin Issues:** `cni plugin not initialized` - Kubernetes cluster configuration issue
- **Permission Denied:** `secretmanager.versions.access` - GCP IAM permissions issue  
- **Image Pull Errors:** `ErrImagePull` - Docker registry/image issues
- **Secret Mount Issues:** `secret "rules" not found` - Kubernetes secret configuration
- **Service Account Issues:** `iam.serviceAccounts.getAccessToken` - GCP Workload Identity configuration

These require infrastructure team intervention to resolve.

## Verification Results

All code-related fixes have been verified using the test script `test_all_fixes.py`:

✅ access_secret has default project_id parameter
✅ KiteConnectManager.get_kite_client accepts project_id parameter  
✅ Runner module imports work from trading bot directories
✅ Main runner imports are valid
✅ Options strategy imports work correctly

## Deployment Notes

1. **Clear Cache:** Ensure all Python cache files are cleared in Docker containers
2. **Path Configuration:** All files now have proper sys.path configuration at the top
3. **Dependency Updates:** Updated requirements.txt should be used for new builds
4. **Backward Compatibility:** All fixes maintain backward compatibility
5. **Infrastructure Issues:** Remaining errors require GCP/Kubernetes configuration fixes

## Files Modified Summary

1. `runner/secret_manager_client.py` - Added default project_id parameter
2. `runner/kiteconnect_manager.py` - Added optional project_id parameter
3. `futures_trading/futures_runner.py` - Fixed import path configuration
4. `stock_trading/stock_runner.py` - Fixed import path configuration
5. `options_trading/options_runner.py` - Fixed import path configuration
6. `runner/main_runner.py` - Added import path configuration
7. `options_trading/strategies/scalp_strategy.py` - Added path configuration
8. `requirements.txt` - Updated dependency versions

## Infrastructure Actions Required

The following issues require infrastructure team action:

1. **GCP IAM Permissions:** Grant `secretmanager.versions.access` permission to service account
2. **Workload Identity:** Configure proper IAM bindings for `gpt-runner-sa@autotrade-453303.iam.gserviceaccount.com`
3. **Kubernetes Secrets:** Create missing `rules` secret
4. **Network Configuration:** Fix CNI plugin initialization
5. **Docker Registry:** Resolve image pull issues

These code fixes should resolve all application-level errors, while infrastructure issues need separate resolution. 
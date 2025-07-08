# Test Environment Setup Guide

This guide documents all requirements and setup steps needed to run the ArchDash test suite successfully.

## System Requirements

### Operating System
- Ubuntu 24.04 LTS (Noble Numbat) or compatible Linux distribution
- WSL2 environment supported

### Python Environment
- Python 3.12+
- Virtual environment recommended but not required

## Dependencies Installation

### 1. Python Dependencies
Install all Python packages from requirements.txt:

```bash
# If using system packages (may require --break-system-packages flag)
python3 -m pip install --user --break-system-packages -r requirements.txt

# Additional dependencies that may be missing
python3 -m pip install --user --break-system-packages psutil multiprocess
```

### 2. System Dependencies for Chrome/Selenium
Chrome browser requires specific system libraries:

```bash
sudo apt update
sudo apt install -y libnss3 libnspr4 libasound2t64
```

Note: `libasound2t64` is the correct package name for Ubuntu 24.04 (replaces `libasound2`)

### 3. Chrome Browser Setup
The test suite is configured to automatically use Chrome in headless mode. The setup process includes:

1. **Automatic Chrome Download**: If no system Chrome is found, Chrome will be downloaded automatically by Selenium
2. **Chrome Location Priority**: Tests will check for Chrome in this order:
   - `/usr/bin/google-chrome`
   - `/usr/bin/google-chrome-stable`
   - `/usr/bin/chromium-browser`
   - `/usr/bin/chromium`
   - `/snap/bin/chromium`
   - Downloaded Chrome in user directory

3. **Chrome Configuration**: Headless mode with the following flags:
   - `--headless`
   - `--no-sandbox`
   - `--disable-dev-shm-usage`
   - `--disable-gpu`
   - `--window-size=800,600`

## Running Tests

### Basic Test Execution
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ -v --cov

# Run specific test file
python3 -m pytest tests/test_T425_unlink_icon_display_logic.py -v

# Run with limited failures (stop after 5 failures)
python3 -m pytest tests/ -v --maxfail=5
```

### Parallel Test Execution
```bash
# Run tests in parallel (requires pytest-xdist)
python3 -m pytest tests/ -n auto
```

## Test Categories

### 1. Unit Tests (T101-T199)
- **Purpose**: Core functionality testing
- **Requirements**: Python dependencies only
- **Examples**: Parameter validation, dependency detection, graph operations

### 2. Layout Tests (T201-T299)
- **Purpose**: UI layout and canvas operations
- **Requirements**: Python dependencies only
- **Examples**: Canvas updates, arrow creation, layout management

### 3. Integration Tests (T301-T399)
- **Purpose**: End-to-end functionality testing
- **Requirements**: Python dependencies only
- **Examples**: Example loading, parameter calculations

### 4. Advanced Feature Tests (T401-T499)
- **Purpose**: Complex feature testing
- **Requirements**: Python dependencies only
- **Examples**: Serialization, unlink functionality, layout operations

### 5. Web Interface Tests (T501-T599)
- **Purpose**: Browser-based UI testing
- **Requirements**: Chrome browser + Selenium
- **Examples**: Node operations, parameter editing, web interface interactions

## Troubleshooting

### Chrome Driver Issues
If you encounter "Status code was: 127" errors:

1. **Check Chrome Installation**:
   ```bash
   /home/readm/chrome_install/opt/google/chrome/chrome --version
   ```

2. **Verify System Dependencies**:
   ```bash
   ldd /home/readm/chrome_install/opt/google/chrome/chrome | grep "not found"
   ```
   Should return no missing libraries.

3. **Test Headless Mode**:
   ```bash
   /home/readm/chrome_install/opt/google/chrome/chrome --headless --disable-gpu --no-sandbox --version
   ```

### Common Issues

#### Missing Python Dependencies
```bash
# Error: ModuleNotFoundError: No module named 'psutil'
python3 -m pip install --user --break-system-packages psutil

# Error: ModuleNotFoundError: No module named 'multiprocess'  
python3 -m pip install --user --break-system-packages multiprocess
```

#### Permission Issues
```bash
# If you get permission errors, use --user flag
python3 -m pip install --user --break-system-packages [package_name]
```

#### Flask Server Port Conflicts
Tests automatically handle port allocation for parallel execution. Each test worker uses a different port range (8051+).

## Test Configuration

### Pytest Configuration (pytest.ini)
The project includes pytest configuration for:
- Custom markers
- Test discovery patterns  
- Coverage settings
- Timeout configurations

### Fixture Configuration (conftest.py)
Key fixtures provide:
- **Flask App Server**: Isolated test server instances
- **Chrome Browser**: Headless Chrome with proper configuration
- **Test Cleanup**: Automatic state cleanup between tests
- **Parallel Support**: Worker-specific port allocation

## Performance Notes

- **Selenium Tests**: Take longer due to browser startup (10-30 seconds each)
- **Unit Tests**: Fast execution (< 1 second each)
- **Parallel Execution**: Recommended for large test suites
- **Memory Usage**: Chrome instances require ~100MB RAM each

## Environment Variables

### Testing Mode
```bash
export TESTING=True  # Automatically set by pytest
```

### Logging Configuration
Tests automatically configure logging to reduce noise:
- Werkzeug: WARNING level
- urllib3: WARNING level
- User warnings: Suppressed

## Success Criteria

A properly configured environment should:
1. ✅ Run all unit tests without errors
2. ✅ Successfully start Chrome in headless mode  
3. ✅ Execute Selenium tests without WebDriver errors
4. ✅ Complete test suite with expected pass/fail ratios

## Last Updated
Generated: 2025-07-07
Environment: Ubuntu 24.04 LTS, Python 3.12.3, Chrome 138.0.7204.92
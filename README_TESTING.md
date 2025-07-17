# 🧪 Wolf Goat Pig Testing Guide

This document explains the comprehensive testing setup for the Wolf Goat Pig Monte Carlo simulation, including **Gherkin BDD tests** with **headless Chrome automation**.

## 🎯 What We're Testing

The test suite covers the complete Monte Carlo simulation functionality:

- **User Interface**: Form interactions, navigation, responsive design
- **Simulation Logic**: API endpoints, mathematical accuracy, performance
- **User Workflows**: Complete end-to-end scenarios written in business language
- **Error Handling**: Invalid inputs, network failures, edge cases
- **Cross-browser Compatibility**: Headless Chrome automation

## 🥒 Gherkin & BDD Overview

**Gherkin** is a business-readable language that lets you write tests as natural scenarios:

```gherkin
Scenario: Running a Monte Carlo simulation
  Given I am on the Monte Carlo simulation page
  When I configure Stuart with handicap "10"
  And I configure three computer opponents
  And I set the number of simulations to "25"
  And I click the "Run Monte Carlo Simulation" button
  Then I should see the simulation results
  And Stuart should have a realistic win percentage
```

**Benefits of Gherkin/BDD:**
- ✅ **Business-readable**: Non-technical stakeholders can understand tests
- ✅ **Living documentation**: Tests describe exactly what the system does
- ✅ **Collaboration**: Bridge between business requirements and technical implementation
- ✅ **Regression prevention**: Catch breaking changes in user workflows

## 🏗️ Test Architecture

### **Test Layers**

1. **Feature Tests** (`tests/features/`)
   - Gherkin scenarios describing user stories
   - Business-focused, readable by anyone
   - Cover complete user workflows

2. **Step Definitions** (`tests/step_definitions/`)
   - Python code that implements Gherkin steps
   - Uses Playwright for browser automation
   - Translates business language to technical actions

3. **API Tests** (`tests/test_monte_carlo_api.py`)
   - Direct testing of backend endpoints
   - Fast, isolated, no browser required
   - Validates data structures and business logic

4. **Configuration** (`tests/conftest.py`, `pytest.ini`)
   - Test fixtures and browser setup
   - Server management and cleanup
   - Test reporting and logging

### **Technology Stack**

- **🥒 pytest-bdd**: Connects Gherkin scenarios to Python code
- **🎭 Playwright**: Modern browser automation (better than Selenium)
- **🔬 pytest**: Test framework with powerful fixtures
- **📊 HTML Reports**: Beautiful test reports with screenshots
- **⚡ Parallel Execution**: Run tests faster with multiple browsers

## 🚀 Getting Started

### **1. Install Dependencies**

```bash
# Install all testing dependencies
./scripts/install_test_dependencies.sh
```

This installs:
- Python testing packages (pytest, playwright, etc.)
- Chromium browser for headless testing
- System dependencies for browser automation

### **2. Start Your Servers**

The tests need both servers running:

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend  
cd frontend
npm start
```

### **3. Run Tests**

```bash
# All BDD tests (headless)
./scripts/run_bdd_tests.sh

# With visible browser (great for debugging)
./scripts/run_bdd_tests.sh --headed

# Quick smoke tests only
./scripts/run_bdd_tests.sh --smoke

# API tests only (fast)
pytest tests/test_monte_carlo_api.py

# All tests with detailed output
pytest -v
```

## 📋 Test Scenarios

### **Core User Workflows**

✅ **Basic Simulation Setup**
- Configure human player and computer opponents
- Validate form inputs and error handling
- Ensure simulation button becomes enabled

✅ **Running Simulations**
- Execute Monte Carlo simulation with loading states
- Verify completion within time limits
- Validate result structure and content

✅ **Results Analysis**
- Check all 4 player statistics are displayed
- Verify win percentages add up to 100%
- Validate human player card highlighting

✅ **Error Handling**
- Invalid simulation counts (0, negative, >1000)
- Missing opponent configurations
- Network failures and timeouts

✅ **Performance Testing**
- Large simulations (100+ games)
- Response time validation
- Memory usage monitoring

✅ **Responsive Design**
- Mobile viewport testing
- Form accessibility on small screens
- Results display adaptation

### **Strategic Validation**

✅ **Handicap Impact Analysis**
- Low handicap vs high handicap scenarios
- Realistic win percentage expectations
- Score distribution validation

✅ **Personality Differences** 
- Aggressive vs conservative AI behavior
- Strategic decision-making validation
- Betting pattern analysis

✅ **Consistency Testing**
- Multiple runs with same configuration
- Results similarity (but not identical due to randomness)
- Reproducible business logic

## 🛠️ Writing New Tests

### **Adding Gherkin Scenarios**

1. **Edit the feature file** (`tests/features/monte_carlo_simulation.feature`):

```gherkin
Scenario: New testing scenario
  Given I have some initial condition
  When I perform some action
  Then I should see some expected result
```

2. **Implement step definitions** (`tests/step_definitions/monte_carlo_steps.py`):

```python
@given('I have some initial condition')
async def initial_condition(page: Page):
    # Implementation using Playwright
    await page.goto("http://localhost:3000/monte-carlo")

@when('I perform some action')
async def perform_action(page: Page):
    await page.click('button:has-text("Some Button")')

@then('I should see some expected result')
async def verify_result(page: Page):
    await expect(page.locator('.result')).to_be_visible()
```

### **Adding API Tests**

Add test methods to `tests/test_monte_carlo_api.py`:

```python
def test_new_api_functionality(self):
    response = requests.post(
        "http://localhost:8000/new-endpoint",
        json={"test": "data"}
    )
    assert response.status_code == 200
    assert response.json()["expected"] == "value"
```

## 🎯 Test Categories & Markers

Tests are organized with pytest markers:

```bash
# Run specific test categories
pytest -m bdd           # All BDD/Gherkin tests
pytest -m smoke         # Quick essential tests
pytest -m slow          # Long-running performance tests
pytest -m integration   # Full-stack workflow tests
pytest -m visual        # UI/visual validation tests
```

## 📊 Test Reports

### **HTML Reports**
- **Location**: `reports/bdd_test_report.html`
- **Features**: Screenshots, error details, timing
- **Usage**: Open in browser for visual test results

### **JUnit XML**
- **Location**: `reports/bdd_junit.xml` 
- **Features**: CI/CD integration, automated parsing
- **Usage**: Import into Jenkins, GitLab CI, etc.

### **Console Output**
- **Real-time**: Immediate feedback during test runs
- **Logging**: Detailed browser interactions and API calls
- **Debugging**: Console errors and network requests

## 🐛 Debugging Tests

### **Visual Debugging**
```bash
# Run with visible browser to see what's happening
./scripts/run_bdd_tests.sh --headed

# Run single test with maximum verbosity
pytest -v -s tests/step_definitions/monte_carlo_steps.py::test_name
```

### **Common Issues**

**❌ Servers not running**
```
Solution: Start backend and frontend servers first
```

**❌ Browser not found**
```bash
Solution: Install Playwright browsers
playwright install chromium
```

**❌ Timeout errors**
```
Solution: Increase timeouts in conftest.py or check server performance
```

**❌ Element not found**
```
Solution: Check CSS selectors in step definitions, elements may have changed
```

## 🔄 CI/CD Integration

### **GitHub Actions Example**

```yaml
name: BDD Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
          playwright install chromium
      
      - name: Start servers
        run: |
          cd backend && python -m uvicorn app.main:app &
          cd frontend && npm start &
          sleep 30
      
      - name: Run BDD tests
        run: ./scripts/run_bdd_tests.sh
      
      - name: Upload test reports
        uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: reports/
```

## 🎓 Best Practices

### **Writing Effective Gherkin**

✅ **DO:**
- Use business language, not technical terms
- Focus on user behavior and outcomes
- Keep scenarios independent and reusable
- Use specific, measurable assertions

❌ **DON'T:**
- Test implementation details
- Make scenarios dependent on each other
- Use technical jargon that business users won't understand
- Create overly complex scenarios

### **Browser Test Optimization**

✅ **DO:**
- Use specific CSS selectors
- Wait for elements to be ready before interacting
- Clean up browser state between tests
- Take screenshots on failures

❌ **DON'T:**
- Use hard-coded waits (sleep)
- Rely on element positions or timing
- Leave tests that modify global state
- Ignore browser console errors

### **Test Data Management**

✅ **DO:**
- Use realistic test data that matches production
- Create data factories for consistent test scenarios
- Clean up test data after scenarios
- Use different data sets for different test scenarios

❌ **DON'T:**
- Hard-code test data in multiple places
- Use production data in tests
- Leave test data lying around
- Use data that doesn't represent real usage

## 🏆 Advanced Testing Features

### **Visual Regression Testing**
```python
# Take screenshot and compare with baseline
await page.screenshot(path="reports/monte_carlo_results.png")
```

### **Performance Testing**
```python
# Monitor simulation performance
start_time = time.time()
await run_simulation()
duration = time.time() - start_time
assert duration < 30, f"Simulation too slow: {duration}s"
```

### **Cross-browser Testing**
```python
# Run same tests in different browsers
@pytest.mark.parametrize("browser_name", ["chromium", "firefox", "webkit"])
async def test_cross_browser(browser_name):
    # Test implementation
```

### **Mobile Testing**
```python
# Test responsive design
await page.set_viewport_size({"width": 375, "height": 667})
await verify_mobile_layout()
```

## 🎉 Conclusion

This comprehensive testing setup provides:

- **🥒 Business-readable scenarios** that document system behavior
- **🎭 Robust browser automation** with modern Playwright
- **⚡ Fast API testing** for quick feedback
- **📊 Beautiful reports** for results analysis
- **🚀 CI/CD ready** for automated deployment pipelines

The combination of **Gherkin BDD** and **headless Chrome** testing ensures that your Wolf Goat Pig Monte Carlo simulation is thoroughly tested from both user and technical perspectives, providing confidence in quality and preventing regressions as the system evolves.

**Happy Testing!** 🧪⚡🎯
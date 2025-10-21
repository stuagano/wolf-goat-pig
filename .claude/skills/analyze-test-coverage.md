# Skill: Analyze Test Coverage

## Description
Analyzes test coverage across backend and frontend, identifies gaps, and generates actionable recommendations.

## Usage
Invoke this skill when you need to understand test coverage, find untested code, and prioritize testing efforts.

## Steps

### 1. Generate Backend Coverage Report

```bash
cd backend

# Run tests with coverage
pytest --cov=app \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-report=json \
  -v

# Coverage report generated at:
# - HTML: htmlcov/index.html
# - JSON: coverage.json
# - Terminal: printed to stdout

echo "Backend coverage report generated"
```

### 2. Generate Frontend Coverage Report

```bash
cd frontend

# Run Jest with coverage
npm test -- --coverage --watchAll=false

# Coverage report generated at:
# - HTML: coverage/lcov-report/index.html
# - JSON: coverage/coverage-final.json
# - Terminal: printed to stdout

echo "Frontend coverage report generated"
```

### 3. Analyze Backend Coverage

```bash
cd backend

# Parse coverage.json to find low-coverage files
python3 << 'EOF'
import json

with open('coverage.json') as f:
    data = json.load(f)

files = data['files']
low_coverage = []

for filepath, metrics in files.items():
    coverage_percent = metrics['summary']['percent_covered']
    if coverage_percent < 80:
        low_coverage.append({
            'file': filepath,
            'coverage': coverage_percent,
            'missing_lines': len(metrics['missing_lines'])
        })

# Sort by coverage (lowest first)
low_coverage.sort(key=lambda x: x['coverage'])

print("\n=== LOW COVERAGE FILES (< 80%) ===\n")
for item in low_coverage[:20]:  # Top 20
    print(f"{item['file']:<60} {item['coverage']:>6.2f}%  ({item['missing_lines']} lines untested)")

print(f"\nTotal files with low coverage: {len(low_coverage)}")
EOF
```

### 4. Analyze Frontend Coverage

```bash
cd frontend

# Parse coverage-final.json
node << 'EOF'
const fs = require('fs');
const coverage = JSON.parse(fs.readFileSync('coverage/coverage-final.json'));

const lowCoverage = [];

for (const [filepath, metrics] of Object.entries(coverage)) {
  const { lines, functions, branches } = metrics;

  const linesCoverage = (lines.total > 0)
    ? (lines.covered / lines.total) * 100
    : 100;

  if (linesCoverage < 80) {
    lowCoverage.push({
      file: filepath.replace(process.cwd(), ''),
      linesCoverage: linesCoverage.toFixed(2),
      functionsCoverage: ((functions.covered / functions.total) * 100).toFixed(2),
      branchesCoverage: ((branches.covered / branches.total) * 100).toFixed(2),
    });
  }
}

lowCoverage.sort((a, b) => a.linesCoverage - b.linesCoverage);

console.log("\n=== LOW COVERAGE FILES (< 80%) ===\n");
console.log("File                                                 Lines    Functions  Branches");
console.log("=".repeat(90));

lowCoverage.slice(0, 20).forEach(item => {
  const file = item.file.substring(0, 50).padEnd(50);
  console.log(`${file} ${item.linesCoverage.padStart(6)}%  ${item.functionsCoverage.padStart(6)}%     ${item.branchesCoverage.padStart(6)}%`);
});

console.log(`\nTotal files with low coverage: ${lowCoverage.length}`);
EOF
```

### 5. Identify Critical Untested Code

```bash
# High-priority files that should have high coverage
echo "=== CRITICAL FILES COVERAGE ANALYSIS ==="

cd backend

# Check coverage for critical services
python3 << 'EOF'
import json

critical_files = [
    'app/wolf_goat_pig_simulation.py',
    'app/services/odds_calculator.py',
    'app/services/monte_carlo.py',
    'app/services/team_formation_service.py',
    'app/game_state.py',
    'app/domain/shot_result.py',
]

with open('coverage.json') as f:
    data = json.load(f)

print("\nCritical Backend Files:\n")
print("File                                          Coverage   Status")
print("=" * 70)

for filepath in critical_files:
    full_path = f'/home/user/wolf-goat-pig/backend/{filepath}'
    if full_path in data['files']:
        coverage = data['files'][full_path]['summary']['percent_covered']
        status = "✅ GOOD" if coverage >= 90 else "⚠️  LOW" if coverage >= 70 else "❌ CRITICAL"
        print(f"{filepath:<45} {coverage:>6.2f}%   {status}")
    else:
        print(f"{filepath:<45}  NOT TESTED ❌")
EOF
```

### 6. Generate Coverage Summary Report

```bash
cat > coverage-report.md << 'EOF'
# Test Coverage Analysis Report

Generated: $(date)

## Overall Coverage

### Backend
- **Lines**: X%
- **Functions**: X%
- **Branches**: X%

### Frontend
- **Lines**: X%
- **Functions**: X%
- **Branches**: X%
- **Statements**: X%

## Critical Gaps

### Backend (< 80% coverage)
1. `app/services/odds_calculator.py` - 65% (priority: HIGH)
2. `app/wolf_goat_pig_simulation.py` - 72% (priority: CRITICAL)
3. `app/game_state.py` - 78% (priority: HIGH)

### Frontend (< 80% coverage)
1. `src/pages/GamePage.js` - 45% (priority: HIGH)
2. `src/components/simulation/DecisionPanel.tsx` - 60% (priority: MEDIUM)
3. `src/hooks/useGameState.js` - 55% (priority: HIGH)

## Recommendations

### Backend Testing Priorities
1. **wolf_goat_pig_simulation.py** (3,868 lines)
   - Add tests for partnership formation logic
   - Test lone wolf scenarios
   - Add edge cases for tie handling

2. **odds_calculator.py** (36KB)
   - Test all betting scenarios
   - Validate probability calculations
   - Add Monte Carlo simulation tests

3. **team_formation_service.py**
   - Test 4, 5, 6 player scenarios
   - Validate handicap distributions
   - Test team balance algorithms

### Frontend Testing Priorities
1. **GamePage.js**
   - Add component render tests
   - Test state updates
   - Mock API calls and test error handling

2. **SimulationDecisionPanel.tsx**
   - Test all decision types (lone wolf, partnership, pass)
   - Test disabled states
   - Validate pot calculations display

3. **Custom Hooks**
   - Test useGameState with different game states
   - Test error scenarios
   - Test polling behavior

## Action Items
- [ ] Write tests for wolf_goat_pig_simulation.py to reach 90%
- [ ] Add unit tests for odds_calculator.py
- [ ] Create component tests for GamePage
- [ ] Test all custom hooks
- [ ] Add integration tests for betting flows
- [ ] Achieve overall backend coverage > 85%
- [ ] Achieve overall frontend coverage > 80%
EOF

echo "Coverage report created at coverage-report.md"
```

### 7. Visualize Coverage Trends

```bash
# Track coverage over time
mkdir -p coverage-history

# Save current coverage
DATE=$(date +%Y-%m-%d)
cd backend
BACKEND_COV=$(pytest --cov=app --cov-report=term | grep TOTAL | awk '{print $4}')

cd ../frontend
FRONTEND_COV=$(npm test -- --coverage --watchAll=false 2>&1 | grep "All files" | awk '{print $4}')

echo "$DATE,$BACKEND_COV,$FRONTEND_COV" >> ../coverage-history/coverage.csv

# Plot coverage trend (if gnuplot installed)
cat > plot-coverage.gnuplot << 'EOF'
set terminal png size 800,600
set output 'coverage-trend.png'
set title 'Test Coverage Over Time'
set xlabel 'Date'
set ylabel 'Coverage %'
set datafile separator ','
set xdata time
set timefmt '%Y-%m-%d'
set format x '%m/%d'
set grid
plot 'coverage-history/coverage.csv' using 1:2 with lines title 'Backend', \
     '' using 1:3 with lines title 'Frontend'
EOF

gnuplot plot-coverage.gnuplot 2>/dev/null || echo "Install gnuplot for coverage trends"
```

### 8. Open Coverage Reports

```bash
# Open in browser
echo "Opening coverage reports..."

# Backend
open backend/htmlcov/index.html 2>/dev/null || \
  xdg-open backend/htmlcov/index.html 2>/dev/null || \
  echo "Backend coverage: file://$(pwd)/backend/htmlcov/index.html"

# Frontend
open frontend/coverage/lcov-report/index.html 2>/dev/null || \
  xdg-open frontend/coverage/lcov-report/index.html 2>/dev/null || \
  echo "Frontend coverage: file://$(pwd)/frontend/coverage/lcov-report/index.html"
```

## Coverage Targets

### Backend
- **Overall**: > 85%
- **Critical modules** (simulation, betting): > 95%
- **Services**: > 80%
- **Utils**: > 70%

### Frontend
- **Overall**: > 80%
- **Components**: > 75%
- **Pages**: > 70%
- **Hooks**: > 90%
- **Utils**: > 85%

## Success Indicators
- ✅ Coverage reports generated for backend and frontend
- ✅ Low-coverage files identified and prioritized
- ✅ Critical gaps documented
- ✅ Actionable recommendations created
- ✅ Coverage trends tracked over time
- ✅ Reports accessible in browser

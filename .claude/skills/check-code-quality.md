# Skill: Check Code Quality

## Description
Runs linters, formatters, and type checkers across the codebase to ensure code quality standards.

## Usage
Invoke this skill before committing code to ensure it meets project quality standards.

## Steps

### 1. Backend Code Quality

#### Lint with Ruff
```bash
cd backend

# Install ruff if needed
pip install ruff

# Run linter
ruff check .

# Auto-fix issues
ruff check --fix .
```

#### Format with Black
```bash
# Install black if needed
pip install black

# Check formatting
black --check app/

# Auto-format
black app/
```

#### Type Check with MyPy
```bash
# Install mypy if needed
pip install mypy

# Run type checker
mypy app/ --ignore-missing-imports
```

#### Check imports with isort
```bash
# Install isort if needed
pip install isort

# Check import sorting
isort --check-only app/

# Auto-fix imports
isort app/
```

### 2. Frontend Code Quality

#### Lint with ESLint
```bash
cd frontend

# Run ESLint
npm run lint

# Auto-fix issues
npm run lint -- --fix
```

#### Format with Prettier
```bash
# Check formatting
npx prettier --check "src/**/*.{js,jsx,ts,tsx,css}"

# Auto-format
npx prettier --write "src/**/*.{js,jsx,ts,tsx,css}"
```

#### Type Check TypeScript
```bash
# If using TypeScript
npx tsc --noEmit
```

### 3. Security Checks

#### Backend Security
```bash
cd backend

# Install safety
pip install safety

# Check for known vulnerabilities
safety check

# Check with bandit for security issues
pip install bandit
bandit -r app/
```

#### Frontend Security
```bash
cd frontend

# Check for vulnerabilities
npm audit

# Fix auto-fixable vulnerabilities
npm audit fix

# Check for outdated packages
npm outdated
```

### 4. Code Complexity

#### Backend Complexity
```bash
# Install radon
pip install radon

# Check cyclomatic complexity
radon cc backend/app -a

# Check maintainability index
radon mi backend/app
```

### 5. Generate Quality Report

```bash
echo "=== CODE QUALITY SUMMARY ==="
echo ""
echo "Backend:"
echo "  - Linting: ruff check ."
echo "  - Formatting: black --check app/"
echo "  - Type checking: mypy app/"
echo "  - Security: bandit -r app/"
echo ""
echo "Frontend:"
echo "  - Linting: npm run lint"
echo "  - Formatting: prettier --check src/"
echo "  - Security: npm audit"
```

## Quality Standards

### Backend
- **Linting**: Zero ruff violations
- **Formatting**: Black-compliant (line length: 100)
- **Type Coverage**: > 70% with mypy
- **Security**: No high/medium severity issues
- **Complexity**: Cyclomatic complexity < 10 per function

### Frontend
- **Linting**: Zero ESLint errors (warnings OK)
- **Formatting**: Prettier-compliant
- **Security**: No high/critical npm audit issues
- **Bundle Size**: < 500KB gzipped

## Auto-fix Script

Create a helper script to auto-fix common issues:

```bash
#!/bin/bash
# scripts/fix-quality.sh

echo "Fixing backend code quality..."
cd backend
ruff check --fix .
black app/
isort app/

echo "Fixing frontend code quality..."
cd ../frontend
npm run lint -- --fix
npx prettier --write "src/**/*.{js,jsx,ts,tsx,css}"

echo "Code quality fixes applied!"
```

## Pre-commit Hook

Add to `.husky/pre-commit`:
```bash
#!/bin/sh

# Run code quality checks
echo "Running code quality checks..."

# Backend
cd backend && ruff check . && black --check app/ || exit 1

# Frontend
cd ../frontend && npm run lint || exit 1

echo "Code quality checks passed!"
```

## Success Indicators
- ✅ Zero linting errors
- ✅ Code properly formatted
- ✅ No type errors
- ✅ No security vulnerabilities
- ✅ Complexity within acceptable range

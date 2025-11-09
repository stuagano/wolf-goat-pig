# Database Transaction Linting Rules

This document describes the custom linting rules for catching PostgreSQL transaction errors.

## Quick Start

### Run the Linter

```bash
# Lint entire app directory
python lint_db_transactions.py app/

# Lint specific file
python lint_db_transactions.py app/seed_data.py

# Lint from project root
cd backend && python lint_db_transactions.py
```

### Install Pre-commit Hook (Recommended)

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the hooks
cd /path/to/wolf-goat-pig
pre-commit install

# Now the linter runs automatically on git commit
```

### Run Pre-commit Manually

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

---

## Linting Rules

### DB001: Datetime Type Mismatch

**Severity:** ERROR

**Pattern Detected:**
```python
# ❌ INCORRECT - Will fail on PostgreSQL
created_at = datetime.now()
updated_at = datetime.utcnow()
```

**Why This Is Bad:**
- PostgreSQL models define timestamp fields as `String` columns
- Application uses ISO format strings: `"2025-11-09T22:39:49.123456"`
- PostgreSQL strictly enforces types and rejects datetime objects in VARCHAR columns
- SQLite is lenient (auto-converts), masking the issue during development

**Correct Pattern:**
```python
# ✅ CORRECT - Works on both SQLite and PostgreSQL
created_at = datetime.now().isoformat()
updated_at = datetime.utcnow().isoformat()
```

**Fields Checked:**
- `created_at`
- `updated_at`
- `last_played`
- `joined_at`
- `completed_at`
- `earned_date`
- `score_date`
- `ghin_last_updated`
- `signup_time`
- `message_time`

---

### DB002: Missing Rollback in Query Loop

**Severity:** WARNING

**Pattern Detected:**
```python
# ❌ INCORRECT - Transaction abort cascades to next iteration
for player in players:
    try:
        profile = db.query(PlayerProfile).filter(...).first()
        # ... do something ...
    except Exception as e:
        logger.warning(f"Failed: {e}")
        continue  # ⚠️ Transaction still aborted!
```

**Why This Is Bad:**
1. Query fails → PostgreSQL aborts transaction
2. Exception caught but transaction NOT rolled back
3. Loop continues to next iteration
4. Next `db.query()` fails with: "current transaction is aborted, commands ignored until end of transaction block"
5. Error cascades through all remaining iterations

**Correct Pattern:**
```python
# ✅ CORRECT - Rollback clears aborted transaction state
for player in players:
    try:
        profile = db.query(PlayerProfile).filter(...).first()
        # ... do something ...
    except Exception as e:
        logger.warning(f"Failed: {e}")
        # Rollback transaction to clear error state
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.warning(f"Rollback failed: {rollback_error}")
        continue  # ✅ Safe to continue now
```

**Alternative Pattern (Batch Operations):**
```python
# ✅ ALTERNATIVE - Commit after each successful operation
for player in players:
    try:
        profile = db.query(PlayerProfile).filter(...).first()
        # ... do something ...
        db.commit()  # Commit immediately
    except Exception as e:
        logger.warning(f"Failed: {e}")
        db.rollback()
        continue
```

---

## Understanding the Errors

### Why These Issues Happen

**SQLite vs PostgreSQL Differences:**

| Aspect | SQLite | PostgreSQL |
|--------|--------|------------|
| Type Enforcement | Lenient (auto-converts) | Strict (rejects type mismatches) |
| Datetime Handling | Accepts datetime objects | Requires strings for VARCHAR columns |
| Transaction State | Forgiving | Aborts on first error, blocks all subsequent queries |

**Common Scenario:**

1. Code works fine in SQLite development environment
2. Deploy to PostgreSQL production
3. First query with datetime object fails
4. Transaction aborts
5. Loop continues without rollback
6. All subsequent queries fail with "transaction aborted" error
7. Application appears completely broken

---

### DB003: Rollback in Loop After Flush (Manual Check)

**Severity:** ERROR (requires manual code review)

**Pattern:**
```python
# ❌ DANGEROUS - Rollback discards flushed objects
game_record = GameRecord(...)
db.add(game_record)
db.flush()  # Gets game_record.id

for player in players:
    try:
        result = GamePlayerResult(game_record_id=game_record.id)
        db.add(result)
    except Exception as e:
        db.rollback()  # ⚠️ Discards game_record!
        continue  # ⚠️ But loop continues with stale game_record.id
```

**The Problem:**
1. Object is added and flushed to get its ID (e.g., `game_record.id = 123`)
2. Loop uses that ID for related objects (`game_record_id=123`)
3. Exception occurs → rollback discards the flushed object
4. Loop continues → subsequent iterations use stale ID (123) that no longer exists
5. Commit fails with foreign key constraint violation

**Correct Pattern (Skip Failed Batch):**
```python
# ✅ CORRECT - Skip entire batch after rollback
game_record = GameRecord(...)
db.add(game_record)
db.flush()

batch_failed = False
for player in players:
    try:
        result = GamePlayerResult(game_record_id=game_record.id)
        db.add(result)
    except Exception as e:
        db.rollback()  # Discards game_record
        batch_failed = True
        break  # ✅ Exit loop - can't continue with rolled-back parent

if not batch_failed:
    db.commit()  # Only commit if all succeeded
```

**Alternative Pattern (Recreate Parent):**
```python
# ✅ ALTERNATIVE - Recreate parent after rollback
for player in players:
    try:
        # Recreate parent if it was rolled back
        if not hasattr(game_record, 'id'):
            game_record = GameRecord(...)
            db.add(game_record)
            db.flush()

        result = GamePlayerResult(game_record_id=game_record.id)
        db.add(result)
    except Exception as e:
        db.rollback()
        game_record = None  # Mark as needing recreation
        continue
```

**Why This Is Critical:**
- Foreign key constraints will fail on commit
- Creates orphaned records
- Data integrity violations
- Silent data loss (partial batches)

---

## Best Practices

### 1. Always Use `.isoformat()` for Timestamps

```python
# Model definition (models.py)
class PlayerProfile(Base):
    created_at = Column(String)  # String column

# Code usage
player = PlayerProfile(
    name="Player",
    created_at=datetime.now().isoformat()  # ✅ Always use .isoformat()
)
```

### 2. Always Rollback in Exception Handlers

```python
# In loops with database queries
for item in items:
    try:
        result = db.query(...).first()
    except Exception as e:
        db.rollback()  # ✅ Always rollback
        continue
```

### 3. Test Against PostgreSQL

```bash
# Run tests against PostgreSQL, not just SQLite
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
pytest tests/
```

### 4. Use Type Hints

```python
from datetime import datetime

def create_player(created_at: str):  # ✅ Type hint indicates string expected
    player = PlayerProfile(created_at=created_at)
```

---

## Suppressing False Positives

If you have a legitimate case where the linter is wrong, add a comment:

```python
created_at = datetime.now()  # noqa: DB001 - justified reason here
```

---

## Integration with CI/CD

### GitHub Actions

```yaml
# .github/workflows/lint.yml
name: Lint Database Transactions

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Run Database Transaction Linter
        run: |
          cd backend
          python lint_db_transactions.py app/
```

### Pre-push Hook

```bash
# .git/hooks/pre-push
#!/bin/bash
cd backend
python lint_db_transactions.py app/
```

---

## Troubleshooting

### Linter Not Running

```bash
# Check pre-commit installation
pre-commit --version

# Reinstall hooks
pre-commit uninstall
pre-commit install

# Run manually to test
pre-commit run --all-files
```

### False Positives

The linter uses regex patterns which may occasionally flag valid code. Review warnings carefully and suppress with `# noqa` comments if needed.

### Need to Skip Pre-commit

```bash
# Skip all pre-commit hooks (not recommended)
git commit --no-verify -m "message"

# Better: Fix the issues the linter found
```

---

## Additional Resources

- [PostgreSQL Type System](https://www.postgresql.org/docs/current/datatype.html)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [Pre-commit Framework](https://pre-commit.com/)

---

## Support

If you encounter issues with the linter, check:

1. Python version (requires 3.7+)
2. File encoding (should be UTF-8)
3. Regex patterns may need updates for edge cases

Report issues or suggest improvements via GitHub issues.

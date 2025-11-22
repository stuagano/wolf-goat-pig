# Type Checking Setup

This project uses `mypy` for static type checking to prevent runtime type errors.

## Quick Start

```bash
# Install dev dependencies
pip install -r requirements-local.txt

# Run type checker manually
cd backend
mypy app/routers/ app/state/

# Or use pre-commit hooks (recommended)
pre-commit install
pre-commit run mypy --all-files
```

## What Does This Prevent?

The type checker would have caught the bug where `get_courses()` returns a list but was treated as a dict:

```python
# ❌ This causes: 'list' object has no attribute 'keys'
courses = get_courses()  # Returns List[Dict[str, Any]]
list(courses.keys())      # Type error! courses is a list, not a dict

# ✅ Correct approach
[c["name"] for c in courses]
```

## Configuration

- **mypy.ini**: Configuration file
- **pyproject.toml**: Ruff linter/formatter config
- **.pre-commit-config.yaml**: Pre-commit hooks

## Current Coverage

We use a **progressive adoption** strategy:

- ✅ **Fully checked**: `app/routers/health.py`, `app/state/course_manager.py`
- 🔄 **Gradually adding**: Other routers and state managers
- ⏸️ **Skipped for now**: Models, core game logic (too many errors to fix at once)

## Adding Type Hints

When adding type hints to new or existing functions:

```python
# ❌ No type hints
def get_player(player_id):
    return db.query(Player).get(player_id)

# ✅ With type hints
def get_player(player_id: int) -> Optional[Player]:
    return db.query(Player).get(player_id)
```

## CI/CD Integration

Type checking runs automatically in GitHub Actions:
- Runs on every PR
- Must pass to merge (unless `continue-on-error: true`)

## Troubleshooting

If mypy reports errors in SQLAlchemy models, you can:

1. Add to mypy.ini to skip that module temporarily:
   ```ini
   [mypy-app.module_name]
   ignore_errors = True
   ```

2. Or suppress specific lines with `# type: ignore`

## Resources

- [mypy documentation](https://mypy.readthedocs.io/)
- [Python type hints guide](https://docs.python.org/3/library/typing.html)
- [FastAPI type hints](https://fastapi.tiangolo.com/python-types/)

# Behaviour-Driven Development Workflow

Wolf Goat Pig now supports authoring functional requirements in plain English, converting them to
Gherkin feature files, and executing them automatically with Behave (Cucumber for Python).

## Quick Start

1. Describe the behaviour you want in natural language. The AI agent can help translate this narrative
   into a structured Gherkin feature and matching step definitions.
2. Save scenarios under `tests/bdd/features/*.feature`. Each file can contain one or more related
   scenarios.
3. Implement or extend Python step definitions in `tests/bdd/steps/`. Shared hooks live in
   `tests/bdd/environment.py`.
4. Run the suite locally:

   ```bash
   npm run test:bdd            # Uses scripts/testing/run_behave.sh under the hood
   # or
   ./scripts/testing/run_behave.sh --tags @smoke
   ```

5. Behave uses FastAPI's `TestClient`, so the scenarios execute quickly without launching the
   production servers. Database access defaults to the SQLite snapshot in `reports/wolf_goat_pig.db`.

## Writing Scenarios Collaboratively with the AI Agent

- Share the user story or requirement in English.
- Ask the agent to propose a `Feature` title, `Background` steps (if needed), and each `Scenario` with
  `Given/When/Then` statements.
- The agent can generate matching Python step skeletons so you only fill in business logic.
- For JSON assertions, use the built-in step `And the JSON response contains:` and provide a table of
  key/value expectations.

## Folder Layout

```
tests/bdd/
├── environment.py          # Behave hooks (adds repo root to PYTHONPATH)
├── features/
│   └── simulation_health.feature
└── steps/
    └── simulation_steps.py
```

## Useful Commands

| Task                                   | Command                                      |
|----------------------------------------|----------------------------------------------|
| Run all BDD scenarios                  | `npm run test:bdd`                           |
| Filter scenarios by tag                | `./scripts/testing/run_behave.sh --tags @ui` |
| Re-run last failed scenario only       | `behave tests/bdd --format progress2`        |
| Generate step definition stubs         | `behave --dry-run --no-summary -q`           |

## Continuous Integration

The pre-push hook continues to execute the simulation regression suite. You can layer BDD checks into
CI by invoking `npm run test:bdd` in your pipeline once the backend dependencies are installed.

## Best Practices

- Keep scenarios declarative. Offload implementation specifics to Python step definitions.
- Use `Background` for common setup to reduce duplication.
- When asserting JSON, prefer table syntax for clarity and to reuse the shared step implementation.
- Tag scenarios (e.g., `@smoke`, `@regression`) to control execution subsets when the library grows.

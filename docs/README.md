# Documentation Index

This directory contains reference material for the Wolf Goat Pig project. Documents
are grouped by purpose so you can quickly find what you need.

## Guides

Day-to-day engineering workflow, deployment, and troubleshooting:

- [Local development](./guides/local-development.md) - Getting started locally
- [Developer quick start](./guides/DEVELOPER_QUICK_START.md) - Fast orientation for contributors
- [Deployment](./guides/DEPLOYMENT.md) - Deploy process for Render + Vercel
- [Deployment troubleshooting](./guides/deployment-troubleshooting.md) - Common deploy issues and fixes
- [Docker setup](./guides/DOCKER-SETUP.md) - Local production-parity container stack
- [Vercel configuration](./guides/VERCEL_CONFIG.md) - Vercel build/config notes
- [Resilience guide](./guides/RESILIENCE_GUIDE.md) - Fault tolerance and recovery
- [BDD workflow](./guides/bdd-workflow.md) - Behave end-to-end testing
- [Validator usage](./guides/VALIDATOR_USAGE_GUIDE.md) - Game-state validators
- [GHIN integration](./guides/GHIN_INTEGRATION_GUIDE.md) - Handicap service integration
- [Golf course offline](./guides/GOLF_COURSE_OFFLINE_GUIDE.md) - Offline course data
- [Google Sheets sync](./guides/google-sheets-sync.md) - Sheet integration
- [Legacy signup bridge](./guides/legacy-signup-bridge.md) - Legacy system integration

## Architecture

System design, data model, and source layout:

- [Architecture](./architecture/architecture.md) - System architecture (canonical)
- [Source tree](./architecture/source-tree.md) - Repository layout and entry points
- [Tech stack](./architecture/tech-stack.md) - Languages, frameworks, tooling
- [Database schema](./architecture/DATABASE_SCHEMA.md) - Tables and relationships
- [Coding standards](./architecture/coding-standards.md) - Conventions and style

## Backend

Backend-specific operational guides:

- [Bootstrap](./backend/BOOTSTRAP_README.md) - Backend setup
- [Database session guide](./backend/DATABASE_SESSION_GUIDE.md) - Session handling
- [DB linting rules](./backend/DB_LINTING_RULES.md) - Database query linting
- [Migration guide](./backend/MIGRATION_GUIDE.md) - Schema migrations
- [Type checking](./backend/README_TYPE_CHECKING.md) - mypy usage
- [Rule manager quickstart](./backend/RULE_MANAGER_QUICKSTART.md) - Rules engine
- [Sheet sync scheduler](./backend/SHEET_SYNC_SCHEDULER.md) - Scheduled sheet sync

## Features

Feature specifications and game rules:

- [Wolf Goat Pig rules](./features/WOLF_GOAT_PIG_RULES.md) - Canonical game rules
- [Enhanced WGP features](./features/ENHANCED_WGP_FEATURES.md)
- [Betting tracker](./features/BETTING_TRACKER.md)
- [Game-state widget](./features/GAMESTATE_WIDGET_FEATURE.md)
- [Achievement badges](./features/achievement-badge-guide.md)
- [Scorecard photo capture](./features/SCORECARD_PHOTO_CAPTURE.md)
- [Scorecard scan improvements](./features/SCORECARD_SCAN_IMPROVEMENTS.md)

## Product context

- [Gameplay user journey](./product/gameplay-user-journey.md)

## Observability

- [Sentry setup](./observability/sentry-setup.md) - Error tracking
- [Uptime monitoring](./observability/uptime-setup.md) - Synthetic monitoring
- [Render blueprint](./observability/render-blueprint.md) - Infrastructure as code

## Development & automation

- [Contributor guidelines](./development/AGENTS.md) - Testing requirements and conventions
- [Claude automation](./development/CLAUDE_AUTOMATION_README.md) - AI automation setup

## Quick commands

Run from the repository root (see root `package.json` for the full script list):

```bash
./scripts/development/dev.sh   # start backend + frontend for local development
npm run test:backend           # backend tests (pytest)
npm run test:frontend          # frontend tests (Vitest)
npm run typecheck              # backend (mypy) + frontend (tsc) type checks
```

For deployment verification commands, see
[Deployment troubleshooting](./guides/deployment-troubleshooting.md).

---
*Last updated: 2026-06-17*

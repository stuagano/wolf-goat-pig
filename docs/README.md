# Documentation Index

This directory contains reference material for the Wolf Goat Pig project. Documents are grouped by purpose so you can quickly find what you need.

## Guides

Day-to-day engineering workflow, troubleshooting, and deployment:

- [Local development](./guides/local-development.md) - Getting started with local development
- [Local deployment testing](./guides/local-deployment-testing.md) - Test deployments locally before production
- [Production setup](./guides/production-setup.md) - Complete production deployment guide
- [Deployment troubleshooting](./guides/deployment-troubleshooting.md) - Common deployment issues and solutions
- [Project structure](./guides/project-structure.md) - Codebase organization
- [Browser testing](./guides/browser-testing.md) - Browser automation testing
- [Legacy signup bridge](./guides/legacy-signup-bridge.md) - Legacy system integration

## Product context

Game design, user journeys, and integration notes:

- [Gameplay user journey](./product/gameplay-user-journey.md)
- [Integration summary](./product/integration-summary.md)
- [TV poker style UX](./product/tv-poker-style-ux.md)

## Status & reports

- [Current project status](./status/current-state.md)
- [Development environment audit](./reports/development-environment-report.md)
- [Historical WGP round results](./reports/wgp-round-test-summary.md)

## Additional references

- [Architecture diagrams and specs](./architecture/)
- [Product requirements & story backlog](./development/prd.md), [`./stories/`](./stories/)
- [Action API contract](./architecture/UNIFIED_ACTION_API.md)

## Quick Testing Commands

### Development
```bash
./scripts/development/dev.sh  # Start both servers
npm run test:all           # Run all tests
npm run test:backend       # Backend tests only
npm run test:frontend      # Frontend tests only
```

### Deployment Testing
```bash
npm run deploy:check       # Check deployment readiness
npm run deploy:test        # Interactive deployment testing
npm run deploy:verify      # Verify deployment health
npm run docker:prod        # Full Docker production stack
```

## Archive

Additional development artifacts (AI-agent prompts, automation docs, and planning documents) are available under [`./development/`](./development/).

---
*Last updated: 2025-10-12*

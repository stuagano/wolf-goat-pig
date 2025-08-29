---
allowed-tools: web_search, web_fetch
description: Generate a comprehensive Product Requirements Document (PRD) with business context and technical direction for Rails applications
---

# Create PRD Command

## Goal
Generate a detailed Product Requirements Document (PRD) that helps break down features into implementable tasks for FastAPI/React applications, with a focus on business value and clear technical direction.

## Context
- **Stack**: FastAPI (Python) with SQLAlchemy ORM and PostgreSQL/SQLite
- **Frontend**: React with hooks, JavaScript/JSX
- **Styling**: CSS modules and responsive design
- **State Management**: React hooks (useState, useEffect, custom hooks)
- **Target**: Features will be split into small, manageable tasks/subtasks

## Process

### 1. Initial Analysis
When given a feature request, first understand:
- Business problem being solved
- Target users and their needs
- Success metrics and business impact

### 2. Clarifying Questions
Ask targeted questions with multiple choice options where possible:

**Business Context:**
- What business problem does this solve?
- Who are the primary users? (a) End customers (b) Internal team (c) Partners (d) Other
- What's the expected business impact? (a) Revenue increase (b) Cost reduction (c) User engagement (d) Operational efficiency

**Functional Requirements:**
- What are the core user actions?
- What data needs to be captured/displayed?
- Are there existing similar features to reference?

**Technical Scope:**
- Does this integrate with existing models/systems?
- Are there third-party APIs involved? (a) Google Sheets (b) Email notifications (c) File storage (d) AI/ML (e) Authentication (f) Other
- What's the complexity level? (a) Simple CRUD (b) Complex game logic (c) Real-time features (d) Data analysis/simulation

### 3. Generate PRD Structure

## PRD Template

```markdown
# PRD: [Feature Name]

## Overview
Brief description of the feature and the business problem it solves.

## Business Goals
- Primary business objective
- Success metrics (specific and measurable)
- Expected impact on revenue/engagement/efficiency

## User Stories
- As a [user type], I want to [action] so that [benefit]
- Include edge cases and error scenarios

## Functional Requirements

### Core Features
1. [Numbered list of must-have functionality]
2. [Be specific about user interactions]
3. [Include data validation rules]

### User Interface Requirements
- Key React components needed
- State management patterns (hooks, context)
- User interactions and event handling
- Mobile responsiveness requirements
- API integration points

### Data Requirements
- New SQLAlchemy models/attributes needed
- Database relationships and foreign keys
- Pydantic schemas for API validation
- Alembic migration considerations

## Technical Implementation Notes

### Backend (FastAPI) Considerations
- SQLAlchemy models and relationships
- API endpoints and routes needed
- Background task requirements (if any)
- Service layer organization
- Error handling and validation

### Frontend (React) Approach
- React components and hooks needed
- State management strategy
- API client integration
- Form handling and validation
- Custom hooks for business logic

### Third-party Integrations
- APIs to integrate
- Webhook handling
- External service dependencies

## Non-Goals (Out of Scope)
- Clear boundaries of what this feature will NOT include
- Future iterations that are explicitly excluded

## Success Metrics
- How success will be measured
- Analytics/tracking requirements
- A/B testing considerations (if applicable)

## Task Breakdown Preparation
- Identify logical chunks for separate pull requests
- Dependencies between tasks
- Suggested implementation order

## Open Questions
- Areas needing further clarification
- Technical decisions to be made during implementation
- Stakeholder approvals needed

## Acceptance Criteria
- Specific, testable criteria for feature completion
- Performance benchmarks
- Cross-browser/device testing requirements
```

## Instructions for Claude

1. **DO NOT** start writing the PRD immediately
2. **ALWAYS** ask clarifying questions first using the framework above
3. **FOCUS** on business value and clear technical direction
4. **CONSIDER** how the feature breaks down into small, manageable tasks
5. **ASSUME** the reader is a competent FastAPI/React developer but may need context on business goals
6. **SAVE** the final PRD as `prd-[feature-name].md` in the `/tasks` directory

## Example Question Flow

"I see you want to add [feature]. Before I create the PRD, let me ask a few questions:

**Business Context:**
A) What specific business problem does this solve?
B) Who are the primary users? (1) End customers (2) Internal team (3) Both
C) What's the main success metric? (1) Increase revenue (2) Improve efficiency (3) Better user experience

**Technical Scope:**
A) Does this need real-time updates? (1) Yes, critical (2) Nice to have (3) No
B) Third-party integrations needed? (1) Google Sheets integration (2) Email notifications (3) File uploads (4) None
C) Complexity level? (1) Simple CRUD (2) Complex game logic (3) Data analysis/simulation

Please respond with your choices (e.g., B2, A1, B3) and any additional context."

## About the PRD:

e
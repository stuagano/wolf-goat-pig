---
allowed-tools: web_search, web_fetch, repl
description: Break down a PRD into detailed, actionable Rails development tasks with codebase analysis
---

# Create Tasks from PRD Command

## Input
The PRD file can be found at the following path inside this project:
$ARGUMENTS

## Goal
Generate a detailed, step-by-step task list from an existing PRD that breaks down implementation into manageable chunks for Rails development, following established patterns and conventions.

## Context
- **Stack**: Ruby on Rails 8.0 with PostgreSQL and Active Record
- **Frontend**: HTML5, Tailwind CSS, Hotwire (Turbo + Stimulus)
- **JavaScript**: Always use Stimulus controllers
- **Testing**: RSpec for Ruby, Rails system tests for integration
- **Target**: Junior to mid-level Rails developers

## Process

### 1. PRD Analysis
Read and analyze the PRD file specified in the Input section above:
- Extract functional requirements and user stories
- Identify technical implementation requirements
- Understand business context and success metrics
- Note acceptance criteria and constraints

### 2. Current State Assessment
Before generating tasks:
- Review existing Rails models, controllers, and routes
- Identify existing Stimulus controllers and Turbo usage patterns
- Check for relevant existing components, partials, and stylesheets
- Note database structure and migration patterns
- Identify existing test patterns and coverage

### 3. Phase 1: Generate Parent Tasks
Create 4-6 high-level tasks that logically break down the feature:
- Database/Model changes
- Backend API/Controller logic
- Frontend UI implementation
- Testing and validation
- Deployment considerations

Present to user: "I have generated the high-level tasks based on the PRD analysis. Ready to generate the detailed sub-tasks? Respond with 'Go' to proceed."

### 4. Phase 2: Generate Detailed Sub-Tasks
Break down each parent task into specific, actionable items:
- Include file modifications needed
- Reference existing patterns to follow
- Consider Rails conventions and best practices
- Include testing requirements for each change

## Task List Template

```markdown
# Tasks: [Feature Name]

*Generated from the PRD file specified above*

## Relevant Files

### Models & Database
- `app/models/[model_name].rb` - Main model for [feature]
- `db/migrate/[timestamp]_[migration_name].rb` - Database changes
- `spec/models/[model_name]_spec.rb` - Model tests

### Controllers & Routes
- `app/controllers/[controller_name]_controller.rb` - Handle [feature] requests
- `config/routes.rb` - Add new routes
- `spec/controllers/[controller_name]_controller_spec.rb` - Controller tests
- `spec/requests/[feature_name]_spec.rb` - Request specs

### Views & Frontend
- `app/views/[controller]/[action].html.erb` - Main view templates
- `app/views/shared/_[partial_name].html.erb` - Reusable partials
- `app/javascript/controllers/[feature]_controller.js` - Stimulus controller
- `app/assets/stylesheets/components/[feature].css` - Feature-specific styles

### Background Jobs (if needed)
- `app/jobs/[job_name]_job.rb` - Background processing
- `spec/jobs/[job_name]_job_spec.rb` - Job tests

### Services/Concerns (if needed)
- `app/services/[service_name].rb` - Business logic service
- `app/concerns/[concern_name].rb` - Shared functionality
- `spec/services/[service_name]_spec.rb` - Service tests

### System Tests
- `spec/system/[feature_name]_spec.rb` - End-to-end feature tests

### Notes
- Follow Rails conventions for file naming and organization
- Use `rails generate` commands where appropriate
- Run `bundle exec rspec` to execute tests
- Use `rails console` for manual testing/debugging

## Tasks

- [ ] 1.0 Database & Model Setup
  - [ ] 1.1 Create migration for [specific changes]
  - [ ] 1.2 Add model validations and associations
  - [ ] 1.3 Add model methods for business logic
  - [ ] 1.4 Write comprehensive model tests
  - [ ] 1.5 Run migration and verify in development

- [ ] 2.0 Backend Controller Logic
  - [ ] 2.1 Add routes to config/routes.rb
  - [ ] 2.2 Create controller with CRUD actions
  - [ ] 2.3 Implement strong parameters
  - [ ] 2.4 Add authorization/authentication logic
  - [ ] 2.5 Handle error cases and validations
  - [ ] 2.6 Write controller and request specs

- [ ] 3.0 Frontend Implementation
  - [ ] 3.1 Create view templates with proper HTML structure
  - [ ] 3.2 Style with Tailwind CSS components
  - [ ] 3.3 Implement Turbo Frame interactions
  - [ ] 3.4 Add Stimulus controller for dynamic behavior
  - [ ] 3.5 Ensure mobile responsiveness
  - [ ] 3.6 Add proper form handling and validation display

- [ ] 4.0 Hotwire Integration
  - [ ] 4.1 Set up Turbo Streams for real-time updates
  - [ ] 4.2 Implement optimistic UI updates
  - [ ] 4.3 Add proper loading states and error handling
  - [ ] 4.4 Test Turbo interactions across different browsers

- [ ] 5.0 Testing & Quality Assurance
  - [ ] 5.1 Write comprehensive system tests
  - [ ] 5.2 Test edge cases and error scenarios
  - [ ] 5.3 Verify mobile and accessibility compliance
  - [ ] 5.4 Performance testing (if applicable)
  - [ ] 5.5 Security review (authorization, CSRF, etc.)

- [ ] 6.0 Documentation & Deployment
  - [ ] 6.1 Update README with feature documentation
  - [ ] 6.2 Add inline code comments for complex logic
  - [ ] 6.3 Verify staging deployment works correctly
  - [ ] 6.4 Plan production rollout strategy
  - [ ] 6.5 Set up monitoring/analytics (if specified in PRD)

## Implementation Notes

### Rails Conventions to Follow
- Use Rails form helpers and validation error display patterns
- Follow REST routing conventions where possible
- Use Rails naming conventions for files and classes
- Leverage Rails built-in security features (CSRF, strong params)

### Hotwire Best Practices
- Use Turbo Frames for isolated updates
- Implement Turbo Streams for real-time features
- Keep Stimulus controllers focused and reusable
- Use data attributes for controller configuration

### Testing Strategy
- Start with model tests for business logic
- Add controller/request tests for API behavior
- Use system tests for user workflows
- Mock external services in tests

### Performance Considerations
- Add database indexes for query performance
- Use Rails caching where appropriate
- Optimize N+1 queries with includes/joins
- Consider background jobs for heavy processing
```

## Instructions for Claude

1. **READ** the PRD file specified in the Input section above
2. **ANALYZE** the PRD thoroughly for requirements and business context
3. **ASSESS** the current Rails application structure and patterns
4. **GENERATE** 4-6 logical parent tasks first
5. **WAIT** for user confirmation with "Go" before proceeding
6. **BREAK DOWN** each parent task into specific, actionable sub-tasks
7. **CONSIDER** Rails conventions and existing code patterns
8. **INCLUDE** proper testing requirements for each task
9. **SAVE** as `tasks-[feature-name].md` in `/tasks/` directory

## Example Interaction Flow

"I'm reading and analyzing the PRD file to understand the feature requirements.

[After reading and analyzing the PRD content]

Based on the PRD analysis, here are the high-level tasks for implementing [feature name]:

- [ ] 1.0 Database & Model Setup
- [ ] 2.0 Backend Controller Logic
- [ ] 3.0 Frontend Implementation
- [ ] 4.0 Hotwire Integration
- [ ] 5.0 Testing & Quality Assurance
- [ ] 6.0 Documentation & Deployment

I have generated the high-level tasks based on the PRD analysis. Ready to generate the detailed sub-tasks? Respond with 'Go' to proceed."
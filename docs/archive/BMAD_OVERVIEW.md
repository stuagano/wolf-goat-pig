# BMad Method in Wolf Goat Pig Project

> **Archived**: The BMad framework assets now live under `docs/archive/bmad-core/` and are no longer part of the active development workflow.

This document provides a project-specific overview of how the BMad Method (Business Methodology for Agile AI-driven Development) is integrated and used within the Wolf Goat Pig golf simulation project.

## What is BMad Method?

BMad Method is a framework that combines AI agents with Agile development methodologies. It transforms traditional software development by using specialized AI agents to handle different roles (Product Manager, Architect, Developer, QA, etc.) within a structured workflow.

## How BMad Powers This Project

The Wolf Goat Pig project serves as a real-world demonstration of BMad Method's capabilities:

### 🎯 **Planning & Architecture**
- **Product Requirements**: Comprehensive PRD in `docs/prd.md` created by PM agent
- **System Architecture**: Detailed architecture specs in `docs/architecture.md` by Architect agent
- **User Stories**: Structured development stories in `docs/stories/` created by SM agent

### 🔧 **Development Workflow**
- **Story-Driven Development**: Each feature implemented as a complete user story
- **Test-Driven Development**: Comprehensive test coverage with quality gates
- **Quality Assurance**: QA agent reviews and refactors code for production readiness

### 📁 **Project Structure**
```
wolf-goat-pig/
├── .bmad-core/           # Complete BMad framework
│   ├── agents/           # AI agent definitions
│   ├── tasks/            # Reusable task templates
│   ├── workflows/        # Development workflows
│   └── user-guide.md     # Complete BMad documentation
├── docs/
│   ├── prd.md           # Product Requirements (PM agent)
│   ├── architecture.md  # System Architecture (Architect agent)
│   └── stories/         # User Stories (SM agent)
└── [application code]
```

## Current Development Stories

The project includes these completed and planned user stories:

1. **story-001-fix-typescript-errors.md** - TypeScript configuration and error resolution
2. **story-002-shot-range-integration.md** - Shot range analysis integration
3. **story-003-betting-odds-calculations.md** - Advanced betting calculations
4. **story-004-player-profiles.md** - Enhanced player profile system
5. **story-005-tutorial-onboarding.md** - Interactive tutorial system

## Key BMad Features Demonstrated

### 1. **Agent Specialization**
- **PM Agent**: Created comprehensive product requirements
- **Architect Agent**: Designed scalable system architecture
- **SM Agent**: Generated focused user stories with acceptance criteria
- **Dev Agent**: Implemented features with proper testing
- **QA Agent**: Performed code reviews and quality assurance

### 2. **Quality Documentation**
- **Living Documentation**: All docs are maintained and updated throughout development
- **Traceability**: Clear links between requirements, architecture, and implementation
- **Testing Strategy**: Comprehensive test coverage with quality gates

### 3. **Structured Workflow**
```mermaid
graph LR
    A[PM: Requirements] --> B[Architect: Design]
    B --> C[SM: Stories]
    C --> D[Dev: Implementation]
    D --> E[QA: Review]
    E --> F[Production Ready]
```

## Getting Started with BMad on This Project

### For New Developers

1. **Understand the Context**:
   ```bash
   # Read the product requirements
   cat docs/prd.md
   
   # Review the architecture
   cat docs/architecture.md
   
   # Check current stories
   ls docs/stories/
   ```

2. **Use BMad Agents**:
   ```bash
   # Create a new story
   @sm *create
   
   # Implement a story
   @dev implement story-xxx
   
   # Review completed work
   @qa *review story-xxx
   ```

3. **Follow the Workflow**:
   - Stories progress: Draft → Approved → InProgress → Done
   - Each story includes acceptance criteria and test requirements
   - QA review is mandatory before marking stories complete

### For Project Enhancement

1. **Adding New Features**:
   - Start with PM agent to update PRD if needed
   - Use Architect agent for significant architectural changes
   - Create stories with SM agent
   - Implement with Dev agent
   - Review with QA agent

2. **Maintaining Quality**:
   - All changes go through BMad workflow
   - Comprehensive testing is required
   - Documentation is updated automatically
   - Quality gates ensure production readiness

## Benefits Realized in This Project

### ⚡ **Development Speed**
- Rapid prototyping and feature implementation
- Automated documentation generation
- Reduced context switching between roles

### 🎯 **Quality Assurance**
- Comprehensive test coverage
- Structured code reviews
- Quality gates prevent defects

### 📚 **Knowledge Management**
- Living documentation stays current
- Clear development history and decisions
- Easy onboarding for new team members

### 🔄 **Agile Practices**
- Story-driven development
- Continuous validation
- Iterative improvement

## BMad Method Resources

- **Complete User Guide**: `.bmad-core/user-guide.md`
- **Agent Documentation**: `.bmad-core/agents/`
- **Task Templates**: `.bmad-core/tasks/`
- **Official Documentation**: [BMad Method GitHub](https://github.com/bmadcode/bmad-method)

## Success Metrics

This project demonstrates BMad Method's effectiveness:

- ✅ **Comprehensive Documentation**: Complete PRD and architecture specs
- ✅ **Test Coverage**: Full test suite with quality gates
- ✅ **Clean Architecture**: Well-structured, maintainable codebase
- ✅ **Rapid Development**: Complex features implemented quickly
- ✅ **Production Ready**: Deployed and running successfully

---

The Wolf Goat Pig project showcases how BMad Method transforms software development from idea to production-ready application through structured AI-agent collaboration and Agile methodologies.
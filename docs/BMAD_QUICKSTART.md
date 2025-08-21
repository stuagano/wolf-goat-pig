# BMad Method Quick Start Guide

Get up and running with BMad Method in the Wolf Goat Pig project in under 10 minutes.

## Prerequisites

- IDE with AI agent support (Cursor, Claude Code, Windsurf, VS Code + Copilot/Cline)
- Basic understanding of Agile development
- Familiarity with the project structure

## 🚀 Quick Setup (2 minutes)

### 1. Verify BMad Installation
```bash
# Check if BMad is already installed
ls .bmad-core/

# You should see:
# agents/    tasks/    workflows/    templates/    user-guide.md
```

✅ **Good news**: BMad is already installed in this project!

### 2. Review Project Context
```bash
# Read the product requirements (2-3 minutes)
cat docs/prd.md

# Review system architecture (2-3 minutes)  
cat docs/architecture.md

# Check existing stories
ls docs/stories/
```

## 🎯 Using BMad Agents (5 minutes)

### Agent Syntax by IDE

| IDE | Agent Syntax | Example |
|-----|-------------|---------|
| **Claude Code** | `/agent-name` | `/sm *create` |
| **Cursor** | `@agent-name` | `@sm *create` |
| **Windsurf** | `/agent-name` | `/sm *create` |
| **VS Code + Copilot** | Select from chat mode | Select "Agent" mode |

### Core Development Cycle

```mermaid
graph LR
    A[SM: Create Story] --> B[You: Approve Story]
    B --> C[Dev: Implement]
    C --> D[QA: Review]
    D --> E[Done]
```

### Step-by-Step Workflow

1. **Create a New Story** (SM Agent)
   ```bash
   # Start new chat session
   @sm *create
   ```
   - Reviews existing stories and epics
   - Creates next logical story
   - Saves to `docs/stories/story-XXX-name.md`

2. **Review & Approve** (You)
   - Read the generated story
   - Update status from "Draft" to "Approved"
   - Make any necessary adjustments

3. **Implement Story** (Dev Agent)
   ```bash
   # Start new chat session  
   @dev implement story-XXX-name
   ```
   - Reads the approved story
   - Implements all requirements
   - Writes comprehensive tests
   - Updates story status to "Review"

4. **Quality Review** (QA Agent)
   ```bash
   # Start new chat session
   @qa *review story-XXX-name
   ```
   - Performs senior developer code review
   - Refactors and improves code
   - Updates story status to "Done" if approved

## 🎯 Essential Commands

### Universal Commands (All Agents)
- `*help` - Show available commands
- `*status` - Show current context/progress
- `*exit` - Exit agent mode

### SM Agent (Story Creation)
- `*create` - Create next story from epics

### Dev Agent (Implementation)
- `implement story-name` - Implement specific story
- `fix bug-description` - Fix specific issues

### QA Agent (Quality Assurance)
- `*review story-name` - Comprehensive code review
- `*trace story-name` - Verify test coverage
- `*nfr story-name` - Check quality attributes

## 🔧 Quick Development Example

Let's create and implement a simple story:

### 1. Create Story (2 minutes)
```bash
# New chat session
@sm *create

# SM creates: story-006-example-feature.md
```

### 2. Implement Story (5-10 minutes)
```bash  
# New chat session
@dev implement story-006-example-feature

# Dev implements:
# - Backend API changes
# - Frontend components
# - Unit tests
# - Integration tests
```

### 3. Quality Review (2-5 minutes)
```bash
# New chat session  
@qa *review story-006-example-feature

# QA performs:
# - Code review
# - Test validation
# - Refactoring if needed
# - Quality gate assessment
```

## 📁 Key Files to Know

### Documentation
- `docs/prd.md` - Product requirements
- `docs/architecture.md` - System architecture  
- `docs/stories/` - Development stories

### BMad Core
- `.bmad-core/user-guide.md` - Complete BMad documentation
- `.bmad-core/agents/` - AI agent definitions
- `.bmad-core/tasks/` - Reusable task templates

### Configuration  
- `.bmad-core/core-config.yaml` - BMad configuration
- `.bmad-core/data/technical-preferences.md` - Tech preferences

## ⚡ Pro Tips

### 1. **Always Start Fresh**
- Use new chat sessions when switching agents
- This ensures clean context and better performance

### 2. **Follow the Workflow**
- SM → Dev → QA (always in this order)
- Don't skip steps or combine agents

### 3. **Review Everything**
- Always review generated stories before implementing
- Verify test coverage and quality gates

### 4. **Keep Context Lean**
- Include only relevant files in agent context
- Use specific agent for specific tasks

## 🚨 Common Issues

### Agent Not Found
```bash
# If agent doesn't load:
ls .bmad-core/agents/

# Verify the agent exists, then try:
@bmad-master help with sm tasks
```

### Story Creation Fails
```bash
# Check if epics exist:
ls docs/prd/

# If no epics, shard the PRD first:
@po *shard-doc docs/prd.md prd
```

### Implementation Errors
```bash
# Always include story content in dev context:
@dev implement story-XXX (include story file in chat)
```

## 🎯 Next Steps

1. **Try the Quick Example**: Follow the development example above
2. **Read Full Documentation**: Review `.bmad-core/user-guide.md`
3. **Explore Agents**: Check out different agents in `.bmad-core/agents/`
4. **Join Community**: [BMad Discord](https://discord.gg/gk8jAdXWmj)

## Success Indicators

You're successfully using BMad when:

- ✅ Stories are created consistently with acceptance criteria
- ✅ Implementation includes comprehensive tests
- ✅ Quality reviews catch issues before production
- ✅ Documentation stays current automatically
- ✅ Development velocity increases over time

---

**Ready to build?** Start with `@sm *create` and begin your first BMad-powered development cycle!
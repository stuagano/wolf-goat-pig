# Agent Workflow Guide
## Research → Planning → Implementation Pattern

This guide shows how to organize Claude Code agents into a three-phase workflow with human review checkpoints, inspired by Advanced Context Engineering patterns.

## Workflow Pattern

```
Research Phase → [HUMAN REVIEW] → Planning Phase → [HUMAN REVIEW] → Implementation Phase
     ↓                                    ↓                                   ↓
 research.md                          plan.md                            Code Changes
```

## Phase 1: Research

**Goal**: Gather information, analyze codebase, understand requirements

**Tools Available**:
- Task() - Spawn research subagents
- Glob/Grep - Search codebase
- Read - Read files
- WebSearch/WebFetch - External research

**Agents for Research**:
- `test-coverage-agent.md` - Research current test coverage
- `component-testing-agent.md` - Analyze component architecture
- `rules-validation-agent.md` - Research business rules
- `error-handling-agent.md` - Analyze error patterns
- `api-docs-agent.md` - Research API structure

**Output**: Creates `research.md` with findings

**Example Research Agent Structure**:
```markdown
# Research Agent: Test Coverage Analysis

## Phase: Research
Your job is to research and document, NOT to implement changes.

## Steps:
1. Use Glob to find all test files
2. Use Grep to analyze test patterns
3. Use Read to examine key test files
4. Spawn subagents if needed with Task()

## Output:
Create a file called `research.md` with:
- Current test coverage summary
- Gaps identified
- Patterns observed
- Recommendations

**IMPORTANT**:
- DO NOT make code changes
- DO NOT create plans
- ONLY research and document findings
- Output goes to research.md for human review
```

## Human Review Checkpoint #1

After research completes:
1. Claude presents: "Research complete! See `research.md`"
2. You review the findings
3. You decide: approve, request changes, or cancel
4. If approved, proceed to Planning

## Phase 2: Planning

**Goal**: Create detailed implementation plan based on research

**Tools Available**:
- Read() - Read research.md
- Task() - Spawn planning subagents
- Write() - Create plan.md

**Agents for Planning**:
- `typescript-migration-agent.md` - Plan TypeScript conversion
- `cicd-improvement-agent.md` - Plan CI/CD improvements

**Output**: Creates `plan.md` with implementation steps

**Example Planning Agent Structure**:
```markdown
# Planning Agent: Test Coverage Plan

## Phase: Planning
Your job is to create a plan, NOT to implement it.

## Inputs:
- Read `research.md` (created by research agent)

## Steps:
1. Read and analyze research findings
2. Identify what needs to be done
3. Break down into concrete steps
4. Estimate complexity
5. Identify risks

## Output:
Create a file called `plan.md` with:
- Clear implementation steps (numbered)
- Files that need changes
- Dependencies between steps
- Testing strategy
- Rollback plan

**IMPORTANT**:
- DO NOT make code changes
- DO NOT start implementing
- ONLY plan based on research
- Output goes to plan.md for human review
```

## Human Review Checkpoint #2

After planning completes:
1. Claude presents: "Plan complete! See `plan.md`"
2. You review the plan
3. You decide: approve, modify, or cancel
4. If approved, proceed to Implementation

## Phase 3: Implementation

**Goal**: Execute the plan with actual code changes

**Tools Available**:
- Read() - Read plan.md and code files
- Edit() - Modify existing files
- Write() - Create new files
- MultiEdit() - Bulk changes
- Bash() - Run tests, build, etc.

**Agents for Implementation**:
(Most agents can be implementation-focused, or you create specific implementation agents)

**Example Implementation Agent Structure**:
```markdown
# Implementation Agent: Test Coverage Implementation

## Phase: Implementation
Your job is to implement the plan with actual code changes.

## Inputs:
- Read `plan.md` (created by planning agent)
- Read `research.md` (for context)

## Steps:
1. Read and understand the plan
2. For each step in plan.md:
   - Read relevant files
   - Make changes with Edit() or Write()
   - Run tests with Bash()
   - Verify changes work
3. Mark plan steps as completed

## Output:
- Actual code changes
- Test results
- Updated documentation
- Summary of what was done

**IMPORTANT**:
- Follow the plan exactly (unless you find issues)
- If you deviate from plan, explain why
- Run tests after each change
- Report any problems immediately
```

## Organizing Your Agents

### Current Agents by Phase

**Research Agents** (analyze and document):
- ✅ `test-coverage-agent.md`
- ✅ `component-testing-agent.md`
- ✅ `rules-validation-agent.md`
- ✅ `error-handling-agent.md`
- ✅ `api-docs-agent.md`

**Planning Agents** (design and plan):
- ✅ `typescript-migration-agent.md`
- ✅ `cicd-improvement-agent.md`

**Implementation Agents** (execute changes):
- Could create specific ones, or use general implementation approach

**Hybrid Agents** (can do multiple phases):
- `poker-frontend-tester.md` - Testing agent (can research, plan, and implement)

## Example Workflow

### Scenario: Add Authentication to API

**1. Research Phase**
```bash
# User: "Research our current authentication approach"
# Claude spawns: api-docs-agent (research mode)
# Output: research.md with current auth analysis
# [HUMAN REVIEWS research.md]
```

**2. Planning Phase**
```bash
# User: "Create a plan to add JWT authentication"
# Claude spawns: planning agent (reads research.md)
# Output: plan.md with implementation steps
# [HUMAN REVIEWS plan.md]
```

**3. Implementation Phase**
```bash
# User: "Implement the authentication plan"
# Claude spawns: implementation agent (reads plan.md)
# Output: Code changes, tests, docs
# Result: Working authentication
```

## Creating Research-First Agents

When creating new agents, follow this pattern:

```markdown
# Agent Name: [Feature] Agent

## Mode Selection

This agent operates in different modes based on the task:

### Research Mode (Default)
When user says: "research", "analyze", "investigate", "audit"
- Use Glob/Grep to explore codebase
- Use Read to examine files
- Use Task() to spawn subagents
- Output: research.md with findings
- DO NOT make code changes

### Planning Mode
When user says: "plan", "design", "create a plan for"
- Read research.md (if exists)
- Analyze requirements
- Create detailed plan
- Output: plan.md with steps
- DO NOT make code changes

### Implementation Mode
When user says: "implement", "execute plan", "make changes"
- Read plan.md (if exists)
- Make actual code changes with Edit/Write
- Run tests with Bash
- Output: Working code changes

### Auto Mode (All Three Phases)
When user says: "add feature X" or "fix Y"
1. First do research → create research.md
2. Wait for human approval
3. Then do planning → create plan.md
4. Wait for human approval
5. Then implement → make code changes

## Instructions

[Your specific agent instructions here]

**Phase Boundaries**:
- Research phase: MUST output to research.md, NO code changes
- Planning phase: MUST output to plan.md, NO code changes
- Implementation phase: MUST make code changes per plan.md
```

## Benefits of This Pattern

1. **Clear separation of concerns**: Each phase has distinct goals
2. **Human oversight**: You review before code changes happen
3. **Better context**: Each phase builds on previous work
4. **Easier debugging**: If something goes wrong, you know which phase
5. **Reusable artifacts**: research.md and plan.md can be referenced later
6. **Audit trail**: Clear record of decision-making process

## Quick Reference

### When to Use Research Agent
- "What's our current test coverage?"
- "Analyze the authentication flow"
- "Find all API endpoints"
- "Audit error handling"

### When to Use Planning Agent
- "Plan how to add feature X"
- "Design a migration strategy"
- "Create a plan to refactor Y"
- "Plan CI/CD improvements"

### When to Use Implementation Agent
- "Implement the plan from plan.md"
- "Execute the authentication plan"
- "Apply the changes described in plan.md"

## Advanced Patterns

### Multi-Agent Research
```bash
# Spawn 3 research agents in parallel
# Each researches different aspect
# Combine findings into one research.md
```

### Incremental Implementation
```bash
# Break plan.md into chunks
# Implement and test each chunk
# Human review after each chunk
```

### Iterative Refinement
```bash
# Research → Plan → Review
# If plan needs changes, go back to Research
# Research → Updated Plan → Implement
```

## Tool Usage by Phase

| Phase | Task() | Glob/Grep | Read | Edit/Write | Bash |
|-------|--------|-----------|------|------------|------|
| Research | ✅ Spawn subagents | ✅ Search | ✅ Examine | ❌ No code changes | ⚠️ Read-only commands |
| Planning | ✅ Spawn subagents | ⚠️ Light use | ✅ Read research | ✅ Create plan.md only | ❌ No execution |
| Implementation | ⚠️ Rare | ⚠️ Light use | ✅ Read plan & code | ✅ Make changes | ✅ Run tests |

## Next Steps

1. **Review your existing agents** - Which phase does each belong to?
2. **Add phase headers** - Label each agent with its primary phase
3. **Create missing agents** - Do you need more research or planning agents?
4. **Test the workflow** - Try a complete R→P→I cycle
5. **Refine** - Adjust based on what works

## Example: Refactoring an Existing Agent

Before (mixed phases):
```markdown
# Test Coverage Agent
- Analyze tests ← Research
- Create plan ← Planning
- Write tests ← Implementation
```

After (phase-separated):
```markdown
# Test Coverage Research Agent (Phase 1)
- Only analyze and document
- Output: research.md

# Test Coverage Planning Agent (Phase 2)
- Read research.md
- Output: plan.md

# Test Coverage Implementation Agent (Phase 3)
- Read plan.md
- Write actual tests
```

Or use Mode Selection to keep one agent with clear phase boundaries!

---

**Remember**: The key insight is that Research creates knowledge artifacts (research.md, plan.md) that Implementation agents consume. Human review happens at artifact boundaries, giving you control over what gets implemented.

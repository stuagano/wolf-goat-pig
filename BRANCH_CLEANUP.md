# Branch Cleanup Guide

This document lists old branches that have been merged into `main` and can be safely deleted.

## Summary
- **Total merged branches to delete:** 14
- **Unmerged branches to keep:** 3

## Branches to Delete (Already Merged)

### Issue Branches (1)
- `60-the-track-a-live-game-and-scoring-system-isnt-working`

### Claude Branches (4)
- `claude/create-claude-folder-structure-011CULeSLRajtshSmENuszqP`
- `claude/fix-simulation-mode-011CUi3wm8C3JR1iM8Psoyux`
- `claude/simplify-simulation-mode-011CUfXwcTJvZi5ewpmudmRW`
- `claude/simplify-simulation-ui-011CUhbngrC6gvcMTRof2bJf`

### Codex Branches (9)
- `codex/add-new-sign-up-button-and-sync`
- `codex/check-fix-for-issue-48-and-add-rng-for-sunday-game`
- `codex/clean-up-repository-structure`
- `codex/create-agents.md-with-contribution-guidelines`
- `codex/create-branch-for-simulation-mode-development`
- `codex/identify-project-requirements`
- `codex/refactor-feedback-handling-in-simulationmode`
- `codex/refactor-probability-payload-handling-in-simulationmode`
- `codex/update-action-handlers-for-game-state`

## Branches to Keep (Not Yet Merged)
- `claude/eth-token-venmo-integration-011CUheEL1mxnismoQr5EPsc`
- `claude/fix-vercel-routes-011CUheEL1mxnismoQr5EPsc`
- `claude/issue-49-20250829-1334`

## How to Delete Branches

### Option 1: Using GitHub Web UI
1. Go to https://github.com/stuagano/wolf-goat-pig/branches
2. Find each branch listed above
3. Click the trash icon next to each branch

### Option 2: Using Git Command Line (One by One)
```bash
git push origin --delete <branch-name>
```

### Option 3: Using Git Command Line (All at Once)
```bash
# Delete all merged branches
git push origin --delete \
  60-the-track-a-live-game-and-scoring-system-isnt-working \
  claude/create-claude-folder-structure-011CULeSLRajtshSmENuszqP \
  claude/fix-simulation-mode-011CUi3wm8C3JR1iM8Psoyux \
  claude/simplify-simulation-mode-011CUfXwcTJvZi5ewpmudmRW \
  claude/simplify-simulation-ui-011CUhbngrC6gvcMTRof2bJf \
  codex/add-new-sign-up-button-and-sync \
  codex/check-fix-for-issue-48-and-add-rng-for-sunday-game \
  codex/clean-up-repository-structure \
  codex/create-agents.md-with-contribution-guidelines \
  codex/create-branch-for-simulation-mode-development \
  codex/identify-project-requirements \
  codex/refactor-feedback-handling-in-simulationmode \
  codex/refactor-probability-payload-handling-in-simulationmode \
  codex/update-action-handlers-for-game-state
```

### Option 4: Using GitHub CLI
```bash
# Delete branches one by one
gh api repos/stuagano/wolf-goat-pig/git/refs/heads/<branch-name> -X DELETE
```

## Local Cleanup
After deleting remote branches, clean up local references:
```bash
git fetch --prune origin
git branch -vv | grep ': gone]' | awk '{print $1}' | xargs git branch -D
```

## Notes
- All branches listed above have been fully merged into `main`
- Their changes are preserved in the main branch history
- Deleting these branches will not affect any code or commit history
- This cleanup will make the repository easier to navigate

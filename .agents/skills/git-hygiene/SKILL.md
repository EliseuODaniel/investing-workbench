---
name: git-hygiene
description: Use when creating branches, staging changes, committing, pushing, or reconciling local work in this repository and you want safe Git practices: inspect the worktree first, avoid destructive commands, make reviewable commits, and push intentionally.
---

# Git Hygiene

## Before touching Git state

- Start with `git status --short`.
- Use `git diff --stat` or targeted diffs before staging.
- Assume the worktree may contain unrelated user changes.
- Never revert or discard unrelated edits unless the user explicitly asks.

## Safe habits

- Prefer non-interactive commands.
- `main` is currently the canonical consolidated branch for this repo; use topic branches with the `codex/` prefix only when the task calls for a review branch or PR flow.
- Stage only intentional files.
- Re-check the staged diff before committing.
- Keep commits small enough to explain in one paragraph.
- Keep downloaded datasets, local caches, workspaces, and generated artifacts out of commits unless they are deliberate fixtures.

## Commands to avoid by default

- `git reset --hard`
- `git checkout -- <path>`
- force-push
- amend/rebase flows that rewrite someone else's expected history

Use them only when the user clearly asked for that outcome.

## Push and share checklist

- Run the relevant tests before committing.
- Confirm the branch name matches the task scope.
- Check `git branch -vv` and `git branch -r` before branch cleanup.
- Push only after the local diff, staged diff, and test results all make sense together.
- In the final summary, say what was pushed and whether anything remains local-only.

---
name: "docs-sync"
description: "Compare documentation against code and update the docs so they reflect the current implementation."
---

# Docs Sync

## Workflow
1. Identify the commands, endpoints, or behaviors changed by the task.
2. Compare README and docs against the code.
3. Update only the relevant sections.
4. Call out any known gaps that remain intentionally unresolved.

## Canonical Docs To Check
- `PLANS.md`: short-horizon active plan.
- `docs/PROJECT_STATUS_AND_DIRECTION.md`: concise project status and direction.
- `docs/CODEX_HANDOFF.md`: resume point for future Codex sessions.
- `docs/FINAL_STATUS.md`: validation and delivered capability snapshot.
- `docs/MASTER_PLAN.md`: longer execution plan and phase gates.
- `README.md`: user-facing overview and quick start.

## Current Drift Risks
- Old `bitcoin-martingale` or crypto-first language in docs that should now say **Investing Workbench**.
- Fixed-income results described as recommendations instead of methodology-specific historical comparisons.
- Docs that explain implementation details but do not explain the user decision being supported.
- Planning notes that add power without preserving didactic simplicity and good UX.
- Commands that use `.venv` directly instead of `uv`.
- Docs that say the worktree is dirty when `main` is actually synchronized.

---
name: "repo-explorer"
description: "Summarize the repository structure, entry points, validation commands, and notable risks before implementation."
---

# Repo Explorer

## Use when
- Starting work in an unfamiliar part of the repository
- Preparing onboarding notes
- Checking what changed structurally after refactors

## Workflow
1. Map top-level directories and important files.
2. Identify backend, frontend, configs, docs, and tests.
3. List canonical commands to run, build, lint, and test.
4. Call out surprising areas, generated artifacts, and risks.
5. Check `PLANS.md` and `docs/PROJECT_STATUS_AND_DIRECTION.md` before interpreting current direction.

## Current Repo Shape
- `Investimentos` is the main product surface.
- `frontend/src/components/InvestmentsWorkspace.tsx` and `src/investing_workbench/application/investments/service.py` are the main modularization hotspots.
- `frontend/src/components/investments/` and `src/investing_workbench/application/investments/narratives.py` contain the first extracted investment decision/methodology modules.
- `src/investing_workbench/application/investments/decision_profile.py` contains the investor-profile normalization used by decision guidance.
- `data/`, `pairs_backtests/`, `research_workspaces/`, and downloaded fixed-income caches are usually runtime artifacts.
- Product direction prioritizes didactic simplicity and good user experience before adding more visible complexity.

## Output
- Keep it concise.
- Include paths to the most important files.
- Call out whether the area being explored supports or hurts the simple didactic user journey.

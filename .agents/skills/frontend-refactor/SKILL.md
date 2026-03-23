---
name: "frontend-refactor"
description: "Refactor the frontend by extracting hooks and feature modules without breaking the existing UI flow."
---

# Frontend Refactor

## Goals
- Reduce the size and responsibility of `frontend/src/App.tsx`.
- Keep API contracts typed and easy to trace.

## Workflow
1. Identify state or logic that can move to a hook.
2. Extract feature-specific concerns first.
3. Add a focused test for the extracted logic when practical.
4. Run lint, tests, and build.

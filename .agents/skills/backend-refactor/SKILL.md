---
name: "backend-refactor"
description: "Refactor backend code incrementally toward service-oriented layers while preserving current behavior."
---

# Backend Refactor

## Goals
- Move orchestration out of route handlers and CLIs.
- Keep domain logic decoupled from HTTP and UI concerns.

## Workflow
1. Identify the smallest unit of business logic to extract.
2. Create or extend `src/investing_workbench/application/`.
3. Keep legacy modules as adapters when needed.
4. Add or update backend tests for behavior changes.
5. Run backend checks after changes.

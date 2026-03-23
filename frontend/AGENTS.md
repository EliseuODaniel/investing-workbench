# Frontend Area Guide

## Scope
- The frontend should move toward a feature-oriented structure over time.
- Prefer extracting hooks and focused components instead of expanding `src/App.tsx`.

## Rules
- Keep UI state close to the feature that owns it.
- Use typed API contracts from `src/types/api.ts`.
- Add Vitest coverage for new utility logic and key UI flows.
- Do not depend on generated backend artifacts in the UI.

## Validation
- Run `npm run lint`
- Run `npm test -- --run`
- Run `npm run build`

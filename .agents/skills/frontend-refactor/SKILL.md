---
name: "frontend-refactor"
description: "Refactor the frontend by extracting hooks and feature modules without breaking the existing UI flow."
---

# Frontend Refactor

## Goals
- Reduce the size and responsibility of `frontend/src/App.tsx`.
- Reduce the size and responsibility of `frontend/src/components/InvestmentsWorkspace.tsx`.
- Keep API contracts typed and easy to trace.
- Keep `Investimentos` simple for non-technical users while allowing advanced controls to live behind tabs or focused sections.
- Preserve or improve didactic UX: one clear question per screen, plain-language labels, readable charts, and progressive disclosure for advanced controls.

## Workflow
1. Identify state or logic that can move to a hook.
2. Extract feature-specific concerns first.
3. Add a focused test for the extracted logic when practical.
4. Check that the default path is easier to understand after the refactor, not merely smaller in code.
5. Run lint, tests, and build.

## Current Extraction Targets
- Investment setup tabs, review summary, and result tab composition.
- Fixed-income summary and methodology explanations, building on `frontend/src/components/investments/InvestmentMethodologyPanel.tsx`, `FixedIncomeDecisionGuidePanel.tsx`, and `PortfolioObjectiveSummaryPanel.tsx`.
- Decision-profile controls, building on `frontend/src/components/investments/InvestmentDecisionProfileForm.tsx`.
- Chart utilities, legend state, date range controls, and tooltip behavior.
- Custom portfolio controls and benchmark selection.

## UX Guardrails
- Do not put every available option on the first visible screen.
- Prefer tabs, summaries, and focused result views over long stacked forms.
- Keep chart interactions discoverable and visually calm.
- Avoid wording that turns a historical winner into a current investment recommendation.

## Suggested Commands
- `cd frontend && npm test -- --run src/components/InvestmentsWorkspace.test.tsx`
- `cd frontend && npm test -- --run src/hooks/useChartDateRange.test.tsx src/hooks/useSeriesLegendState.test.tsx`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

# Active Plans

## Sprint 1
- Prepare the repository for reliable Codex collaboration.
- Add modern Python tooling and a clear project root.
- Introduce the first `src/investing_workbench` application service layer.
- Fix API error handling and align tests.
- Add the first frontend lint/test scaffolding that actually runs.

## Current Product Direction
- Position the app as **Investing Workbench**, not only as a martingale backtester.
- Keep `Investimentos` as the didactic entry point for comparing B3-oriented investments and guided portfolios.
- Keep `Simular` for strategy backtests and `Avancado` for research workflows.
- Prefer simple investor-first UX in the main product and push technical density deeper into advanced areas.

## Migration Guardrails
- The existing `src/` runtime remains valid until the new architecture is feature-complete.
- Migrate behavior through adapters, not rewrites.
- Preserve YAML config compatibility during the migration.

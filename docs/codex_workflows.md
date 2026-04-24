# Codex Workflows

## Repository-Level Guidance
- Use the root `AGENTS.md` for shared repo rules.
- Add scoped `AGENTS.md` files when a subdirectory has special constraints.
- Use `.agents/skills/` for repeatable workflows that deserve reusable instructions.

## Recommended Repo-Local Skills
- `repo-explorer`
- `software-engineering-guardrails`
- `backend-refactor`
- `frontend-refactor`
- `backtest-validation`
- `docs-sync`
- `git-hygiene`

## Recommended MCPs
- `openaiDeveloperDocs` for official OpenAI and Codex docs
- `context7` for library documentation lookups
- `playwright` for browser automation and UI checks
- `github` for issue and PR workflows when the repo is hosted remotely

## Suggested OpenAI MCP Command
- `codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp`

## Working Pattern
1. Start with a short plan.
2. Explore the relevant area of the repo.
3. Implement small, reviewable changes.
4. Run the smallest reliable validation loop.
5. Summarize what changed, what was verified, and any residual risk.

## Current Project Bias
- Treat `Investimentos` as the main product surface and keep advanced research density behind deeper sections.
- Before expanding asset coverage, confirm the methodology, assumptions, and user-facing explanation are clear.
- Prefer didactic, simple, low-friction user flows over exposing every technical option by default.
- Use progressive disclosure: beginner screens should clarify decisions, while advanced controls should remain reachable without dominating the main path.
- Use `docs/PROJECT_STATUS_AND_DIRECTION.md` and `PLANS.md` as the current planning pair.
- Keep local runtime artifacts out of commits unless they are intentional fixtures.

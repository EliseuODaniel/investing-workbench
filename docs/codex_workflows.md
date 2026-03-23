# Codex Workflows

## Repository-Level Guidance
- Use the root `AGENTS.md` for shared repo rules.
- Add scoped `AGENTS.md` files when a subdirectory has special constraints.
- Use `.agents/skills/` for repeatable workflows that deserve reusable instructions.

## Recommended Repo-Local Skills
- `repo-explorer`
- `backend-refactor`
- `frontend-refactor`
- `backtest-validation`
- `docs-sync`

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

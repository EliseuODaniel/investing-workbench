# Test Area Guide

## Goals
- Prefer small, deterministic tests.
- Cover domain behavior, API contract behavior, and regression-prone calculations.

## Rules
- Add tests for real bugs before or alongside fixes.
- Prefer explicit fixtures over hidden shared state.
- Keep backtest regression tests focused on observable outputs: trades, equity, metrics, and status codes.

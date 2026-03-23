# Code Review Guide

## Primary Focus
- Correctness of backtest behavior
- Numerical and metrics regressions
- API contract stability
- Missing validation or error handling
- Missing tests for behavior changes

## Review Checklist
- Does the change alter trades, fills, or metrics?
- Are status codes and error messages preserved or intentionally changed?
- Is business logic placed in the correct layer?
- Are generated artifacts and caches kept out of version control?
- Were the relevant checks run?

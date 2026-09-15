# Milestone Plan

This document maps the repository history to delivery milestones. The commit
ranges below describe the intended boundaries; use the same commit subjects
when selecting ranges in the review workflow.

| Milestone | Commit Range | Independent Goal | Acceptance Check |
| --- | --- | --- | --- |
| M1 Engineering foundation | Project skeleton through environment settings | Define package metadata, domain models, and configuration without delivery code | `python -m compileall -q src` succeeds and domain normalization is deterministic |
| M2 Persistence | SQLite repository and schema commits | Persist candidates, jobs, and match results with foreign keys | Repository CRUD tests pass on a fresh SQLite database |
| M3 Parsing and matching | Resume parser and matching engine commits | Convert resume text into candidates and produce explainable scores | Parser and matcher unit tests cover valid, empty, and invalid input |
| M4 API and operations | HTTP endpoints, CLI, and demo data commits | Expose a complete local workflow over JSON and the command line | HTTP integration and CLI tests pass |
| M5 Quality and delivery | Integration fixes, tests, CI, and Docker commits | Lock in thread-safe API behavior and reproducible delivery | Full test suite and `compileall` pass in CI and Docker |
| M6 Documentation | README, API reference, requirements, and milestone commits | Make the implemented behavior discoverable and reviewable | README commands and API reference match the current code |

## Suggested Future Work

1. Add OCR fallback and timeout handling in `services/parser.py`.
2. Make matching weights configurable per job family in `services/matcher.py`.
3. Add authentication, authorization, and tenant isolation in `api/server.py`.
4. Move parsing and matching to a background queue with retry and dead-letter handling.
5. Add structured logging, request tracing, and match-time metrics.

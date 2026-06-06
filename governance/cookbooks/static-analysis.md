# Static Analysis Cookbook

## Purpose

Use analysis tools to find candidates, not final conclusions.

## Inputs

- Existing reports: coverage, lint, dependency audit, Sonar/Snyk/Dependabot.
- Project-defined commands: lint, typecheck, test, audit.
- Language-specific configured tooling already present in the repo.

## Procedure

1. Read existing reports first.
2. In `herramientas`, run configured commands only with authorization.
3. Convert findings into candidates.
4. Validate candidates against evidence of change cost before debt classification.

## Evidence Value

| Finding | Register in |
|---|---|
| Lint/type errors | `evidence/code.md` |
| Low/absent coverage in critical module | `evidence/specialized/qa.md`; debt only in `profundo` if change cost is evidenced |
| Dependency CVE | `evidence/specialized/security.md`; debt only if update is costly due to artifact |
| Complexity/hotspot | candidate; needs change-cost evidence |

## Continue

If tools are absent, record absence only if relevant to quality confidence. Do not install tools unless authorized.

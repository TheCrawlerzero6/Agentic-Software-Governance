# Project Commands Cookbook

## Purpose

Use project-defined commands as optional verification evidence, only when permissions allow.

## Detection

Inspect manifests and scripts:

- Node: `package.json`, lockfiles.
- Python: `pyproject.toml`, `requirements.txt`, `tox.ini`, `pytest.ini`.
- Java/Kotlin: `pom.xml`, `build.gradle`.
- Go: `go.mod`.
- Rust: `Cargo.toml`.
- Make: `Makefile`.

## Procedure

1. In `seguro`, only read manifests and record available scripts.
2. In `herramientas`, ask authorization before running tests/lint/build/typecheck.
3. Prefer existing scripts over invented commands.
4. Record command, purpose, result, and affected source file.

## Evidence Value

| Command type | What it supports | Register in |
|---|---|---|
| test | coverage/quality confidence | `evidence/code.md` and potential gaps in `evidence/specialized/qa.md` |
| lint/typecheck | code quality/config constraints | `evidence/code.md` |
| build | deployment/runtime confidence | `evidence/code.md` |
| format check | style tooling existence | `evidence/agents.md` if rules mention style |

## Limits

Do not install dependencies or run mutating formatters unless the user explicitly asks for implementation work.

## Continue

If commands cannot run, record why and continue. Failed or unavailable commands are evidence, not blockers by default.

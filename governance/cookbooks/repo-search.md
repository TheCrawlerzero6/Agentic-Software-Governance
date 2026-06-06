# Repo Search Cookbook

## Purpose

Build the local evidence map without running project code.

## Procedure

1. List files with `rg --files` when available.
2. Exclude generated/vendor/governance folders: `.git`, `.governance`, `governance`, `node_modules`, `dist`, `build`, `.next`, `.venv`, `target`, `coverage`.
3. Identify stack from manifests before interpreting structure.
4. Search each pyramid layer separately and register findings in the matching source file.

## Search Targets

| Layer | Look for | Register in |
|---|---|---|
| Code | manifests, entrypoints, modules, tests, config, DB/migrations, clients, SDKs | `evidence/code.md` |
| Documentation | README, docs, architecture, ADR/MADR, runbooks, setup | `evidence/documentation.md` |
| Versioning | git availability, history, hotspots, reverts | `evidence/versioning.md` |
| Agents | AGENTS.md, `.agents`, prompts, rules, hooks, config | `evidence/agents.md` |

## Useful Patterns

- Entry points: `main`, `app`, `server`, `route`, `worker`, `cli`, `handler`.
- Config: `.env.example`, `config`, `settings`, `compose`, `Dockerfile`.
- Persistence: `migration`, `schema`, `model`, `repository`, `prisma`, `typeorm`.
- SATD: `TODO`, `FIXME`, `HACK`, `WORKAROUND`, `XXX`, `temporary`, `quick fix`.

## Continue

If a target is absent, write `no encontrado`, where you searched, effect, and continuity. Absence does not block the next layer.

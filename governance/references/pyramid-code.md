# Pyramid: Code

Use this layer to understand executable reality.

Read `references/arc42-reducido.md` before summarizing this layer.

## Inspect

- Repository structure and top-level manifests.
- Entry points: apps, CLIs, servers, route handlers, workers, scheduled jobs.
- Modules and boundaries.
- Tests and coverage indicators.
- Configuration: env examples, config files, secrets patterns without reading secrets.
- Dependencies and lockfiles.
- Persistence: DB schemas, migrations, ORM models.
- External integrations: clients, SDKs, webhooks, queues.
- Error handling, logging, auth, permissions, validation.

## Evidence To Record

- What components exist and where.
- What flows appear critical.
- What dependencies/configuration shape system behavior.
- What tests exist or are absent.
- What risks or debt signals are visible, without formal scoring in `normal`.

## Arc42 Mapping

| Code evidence | Source section | `system-context.md` section |
|---|---|---|
| Entrypoints, apps, packages | elements/building blocks | purpose, building blocks |
| Routes, handlers, jobs, CLIs | flows | flows |
| Config/env/scripts/manifests | restrictions/config | restrictions, deployment/configuration |
| Auth/logging/errors/validation | concepts/restrictions | cross-cutting concepts |
| Tests/coverage absence | risks/questions | quality, risks, limitations |
| Imports, clients, SDKs, DB models | elements/building blocks | context, building blocks, restrictions |

## Continue If Missing

- If tests are absent, record the absence as a risk/signal and continue.
- If entrypoints are unclear, record candidate entrypoints and a question.
- If config references secrets, record variable names only, not values.

## Do Not Overclaim

- Code proves current behavior shape, not original intent.
- A TODO is only a signal.
- Complexity is not debt unless it increases change cost.
- Missing tests are a risk; formal test debt requires `profundo` evidence.

## Register In

- `governance/system-context.md`
- `governance/evidence/code.md`
- `governance/decisions.md` for decision candidates
- `governance/technical-debt.md` only in `profundo`

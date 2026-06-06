# Pyramid: Documentation

Use this layer to understand declared intent.

Read `references/arc42-reducido.md` before updating `system-context.md`.

## Inspect

- README files.
- `docs/`, architecture notes, runbooks, diagrams.
- Existing ADRs/MADRs.
- Setup, deployment, operations, and onboarding docs.
- API docs and domain glossaries.
- Explicitly declared risks, known limitations, TODOs, and debt.

## Compare

- Documentation versus code.
- Documentation versus decisions.
- Documentation versus agent rules.
- Setup instructions versus actual manifests/scripts.

## Evidence To Record

- Declared purpose and scope.
- Declared architecture and flows.
- Dependencies or integrations named in docs.
- Decisions that are explicit.
- Contradictions or stale documentation.
- Missing docs for critical behavior.

## Arc42 Mapping

| Documentation evidence | Source section | `system-context.md` section |
|---|---|---|
| README purpose/setup | context/elements | purpose, scope, restrictions |
| Architecture docs/diagrams | building blocks/flows | context, building blocks, flows |
| ADR/MADR files | decisions | decisions existing |
| Runbooks/deploy docs | restrictions/config | deployment/configuration, concepts |
| Glossary/domain docs | context | glossary |
| Stale or missing docs | contradictions/questions | limitations, risks |

## Continue If Missing

- If no README/docs exist, write `no encontrado`, where you searched, impact, and continue.
- If docs conflict with code, record both; do not choose a winner unless evidence is direct.
- If docs mention external docs outside the repo, ask later only if needed to close a decision or criticality gap.

## Do Not Overclaim

- Outdated docs are evidence of contradiction, not proof of current behavior.
- If docs and code conflict, record both and mark impact.
- Do not invent intent; mark missing or ask later.

## Register In

- `governance/evidence/documentation.md`
- `governance/system-context.md`
- `governance/decisions.md`

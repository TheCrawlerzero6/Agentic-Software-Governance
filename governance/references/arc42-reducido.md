# Arc42 Reducido

Use arc42 reducido as the shared method for `system-context.md` and every `evidence/*.md` review. It is not a full architecture document; it is a minimum evidence map that lets the agent continue the governance flow.

## Reduced Views

1. Proposito: what the system appears to do.
2. Alcance: what was reviewed, excluded, or unavailable.
3. Stakeholders: users, operators, teams, managers, agents, or external systems.
4. Restricciones: language, framework, provider, infrastructure, security, operations, compliance, permissions.
5. Contexto: actors, inputs, outputs, integrations, external services.
6. Building blocks: modules, apps, services, packages, workers, data stores, boundaries.
7. Flujos: technical or business workflows crossing blocks, including trigger/input, output, modules, business rule, evidence, confidence, and questions.
8. Despliegue/configuracion: Docker, scripts, env names, databases, queues, runtime, CI/CD hints.
9. Conceptos transversales: auth, persistence, logging, validation, errors, permissions, retries, scraping, caching, observability.
10. Decisiones existentes: documented or inferred choices found while reviewing.
11. Calidad/riesgos/deuda declarada: risks, TODO/FIXME, known limitations, declared debt.
12. Glosario: domain or technical terms needed to understand the system.
13. Limitaciones: unavailable sources, weak evidence, unverified assumptions.

## Source-To-Arc42 Mapping

| Evidence | Write in source file | Update in `system-context.md` |
|---|---|---|
| Repo structure, manifests, entrypoints | `evidence/code.md` sections 1-7 | purpose, building blocks, flows, restrictions |
| Config, env examples, Docker, scripts | `evidence/code.md` or `evidence/documentation.md` | deployment/configuration, restrictions |
| README/docs/ADRs/runbooks | `evidence/documentation.md` | purpose, context, decisions, glossary |
| Git commits/reverts/hotspots | `evidence/versioning.md` | decisions, risks, limitations |
| AGENTS/rules/prompts/skills | `evidence/agents.md` | stakeholders, restrictions, decisions |
| Missing or contradictory evidence | source file sections 9-10 | limitations, risks, questions |

## How To Write Each View

- Prefer tables for blocks, flows, decisions, contradictions, and questions.
- Every non-obvious statement needs an evidence pointer: path, doc, command, commit, or `governance/` file.
- Use confidence `alta`, `media`, or `baja`.
- Use `inferido` when evidence suggests intent but does not prove it.
- Use `no encontrado` when a source or expected artifact is absent.

## Update Triggers

Update `system-context.md` when:

- a significant block is found;
- a flow becomes clearer;
- a critical dependency/configuration appears;
- documentation changes the interpretation;
- user feedback corrects an inference;
- confidence changes;
- a limitation or contradiction affects the report.

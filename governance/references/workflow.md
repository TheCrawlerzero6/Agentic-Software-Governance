# Workflow

## Goal

Create an evidence-backed governance base for an existing repository. The review answers what the system does, how it is organized, what evidence exists, which decisions can be reconstructed, what is missing or contradictory, what specialized signals may require expert review, and what actions should be considered.

## Inputs

- Depth: `normal` or `profundo`.
- Audience: `tecnico` or `jefatura`.
- Permissions: `seguro` or `herramientas`.
- Scope: repo completo, module, folder, or flow.
- Recursos disponibles: repositorio local, historial local, repositorio remoto, documentacion externa, verificacion local, entorno local, reportes existentes, revision especializada.

Ask for missing initial inputs before writing `governance/`.

Audience is used only when writing the final report. It must not change the evidence workflow, source order, confidence, impact, debt classification, questions, or recommendations.

## Modes

`normal` includes context, source review, specialized potential evidence, decision reconstruction, contradictions, questions, and action register. It does not include formal technical debt scoring.

`profundo` includes normal mode plus formal technical debt evaluation, litmus-test classification, qualitative prioritization where evidence allows, and `technical-debt.md`.

## User-Visible Checklist

1. Preparar revision: create/update `governance-config.md`.
2. Explorar base: run `prescan_evidence.py` to seed evidence without executing project tools.
3. Entender sistema: build `system-context.md` using `arc42-reducido.md`.
4. Revisar evidencia: code, documentation, versioning, agents.
5. Registrar evidencia especializada potencial in `evidence/specialized/`.
6. Reconstruir decisiones in `decisions.md`.
7. Preguntar solo por huecos that affect evidence, decision, debt, specialist interpretation, or action.
8. Evaluar deuda only in `profundo`: require technical construct, scenario of change, interest when changed, evidence, and management decision.
9. Cerrar revision: fill `action-register.md` with structured context questions, then validate with `--strict`.
10. Generate Markdown report or PDF only when requested or when producing a closure summary.

## Resource Categories

| User-facing resource | Internal use | Evidence target |
|---|---|---|
| Repositorio local | file search, manifests, configs | `evidence/code.md`, `evidence/documentation.md` |
| Historial local | read-only git | `evidence/versioning.md`, `decisions.md` |
| Repositorio remoto | PRs, issues, releases, roadmap when already authorized | `evidence/versioning.md`, `decisions.md` |
| Documentacion externa | existing connectors or knowledge sources | `evidence/documentation.md` |
| Verificacion local | tests, lint, build, typecheck when authorized | `evidence/code.md`, `evidence/specialized/qa.md` |
| Entorno local | Docker/Compose, local services, logs when authorized | `evidence/code.md`, `system-context.md` |
| Reportes existentes | CI, coverage, dependency, quality reports | `evidence/code.md`, `evidence/specialized/` |
| Revision especializada | available skills/plugins or human specialist | `evidence/specialized/` |

## Progress Gates

- Do not review debt before `decisions.md` exists.
- Do not generate a closure report before validation.
- Do not skip pre-scan; if it cannot run, document why in `evidence/*` and continue manually.
- Do not convert a signal into debt without evidence of future change cost.
- Do not treat inferred decisions as truth until confirmed.
- Do not add findings to the report if they are not already present in `governance/`.
- Do not stop on missing optional evidence. Record `no encontrado`, confidence, continuity reason, and proceed.
- Do not leave `system-context.md` stale after a source review changes purpose, blocks, flows, restrictions, decisions, risks, or limitations.
- Do not assert specialized findings as confirmed unless direct evidence exists.
- Do not ask insight questions without context: each one must name missing context, affected flow, current evidence, and why the answer matters.
- Use `change-log.md` for intervention/change decisions only; keep inferred system decisions in `decisions.md`.

## IDs

- `CTX-001`: context item.
- `CODE-001`: code evidence.
- `DOC-001`: documentation evidence.
- `VER-001`: versioning evidence.
- `AGT-001`: agent/rule evidence.
- `SEC-POT-001`: potential security evidence.
- `QA-POT-001`: potential QA evidence.
- `DATA-POT-001`: potential data evidence.
- `PERF-POT-001`: potential performance evidence.
- `COMP-POT-001`: potential compliance evidence.
- `DEC-001`: decision.
- `TD-001`: technical debt.
- `ACT-001`: actionable insight.

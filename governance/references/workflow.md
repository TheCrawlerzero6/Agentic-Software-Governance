# Workflow

## Goal

Create an evidence-backed governance base for an existing repository. The review answers what the system does, how it is organized, what evidence exists, which decisions can be reconstructed, what is missing or contradictory, what specialized signals may require expert review, and what actions should be considered.

## Inputs

- Depth: `normal` or `profundo`.
- Audience: `tecnico` or `jefatura`.
- Permissions: `seguro` or `herramientas`.
- Scope: repo completo, module, folder, or flow.
- Recursos disponibles: repositorio local, historial local, repositorio remoto, documentacion externa, verificacion local, entorno local, reportes existentes, revision especializada.

Ask for missing initial inputs before writing `governance/`. Use `request_user_input` in batches of at most 3 questions. If that tool is unavailable, stop before the decision and ask for a selection-capable interaction.

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
6. Reconstruir decisiones in `decisions.md`; infer from consistent evidence without asking when the panorama is clear.
7. Preguntar solo por huecos that cannot be resolved from written evidence and affect evidence, decision, debt, specialist interpretation, or action.
8. Evaluar deuda only in `profundo`: require technical construct, scenario of change, interest when changed, evidence, and management decision.
9. Registrar insights: fill `action-register.md` with structured actionable insights.
10. Validar base de revision with `--strict`.
11. Seleccionar insights: show actionable insights with `request_user_input`.
12. Correccion segura: only after user choice, record safe correction, postponement, discard, or specialist handoff.
13. Revalidar after selected actions.
14. Cerrar revision: ask with `request_user_input` whether to generate Markdown report, Markdown plus PDF, or close without report.
15. Generate Markdown report or PDF only after insight decisions are closed.

## Question Protocol

- Initial setup questions cover only depth, audience, permissions, scope, available resources, and specialized-review support.
- Use `request_user_input` for every critical choice. Do not use `#question`, free text, or an optionless question tool for critical choices.
- Batch 1: depth, audience, permissions.
- Batch 2: scope, resource profile, specialized-review support.
- Ask at most 3 `request_user_input` questions per call and every question must have valid `options`.
- Use plain text only for non-decision details after a choice is made, such as an exact folder path for a selected folder/module scope.
- Later questions are allowed only when the answer changes evidence, decision, debt, specialist handoff, action, or continuity.
- Every later question must name missing context, affected flow, current evidence, and why the answer matters.
- During decision reconstruction, analyze first and ask only if human context can change the interpretation. If evidence is sufficient, write `Pregunta pendiente: no necesaria`.
- For insight selection, use `request_user_input`: `Corregir seguro`, `Posponer`, `Descartar`, `Requiere especialista`.
- For correction authorization, use `request_user_input`; do not treat insight selection as blanket permission for unrelated edits.
- For report closure, use `request_user_input`: `Generar reporte Markdown`, `Generar Markdown + PDF`, `Cerrar sin reporte`.
- If `request_user_input` is unavailable for insight, correction, handoff, or closure decisions, stop and ask for a selection-capable interaction instead of continuing through ambiguous free text.

## Insight Selection And Safe Correction

- The base review ends by writing `action-register.md`; it does not imply permission to change source code.
- Insights start as `pendiente de decision`.
- Do not generate a final report while any actionable insight remains `pendiente de decision`.
- If the user selects `Corregir seguro`, record authorized scope before edits and update `change-log.md`, `interventions/ACT-XXX.md`, and `action-register.md` after the correction.
- If the user selects `Posponer`, record the reason and expected revisit trigger.
- If the user selects `Descartar`, record the reason and evidence used.
- If the user selects `Requiere especialista`, record the handoff target if available. For `SEC-POT-*`, never correct directly from this skill.
- Revalidate after selected insight outcomes before final report generation.

## Low-Noise Execution

- Prefer script `--quiet` mode for routine execution.
- Store detailed command output and file-level evidence in `governance/`, not in chat.
- Chat updates should report only phase, blocker, required authorization, or compact result.
- Do not paste full stdout, long inventories, diffs, repeated commands, or file-by-file change logs into chat unless explicitly requested.
- Platform-level traces such as thought timing, tool-call metadata, OpenCode task panels, and client UI events may still be shown by the client; this workflow only controls skill/script output and agent summaries.

## Single-Agent Execution

- Use one responsible agent for the full review.
- Do not install, configure, or invoke subagents, plugins, MCP servers, or specialized tools from this workflow.
- If a relevant tool, skill, plugin, MCP, or specialist channel is already available and authorized, record it as a possible handoff/support resource. If it is not available, write `no disponible` and continue with local evidence.
- Background execution means long-running commands or checks may run as background sessions when the runtime supports it; it does not mean delegating decisions or review ownership to another agent.
- Do not use ad hoc heredoc scripts to rewrite `governance/`; use bundled scripts with `--quiet` for deterministic operations.

## Path Policy

- Write paths relative to the reviewed `--root`.
- Use `.` for the reviewed root.
- Use `governance/...` for generated governance files.
- Do not write absolute machine paths such as `/home/...` or `/tmp/...`.
- If a path is outside `--root`, write `fuera del alcance revisado`.

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
- Do not generate a closure report while `action-register.md` contains actionable insights pending user decision.
- Do not skip pre-scan; if it cannot run, document why in `evidence/*` and continue manually.
- Do not convert a signal into debt without evidence of future change cost.
- Do not treat inferred decisions as truth until confirmed.
- Do not add findings to the report if they are not already present in `governance/`.
- Do not stop on missing optional evidence. Record `no encontrado`, confidence, continuity reason, and proceed.
- Do not leave `system-context.md` stale after a source review changes purpose, blocks, flows, restrictions, decisions, risks, or limitations.
- Do not assert specialized findings as confirmed unless direct evidence exists.
- Do not ask insight questions without context: each one must name missing context, affected flow, current evidence, and why the answer matters.
- Do not ask about inferred decisions when written evidence is consistent enough to support the inference.
- Do not batch more than 3 `request_user_input` questions, and never omit options.
- Do not use `#question` or free text for critical choices.
- Use `change-log.md` for intervention/change decisions only; keep inferred system decisions in `decisions.md`.
- Use `interventions/ACT-XXX.md` for each selected insight that is corrected, postponed, discarded, or handed off.

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

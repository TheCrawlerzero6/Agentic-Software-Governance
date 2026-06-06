# Validation Checklist

## Configuration

- `governance-config.md` declares scope, depth, audience, permissions, resources available, and checklist state.
- Operational rules match the selected mode.
- Scope and exclusions are clear.
- Credential handling is documented.

## Evidence Pyramid

- `prescan_evidence.py` was run, or inability to run it is documented in evidence files.
- `system-context.md` exists and contains real evidence.
- `system-context.md` follows arc42 reducido sections.
- `system-context.md` records flows with input, output, modules, business rule, evidence, confidence, and questions when known.
- `evidence/code.md` records code structure, entry points, config, tests, dependencies, or absence.
- `evidence/documentation.md` records docs found, docs missing, and doc/code contradictions.
- `evidence/versioning.md` records git evidence or states that no valid git repo exists.
- `evidence/agents.md` records agent rules or their absence.
- Each reviewed or partial evidence file has `Resumen util` with information that changes understanding, decision, risk, debt, or action.
- Evidence findings include evidence and confidence; avoid generic inventory without impact or destination.
- Inferences have confidence.
- Missing sources are documented as `no encontrado` with search scope and continuity reason.

## Specialized Evidence

- `evidence/specialized/` exists with index, security, QA, data, performance, and compliance files.
- Specialized entries are written as potential unless direct evidence confirms them.
- Every specialized signal has evidence and an action suggested.
- Specialized evidence is not copied into technical debt unless artifact and change cost are documented.
- Security signals use handoff language only: specialized review or available skill/plugin, not direct correction.
- QA signals use general checks only unless a QA-specific skill/plugin is available.

## Decisions

- `decisions.md` separates documented, inferred, missing, and contradictory decisions.
- `decisions.md` separates system decisions from intervention/change decisions; intervention decisions belong in `change-log.md`.
- Inferred decisions have confidence and a pending validation question.
- ADR retrospective entries are suggestions, not final ADRs.
- User questions are tied to evidence.

## Technical Debt

- `normal`: no formal TD entries or scoring.
- `profundo`: every TD item passes the litmus test: technical construct, scenario of change, interest when changed, evidence, and management decision.
- Debt classification separates bugs, vulnerabilities, missing features, QA gaps, and process problems unless a technical construct raises change cost.
- Probable or low/medium-confidence debt records include missing context and a concrete user question.
- Prioritization records interest, interest probability, cost of not paying, payment cost/principal, benefit of payment, maintainability/evolution impact, confidence, and estimated priority.
- Accepted debt has a reason, review date, and management decision instead of being treated as forgotten debt.

## Actions

- `action-register.md` recommendations cite evidence.
- `action-register.md` questions include missing context and affected flow.
- Each insight has a concrete next action or explicit decision state.
- `change-log.md` exists for intervention decisions; it may be empty during the base review.

## Report

- Report declares the configured audience.
- Audience affected only presentation, not process, evidence, confidence, impact, debt, or recommendations.
- Report starts with `Lectura rapida`, `Semaforo de gobernanza`, and `Decisiones o preguntas que requieren atencion`.
- Report cites `governance/` files.
- Report separates confirmed findings, potential specialized evidence, technical debt, and actions.
- Report does not introduce new findings.
- Generated PDFs are written under `governance/reports/generated/`.

# Report Writing

Use this reference only when writing `governance/reports/governance-report.md`.

## Non-Negotiable Rule

Audience changes presentation only. It must not change:

- workflow steps;
- source review order;
- evidence thresholds;
- confidence;
- impact;
- questions;
- decision status;
- technical debt classification;
- recommendations.

The report must declare the configured audience from `governance/governance-config.md` and cite `governance/` files for every relevant conclusion.

## Shared Rules

- Write the report after strict validation passes.
- Use only findings already recorded in `governance/`.
- Keep inferred items marked as inferred.
- Keep absences as evidence when the search scope is documented.
- Do not hide low-confidence findings; explain their confidence.
- Do not create new decisions, debt items, risks, specialized signals, or recommendations in the report.
- Separate confirmed findings, potential specialized evidence, technical debt, and actions.
- In the technical debt section, separate confirmed debt, probable debt, accepted temporary debt, monitored debt, and signals that did not qualify as debt.
- Explain debt in terms of affected construct, change scenario, interest, cost of not paying, payment cost, confidence, and management decision.
- Summarize unresolved insight questions with missing context, affected flow, and why the answer matters.
- If `change-log.md` has entries, summarize intervention decisions separately from inferred system decisions.
- Include system flows from `system-context.md`; distinguish business rules from technical problems, specialized signals, and debt.
- The first screen of the report must be useful without reading the rest: use `Lectura rapida`, `Semaforo de gobernanza`, and `Decisiones o preguntas que requieren atencion`.
- Do not fill report sections with generic descriptions of the process. Each row or bullet must cite evidence, name impact, or ask for a concrete decision.
- Keep deep traceability later in the report. Do not put long source inventories, raw command output, or long path lists in the opening sections.

## Opening Sections

`## 1. Lectura rapida` must contain:

- overall state in one sentence;
- confidence level and why;
- top 3 findings or absences that affect decisions;
- top 3 actions or decisions requested;
- links or citations to `governance/` evidence.

`## 2. Semaforo de gobernanza` must summarize these areas:

- Sistema;
- Documentacion;
- Versionado;
- Agentes;
- Deuda tecnica;
- Revision especializada.

Use states such as `verde`, `amarillo`, `rojo`, or `gris`:

- `verde`: evidence is sufficient and no relevant blocker was found.
- `amarillo`: usable, but with gaps or medium-confidence issues.
- `rojo`: blocker, contradiction, or high-priority action.
- `gris`: not reviewed, no source, or unavailable resource.

`## 3. Decisiones o preguntas que requieren atencion` must include only questions that change action, priority, debt classification, scope, or risk handoff.

## Specialized Evidence Section

Use `## 8. Evidencia especializada potencial` to summarize `governance/evidence/specialized/`.

Rules:

- Say `senal potencial`, `requiere revision especializada`, or `evidencia insuficiente` unless direct evidence confirms the issue.
- Do not write `amenaza confirmada`, `vulnerabilidad explotable`, `fallo QA`, or `incumplimiento confirmado` without direct evidence and source citation.
- Do not convert specialized evidence into debt unless `technical-debt.md` explains artifact and change cost.
- For security signals, only recommend specialized review or an available security skill/plugin if one exists. Do not recommend direct correction from this skill.
- For QA signals, recommend only general checks unless a QA-specific skill/plugin is available or the evidence is non-specialized.

## Audience: tecnico

Use when the reader will act on implementation, architecture, or repository details.

Emphasize:

- architecture blocks, flow boundaries, integration points, and affected modules in the opening;
- modules, paths, entry points, commands, configs, dependencies, tests, and Docker evidence;
- code/documentation/versioning/agent contradictions;
- inferred architecture and affected building blocks;
- ADR/MADR gaps that block technical decisions;
- specialized evidence references and what specialist should review;
- concrete next actions with responsible artifact or area.

Style:

- more file paths and command summaries;
- more implementation detail;
- direct language for technical constraints;
- keep opening sections short, then put traceability and implementation detail in later sections.

## Audience: jefatura

Use when the reader needs governance, delivery, risk, and decision context.

Emphasize:

- what needs attention now, what can wait, and what decision unlocks progress;
- current system state;
- confidence level of the review;
- business or delivery impact of risks;
- decisions missing or pending validation;
- probable debt and why it matters;
- specialized review needs without technical alarmism;
- recommended actions grouped by management value.

Style:

- fewer low-level paths unless needed as evidence;
- explain impact before implementation detail;
- separate immediate decisions from follow-up technical work;
- include counts and top actions;
- keep technical details available in the evidence section.
- avoid alarmist security or QA language; say potential signal and recommended handoff when appropriate.

## Required Report Shape

Keep the canonical sections from `references/templates.md`. The first two sections must include:

- audience;
- scope;
- depth;
- permissions;
- resources evidence level;
- explicit statement that audience affected presentation only.

Reports generated as PDF must be written under `governance/reports/generated/`. The Markdown report remains the source of truth. If `governance/assets/architecture.png` exists, reference it in `## 4. Mapa actual del sistema`; embedding it in the PDF is optional.

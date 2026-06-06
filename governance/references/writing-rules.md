# Writing Rules

## Evidence

Write evidence as observable facts:

- file paths;
- commands and outputs summarized;
- docs found or absent;
- commit evidence;
- config, manifests, scripts, and tests.

Avoid unsupported claims. Use `no encontrado`, `pendiente`, or `inferido` when appropriate.

Paths must be relative to the reviewed project root. Do not write absolute machine paths such as `/home/...` or `/tmp/...` in chat, evidence, reports, or generated outputs. If a path is outside the reviewed root, write `fuera del alcance revisado`.

## Absence

Absence is evidence when the agent records where it looked. Use:

```md
**Estado de fuente:** no encontrado
**Buscado en:** paths/commands/docs checked
**Efecto:** what this limits
**Continuidad:** why the next step can continue
```

Do not leave a section blank when evidence is absent.

## Inferences

An inference must include evidence, reasoning, and confidence. Add a validation question only when human intent can change interpretation, priority, scope, debt, risk, specialist handoff, or action. If evidence is sufficient, write `Pregunta pendiente: no necesaria`. Never write an inferred decision as a confirmed fact.

## Confidence

- `alta`: direct and consistent evidence.
- `media`: partial evidence or reasonable inference.
- `baja`: weak signal, contradiction, or missing human context.

## Impact

- `alto`: affects critical flows, security, stability, compliance, roadmap, multiple modules, or multiple teams.
- `medio`: affects maintainability, delivery speed, quality, or an important area.
- `bajo`: local effect with limited current consequence.

## Questions

Ask only after evidence exists, except for initial configuration. Ask about:

- intent;
- criticality;
- external documentation;
- conventions;
- discarded alternatives;
- accepted debt;
- correction of an inference.

Save useful answers into the relevant `governance/` file.

Use `request_user_input` for every critical choice: depth, audience, permissions, scope, resource profile, specialized-review support, insight selection, correction authorization, specialist handoff, and report/PDF closure. Ask at most 3 questions per call and include valid options for every question.

Do not use `#question`, free text, or an optionless question tool for decisions that change scope, priority, debt, action, handoff, correction, or report generation. Plain text is allowed only for non-decision details after a choice is made.

Every non-initial question must include:

- missing context;
- current evidence;
- affected flow or artifact;
- why the answer changes action, decision, debt, risk, or continuity.

## Chat Output

Keep chat output compact. Summarize command results and write detailed evidence, command output, and traceability into `governance/`. Prefer script `--quiet` mode during routine runs.

Do not paste full stdout, long file inventories, diffs, repeated commands, or file-by-file change logs into chat unless explicitly requested. Show phase, blocker, authorization need, or compact result.

Do not use ad hoc heredoc scripts to rewrite `governance/`. If normalization needs deterministic automation, use a bundled script with `--quiet`.

Do not promise to hide platform-level traces such as thought timing, tool-call metadata, OpenCode task panels, or client UI events. Only the skill's own script output and chat summaries are controllable.

## Continue Rule

After writing evidence, absence, contradiction, or inference, continue to the next workflow step. Stop only for missing initial configuration, inability to write `governance/`, unreadable repo, or denied authorization for a requested tool.

## Insight Decisions

Present actionable insights for user selection before final report generation. Use `request_user_input`: `Corregir seguro`, `Posponer`, `Descartar`, `Requiere especialista`. If `request_user_input` is unavailable, stop before the choice.

For security signals, do not offer or record `Corregir seguro`. Use `Requiere especialista`, `Posponer`, or `Descartar`.

Record every selected outcome in `action-register.md`. For non-pending outcomes, also create an `interventions/ACT-XXX.md` record and add the decision to `change-log.md`.

## Enum Fields

Fields constrained to a fixed vocabulary must contain only the allowed value. Do not append explanations in parentheses or combine values with slashes.

Use narrative fields for explanation:

- debt rationale: `Impacto de deuda`, `Viabilidad de pago`, `Contexto faltante`, or `Evidencia`;
- action rationale: `Contexto faltante`, `Siguiente paso`, `Resultado`, or `Intervencion`.

## Report Writing

The final report must synthesize existing `governance/` files. It must not introduce new findings. Recommendations should be concrete and split into technical, documentation, decision, specialist-review, and follow-up actions when useful.

Before writing the final report, close insight decisions and read `references/report-writing.md`. The configured audience affects only report presentation, not the review process or conclusions.

## Specialized Evidence

Security, QA, data, performance, and compliance signals must be written as potential evidence unless directly confirmed. Use `evidence/specialized/` and avoid absolute language such as confirmed threat, exploitable vulnerability, QA failure, or compliance breach without direct evidence.

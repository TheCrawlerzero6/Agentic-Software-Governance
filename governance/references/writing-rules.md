# Writing Rules

## Evidence

Write evidence as observable facts:

- file paths;
- commands and outputs summarized;
- docs found or absent;
- commit evidence;
- config, manifests, scripts, and tests.

Avoid unsupported claims. Use `no encontrado`, `pendiente`, or `inferido` when appropriate.

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

An inference must include evidence, reasoning, confidence, and a validation question when human intent matters. Never write an inferred decision as a confirmed fact.

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

## Continue Rule

After writing evidence, absence, contradiction, or inference, continue to the next workflow step. Stop only for missing initial configuration, inability to write `governance/`, unreadable repo, or denied authorization for a requested tool.

## Report Writing

The final report must synthesize existing `governance/` files. It must not introduce new findings. Recommendations should be concrete and split into technical, documentation, decision, specialist-review, and follow-up actions when useful.

Before writing the final report, read `references/report-writing.md`. The configured audience affects only report presentation, not the review process or conclusions.

## Specialized Evidence

Security, QA, data, performance, and compliance signals must be written as potential evidence unless directly confirmed. Use `evidence/specialized/` and avoid absolute language such as confirmed threat, exploitable vulnerability, QA failure, or compliance breach without direct evidence.

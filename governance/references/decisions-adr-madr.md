# Decisions ADR/MADR

## What Counts

Record decisions that affect architecture, dependencies, critical flows, persistence, configuration, external integrations, accepted debt, deployment, security posture, or future evolution.

Use `decisions.md` for system decisions found or inferred from repository evidence. Use `change-log.md` for decisions made during later interventions or corrections.

## Types

- `documentada`: explicit ADR, doc, comment, or clear explanation.
- `inferida`: code/config/git suggest a choice but intent is not written.
- `faltante`: important choice exists without explanation.
- `contradictoria`: two evidence sources disagree.

## ADR Retrospective Candidate

Suggest an ADR when the decision involves:

- major provider or dependency;
- structural integration;
- repeated architecture pattern;
- critical flow;
- persistence model;
- critical configuration;
- accepted explicit or implicit debt;
- hard-to-reverse choice.

## MADR Retrospective Shape

Use this shape inside `decisions.md` notes or when drafting a suggested ADR later:

```md
### DEC-XXX: Decision title

**Estado:** documentada / inferida / faltante / contradictoria
**Contexto:** situation or force that made the decision relevant
**Decision:** what appears to have been chosen
**Alternativas observadas:** options mentioned or implied; write `no encontrado` if absent
**Evidencia:** docs, code paths, config, commits, source review rows
**Consecuencias:** known or likely tradeoffs
**Confianza:** baja / media / alta
**Pregunta pendiente:** concrete validation question if needed; otherwise `no necesaria`
**ADR retrospectivo sugerido:** si / no, reason
```

## When To Document And Continue

- Document `documentada` when a source explicitly states the decision.
- Document `inferida` when code/config/git consistently indicate a choice but intent is missing. Do not ask if the evidence is enough to explain the inference.
- Document `faltante` when a significant choice exists and no rationale is found.
- Document `contradictoria` when two evidence sources disagree.
- Continue after documenting, unless the decision determines the review scope itself.

## When To Ask

Ask only if human context can change interpretation, priority, scope, debt classification, specialist handoff, or action.

Do not ask just because a decision is inferred. If the panorama is clear, record:

```md
**Pregunta pendiente:** no necesaria
```

Use a concrete question when:

- evidence is contradictory;
- confidence is `baja`;
- repository evidence shows the choice but not the business or operational constraint that changes the conclusion;
- the decision affects review scope or immediate action.

## Writing Rules

- Do not create final ADRs automatically.
- Keep evidence and interpretation separate.
- Every inferred decision needs evidence, reasoning, confidence, and either a needed question or `Pregunta pendiente: no necesaria`.
- Prefer concise decision titles: "Use PostgreSQL for persistence", not broad summaries.
- Mark whether a decision appears to be business logic, technical design, operational constraint, specialized risk context, or debt acceptance when that distinction helps avoid misclassification.

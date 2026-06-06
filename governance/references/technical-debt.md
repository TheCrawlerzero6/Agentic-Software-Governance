# Technical Debt

Read only in `profundo` or when the user explicitly asks for technical debt evaluation.

This reference adapts Avgeriou et al. 2024 and Perera et al. 2023 into a practical
agent workflow. Use it as a classification and prioritization guide, not as a claim
that one universal metric exists.

## Definition

Technical debt is a concrete requirements, architecture, design, implementation,
test, build, dependency, documentation, or data construct that creates a technical
context where future or current changes become more costly, slower, riskier, or
impossible.

Debt requires:

```text
technical construct + scenario of change + interest when changed + evidence + management decision
```

Do not dilute the term. Bugs, vulnerabilities, missing features, process problems,
or old technology are not technical debt by themselves. They may reveal debt only
when a technical construct makes change cost increase.

## Required Litmus Test

Before registering `TD-*`, answer all five questions:

1. What concrete technical artifact or construct exists?
2. What current or future change touches that construct?
3. What extra cost, delay, rework, workaround, or uncertainty appears because of it?
4. How likely is the affected change scenario to occur?
5. What decision is being made: pay, plan, accept temporarily, monitor, or reject?

If 1, 2, or 3 is missing, do not create formal debt. Record a signal in evidence.
If 4 or 5 is missing, create at most `candidata` or `probable` with a user question.

## States

- `candidata`: signal exists, but the litmus test is incomplete.
- `probable`: construct and change-cost evidence exist; impact, timing, or owner needs confirmation.
- `confirmada`: evidence supports construct, change scenario, interest, and management option.
- `aceptada`: debt is deliberately retained for value, timing, or capacity reasons and has a review date.
- `planificada`: repayment or containment is scheduled.
- `en pago`: repayment work is active.
- `pagada`: repayment completed and evidence updated.
- `rechazada`: reviewed and does not qualify as technical debt.

## Origin

- `deliberada`: intentionally taken for short-term value, time, cost, or delivery pressure.
- `inadvertida`: introduced unintentionally through incomplete knowledge, drift, or poor visibility.
- `contingente`: becomes debt when circumstances change, such as roadmap, scale, dependency support, regulation, or platform shift.
- `desconocida`: origin cannot be inferred from written evidence.

## Types

- `requisitos`: unclear, incomplete, or inconsistent requirements that raise maintenance/evolution cost.
- `arquitectura`: dependency cycles, wrong boundaries, cross-domain coupling, hard-to-change platform choices.
- `diseno`: god objects, wrong abstractions, feature envy, deep inheritance, low cohesion.
- `codigo`: complex, duplicated, obscure, or fragile implementation constructs.
- `pruebas`: missing, flaky, slow, or implementation-coupled tests that make changes more expensive.
- `build`: brittle build scripts, environment-specific builds, unclear release mechanics.
- `dependencias`: unsupported libraries, blocked upgrades, dependency coupling.
- `documentacion`: missing or stale technical decisions or critical operational knowledge that slows safe change.
- `datos`: rigid schemas, overloaded fields, duplicated data, implicit relations, manual migrations.

## Evidence Classes

Use repository evidence first. Useful evidence includes:

- code structure, coupling, change propagation, repeated workarounds, complexity, or boundary violations;
- tests, build scripts, dependency manifests, migrations, config, Docker, CI, or release files;
- git history showing repeated attempted fixes, revert loops, workaround commits, or long-running unresolved changes;
- docs, ADR/MADR, TODO/FIXME, issue references, incident notes, or explicit self-admitted debt;
- user-provided roadmap or business context when repository evidence cannot answer change probability.

Signals are proxies, not conclusions. A code smell, low coverage, TODO, vulnerability signal, or static-analysis warning
does not become debt until the litmus test connects it to change cost.

## Specialized Evidence Is Not Debt By Default

Security, QA, data, performance, and compliance signals live first in `evidence/specialized/`.

Security evidence is record-and-handoff only in this skill. Do not propose direct fixes, patches, mitigations,
exploitability conclusions, or implementation work for `SEC-POT-*`. If a relevant security skill/plugin is available,
propose using it; otherwise recommend specialized review.

A specialized signal becomes technical debt only when it also proves:

```text
technical construct + scenario of change + interest when changed + payment/management option
```

Examples:

- Possible CVE in a dependency: specialized security evidence, not debt.
- Dependency with possible CVE and upgrade blocked by module coupling: specialized evidence plus possible dependency debt.
- Missing tests: QA evidence, not automatically debt.
- Missing tests that force repeated manual validation in a critical change path: possible testing debt.

## Quantification Model

Use qualitative scores unless the project already has reliable cost data. Do not invent money, hours, ROI, or percentages.

Score these dimensions as `bajo` = 1, `medio` = 2, `alto` = 3:

- `Interes actual`: extra cost already being paid.
- `Interes esperado`: extra cost expected in future changes.
- `Probabilidad de interes`: likelihood that upcoming/current work touches the debt item.
- `Costo de no pagar`: expected delivery, maintenance, reliability, or evolution cost if retained.
- `Impacto en evolucion`: effect on roadmap, feature delivery, modernization, or integration.
- `Impacto en mantenibilidad`: effect on comprehension, local change, testing, and support.
- `Costo de pago / principal`: effort to refactor, replace, document, migrate, or otherwise repay.
- `Beneficio de pago`: expected benefit after repayment.
- `Confianza de evidencia`: strength of evidence behind the item.

Derived values:

```text
impacto_de_deuda =
  interes_actual + interes_esperado + probabilidad_de_interes +
  costo_de_no_pagar + impacto_en_evolucion + impacto_en_mantenibilidad

viabilidad_de_pago = beneficio_de_pago / costo_de_pago

prioridad =
  (impacto_de_deuda * confianza_de_evidencia) / costo_de_pago
```

Criticality:

- `critica`: priority >= 10 or automatic escalation.
- `alta`: priority >= 7 and < 10.
- `media`: priority >= 4 and < 7.
- `baja`: priority < 4.

If exact calculation is not possible, record qualitative `Prioridad estimada` and explain missing context.

## Automatic Escalation

Mark as at least `alta`, or `critica` when the evidence is strong, if the item:

- blocks a known upcoming change, release, migration, dependency update, or critical integration;
- affects architecture boundaries, data model, or core flow across multiple modules;
- appears in repeated failed fixes, revert loops, or workaround commits;
- makes specialist handoff difficult because the affected construct is unclear or undocumented;
- affects a critical flow and no alternative validation path exists;
- has accepted debt with no review date or owner.

## Management Decisions

- `pagar ahora`: repayment should precede or accompany current work.
- `pagar con feature`: repay while touching the affected area.
- `planificar`: create technical epic or scheduled work.
- `aceptar temporalmente`: keep intentionally, with reason, owner, and review date.
- `monitorear`: watch until change probability or impact increases.
- `rechazar`: does not qualify as technical debt.

Accepted debt is still debt. Record why it was accepted, what value it creates, and when to revisit it.

## Required TD Record

```md
### TD-001: Titulo corto

**Estado:** candidata / probable / confirmada / aceptada / planificada / en pago / pagada / rechazada
**Tipo:** requisitos / arquitectura / diseno / codigo / pruebas / build / dependencias / documentacion / datos
**Origen:** deliberada / inadvertida / contingente / desconocida
**Artefacto afectado:**
**Decision relacionada:** DEC- / ninguna
**Flujo afectado:** FLW- / no identificado
**Escenario de cambio:**
**Constructo que encarece el cambio:**
**Interes actual:** bajo / medio / alto
**Interes esperado:** bajo / medio / alto
**Probabilidad de interes:** baja / media / alta
**Costo de pago / principal:** bajo / medio / alto
**Beneficio de pago:** bajo / medio / alto
**Costo de no pagar:** bajo / medio / alto
**Impacto en evolucion:** bajo / medio / alto
**Impacto en mantenibilidad:** bajo / medio / alto
**Confianza de evidencia:** baja / media / alta
**Impacto de deuda:**
**Viabilidad de pago:**
**Prioridad estimada:** baja / media / alta / critica
**Evidencia:**
**Evidencia especializada relacionada:** SEC-POT / QA-POT / DATA-POT / PERF-POT / COMP-POT / ninguna
**Contexto faltante:**
**Pregunta al usuario:**
**Decision de gestion:** pagar ahora / pagar con feature / planificar / aceptar temporalmente / monitorear / rechazar
**Fecha de revision:**
```

## When To Ask

Ask only when classification depends on context not present in written evidence:

- whether the affected flow is critical;
- whether a shortcut was deliberately accepted;
- whether roadmap work will touch the artifact soon;
- whether incident, support, or manual-validation evidence exists outside the repo;
- whether a specialized signal has been confirmed by a specialist.

Questions must include the missing context, affected flow, current evidence, and consequence of the answer.

If the answer is unavailable, continue with `candidata`, `probable`, or `monitorear`; do not inflate confidence.

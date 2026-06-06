---
name: gobernanza-por-evidencia
description: Use this skill when reviewing an existing local repository by written evidence, creating or updating governance/, mapping system context with arc42-reduced analysis, auditing code/docs/git/agent instructions, recording specialized potential evidence, reconstructing ADR/MADR decisions, producing governance reports, or evaluating technical debt only in deep mode.
---

# Gobernanza Por Evidencia

## Non-Negotiables

Run an evidence-based governance review of an existing local repository. Do not modify source code during the base review. Persist evidence in `governance/`; do not leave findings only in chat.

Before creating or changing `governance/`, obtain:

1. Depth: `normal` or `profundo`.
2. Audience: `tecnico` or `jefatura`.
3. Permissions: `seguro` or `herramientas`.
4. Scope: repo completo, module, folder, or flow.
5. Available resources: local repository, local history, remote repository context, external documentation, local verification commands, local environment, existing reports, and specialized review support.

Ask for missing initial inputs in one concise block and stop before writing if they are absent. Never ask the user to paste tokens.

## Review Checklist

Use this checklist as the user-visible flow. It is not a rigid script, but the evidence gates must be satisfied before closure.

1. Prepare review: read `references/workflow.md`, `references/arc42-reducido.md`, and `references/continuation-rules.md`.
2. Initialize `governance/` with `scripts/init_governance.py`.
3. Record `governance/governance-config.md`, including `Recursos disponibles`.
4. Explore base: run `scripts/prescan_evidence.py` without executing project tools.
5. Understand system: fill `governance/system-context.md`.
6. Review evidence in order:
   - code: read `references/pyramid-code.md`;
   - documentation: read `references/pyramid-documentation.md`;
   - versioning: read `references/pyramid-versioning.md` and `cookbooks/git.md`;
   - agents: read `references/pyramid-agents.md`.
7. Record potential specialized evidence in `governance/evidence/specialized/` when security, QA, data, performance, or compliance signals appear.
8. Fill `governance/decisions.md` using `references/decisions-adr-madr.md`.
9. Ask the user only for gaps that cannot be resolved from written evidence.
10. If depth is `profundo`, read `references/technical-debt.md` and fill `governance/technical-debt.md`.
11. Fill `governance/action-register.md` with actionable insights, missing context, structured questions, affected flow, and evidence.
12. Validate with `scripts/validate_governance.py --strict`.
13. At closure, read `references/report-writing.md` and update `governance/reports/governance-report.md` only from `governance/` files when the user requests or the review is ready to close.
14. Generate the PDF with `scripts/render_report.py` only when requested or when producing an executive closure. The PDF is written under `governance/reports/generated/`.

Do not skip a step. Later steps depend on earlier written evidence.

## Resource Map

- Use `references/templates.md` whenever creating or rewriting `governance/` files.
- Use `references/arc42-reducido.md` when deciding what each evidence item contributes to `system-context.md` or `evidence/*.md`.
- Use `references/continuation-rules.md` when evidence is missing, contradictory, weak, or only inferable.
- Use `references/writing-rules.md` before recording evidence, confidence, impact, contradictions, questions, or recommendations.
- Use `references/report-writing.md` before writing the final report. Audience changes only report presentation.
- Use `references/validation-checklist.md` before finalizing.
- Use `cookbooks/repo-search.md` for local search.
- Use `cookbooks/project-commands.md` only in `herramientas` mode.
- Use `cookbooks/docker.md` only for Docker evidence and only within permissions.
- Use `cookbooks/github.md`, `cookbooks/mcp.md`, and `cookbooks/static-analysis.md` internally only when the matching user-facing resource is available and authorized.

## Operating Rules

- `seguro`: read/search local files, inspect local git read-only, and write only `governance/`.
- `herramientas`: may run tests/lint/build/typecheck/Docker/project commands only when authorized and relevant.
- Never use `sudo`, destructive commands, production access, history rewrites, pushes, resets, deletes, or credential capture.
- Never ask the user to paste tokens. Use existing configured tools/tokens only if authorized; do not print, store, or copy secrets into `governance/`.
- Record relevant commands with purpose and result in the matching `governance/evidence/*.md` file.
- Keep evidence files concise: record useful summary, coverage, findings with evidence/confidence, relevant decisions, contradictions/absences, questions, and commands. Do not fill generic sections with low-value inventory.
- Mark undocumented interpretations as `inferido` until confirmed.
- Use `governance/decisions.md` for system decisions found or inferred from evidence. Use `governance/change-log.md` only for decisions made during later interventions or corrections.
- Every insight question must state what context is missing, why it matters, where evidence was found, and which flow is affected. Do not ask vague questions like "what should I do?".
- Audience (`tecnico` or `jefatura`) must not change the workflow, evidence reviewed, confidence, impact, questions, debt classification, or recommendations. It only changes report wording, emphasis, and level of detail.
- Specialized evidence is potential by default. Do not assert threats, exploitable vulnerabilities, QA failures, data issues, performance defects, or compliance failures without direct evidence.
- Security signals (`SEC-POT-*`) are record-and-handoff only. Do not propose direct fixes, patches, mitigations, exploitability conclusions, or implementation work from this skill. After recording them, check whether a relevant available skill/plugin exists; propose it only if present, otherwise recommend specialized review.
- QA signals may suggest general non-specialist actions only when safe and authorized, such as running existing tests or reviewing coverage. If specialized QA judgment is needed, record and hand off instead of correcting.
- A specialized signal becomes technical debt only when it also has concrete artifact, change-cost evidence, interest, and mitigation action.
- If evidence is absent, write `no encontrado`, explain where you looked, assign low confidence when relevant, add a pending question only if human context can change the conclusion, and continue.
- In `normal`, record only risk/debt signals. Do not score or confirm formal technical debt.
- In `profundo`, every debt item must name a concrete technical construct, the affected change scenario, current/expected interest, interest probability, payment cost, evidence confidence, priority, and management decision.

## Scripts

Initialize:

```bash
python3 gobernanza-por-evidencia/scripts/init_governance.py \
  --root . \
  --depth normal \
  --audience tecnico \
  --permissions seguro \
  --scope "repo completo"
```

Pre-scan evidence:

```bash
python3 gobernanza-por-evidencia/scripts/prescan_evidence.py --root .
```

Validate:

```bash
python3 gobernanza-por-evidencia/scripts/validate_governance.py --root . --strict
```

Render PDF:

```bash
python3 gobernanza-por-evidencia/scripts/render_report.py --root .
```

If validation fails, fix `governance/` evidence files before generating or updating the final report.

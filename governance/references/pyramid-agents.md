# Pyramid: Agents

Use this layer to understand AI/operator rules that affect how work should be done.

Read `references/arc42-reducido.md` before deciding whether rules are restrictions, decisions, or limitations.

## Inspect

- `AGENTS.md` and nested variants.
- `.agents/skills`, local skills, prompts, rules, hooks, config.
- Project-specific testing or documentation instructions.
- MCP or tool configuration referenced by repo files.
- Any rules that constrain architecture, style, permissions, or reviews.

## Evidence To Record

- Rules that govern agent behavior.
- Skills or prompts already present.
- Tooling permissions or limits.
- Contradictions between rules and repo reality.
- Missing rules for decisions, docs, or debt.

## Arc42 Mapping

| Agent/rule evidence | Source section | `system-context.md` section |
|---|---|---|
| AGENTS.md constraints | restrictions | restrictions |
| Testing/documentation commands | restrictions/config | deployment/configuration, limitations |
| Existing skills/prompts/rules | elements/context | stakeholders, restrictions |
| Architecture/style rules | decisions | decisions existing or inferred |
| Missing or contradictory rules | contradictions/questions | limitations, risks |

## Continue If Missing

- If no agent rules exist, record absence and continue.
- If rules conflict with code or docs, record contradiction and impact.
- If rules encode an architectural choice, add a decision candidate.

## Do Not Overclaim

- Agent rules are process evidence, not proof of system behavior.
- If no agent rules exist, record absence and impact.
- Do not expose secrets from config files.

## Register In

- `governance/evidence/agents.md`
- `governance/decisions.md` when rules encode decisions

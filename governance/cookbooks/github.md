# GitHub Cookbook

## Purpose

Use GitHub as optional external evidence for decisions, PR history, known risks, and roadmap context.

## Authorization

- Use only an already configured `gh` session, GitHub MCP, or existing token.
- Do not ask the user to paste a token.
- Do not print, store, or copy secrets into `governance/`.
- If auth is unavailable, record `GitHub no disponible` and continue.

## Read-Only Procedure

1. Check `gh auth status` only if `herramientas` or explicit authorization allows it.
2. Use `gh repo view` to confirm repository identity.
3. Review recent PRs/issues only for concrete evidence gaps.
4. Summarize PR/issue IDs and URLs; do not paste long bodies.

## Evidence Value

| GitHub evidence | Register in |
|---|---|
| PR explains architecture/provider choice | `decisions.md` |
| Issue documents known limitation | `evidence/documentation.md` or `evidence/versioning.md` |
| Review comments reveal convention | `evidence/agents.md` or decisions |
| Milestone/roadmap changes criticality | questions or debt impact in `profundo` |
| Security/QA issue without direct validation | `evidence/specialized/security.md` or `evidence/specialized/qa.md` as potential |

## Continue

GitHub is never required for the base review. Local repo evidence remains primary.

# Pyramid: Versioning

Use this layer to understand evolution, not to dump git output.

Read `references/arc42-reducido.md` and `cookbooks/git.md` before recording this layer.

## Inspect

- `git status --short`
- Recent commit messages.
- Commit stats for repeated files or modules.
- Reverts, hotfixes, bug-fix clusters.
- Large commits touching unrelated areas.
- Dependency or framework introduction/removal.

Use `cookbooks/git.md` before running commands.

## Evidence To Record

- Modules with frequent changes.
- Historical decisions suggested by commits.
- Fragile zones suggested by rework or fixes.
- Changes that do not have enough explanation.
- Versioning limitations, including no valid git repository.

## Arc42 Mapping

| Versioning evidence | Source section | `system-context.md` section |
|---|---|---|
| Frequent files/modules | elements/risks | building blocks, risks |
| Reverts/hotfixes/rework | risks/questions | quality, limitations |
| Commit messages explaining choices | decisions | decisions existing or inferred |
| Dependency introduction/removal | decisions/restrictions | restrictions, decisions |
| No git repository | source reviewed/limitations | limitations |

## Continue If Missing

- If git is unavailable or invalid, record `no encontrado` and continue.
- If history is shallow or noisy, record limitation and avoid conclusions.
- If a commit suggests intent, mark it as historical evidence, not confirmed current intent.

## Do Not Overclaim

- Commit frequency is a signal, not a verdict.
- A revert is a signal of change risk, not necessarily debt.
- Do not blame people; record artifacts and change patterns.

## Register In

- `governance/evidence/versioning.md`
- `governance/decisions.md`
- `governance/technical-debt.md` only in `profundo`

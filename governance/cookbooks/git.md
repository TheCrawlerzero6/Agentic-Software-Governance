# Git Cookbook

## Purpose

Use local git history as evolution evidence without modifying the repository.

## Procedure

1. Run `git status --short` and record whether the tree is dirty.
2. Run `git log --oneline --decorate -n 30` for recent intent clues.
3. Run `git log --stat -n 20` only to identify frequently changed files or wide changes.
4. Use `git show <commit>` only for commits that appear decision-relevant.
5. Use `git blame <file>` only when it explains a concrete decision or risk.

## Look For

| Evidence | Interpretation | Register in |
|---|---|---|
| Commit message explains technology/provider/pattern | decision candidate | `decisions.md` |
| Same module changes repeatedly | hotspot/risk signal | `evidence/versioning.md` |
| Reverts/hotfixes | fragility signal | `evidence/versioning.md` |
| Commit touches unrelated modules | possible coupling/change propagation | `evidence/versioning.md`; debt only in `profundo` |
| Dependency introduced/removed | decision or restriction | `evidence/versioning.md`, `decisions.md` |

## Limits

Never run commit, checkout, reset, rebase, push, stash, clean, or history rewrite commands.

## Continue

If git is unavailable or invalid, set `evidence/versioning.md` to `no encontrado`, record the command attempted, and continue to agents.

# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Git workflow

- **Never commit directly to `main`.** All changes must go through a branch and a pull request for review before merging.
- Create a feature/fix branch, commit there, push it, and open a PR (`gh pr create`) instead of pushing straight to `main` — even for small doc or config changes.
- Do not use `(closes #N)` / `(fixes #N)` in commit messages destined for direct `main` pushes, since that auto-closes issues on push. Let the PR merge close the issue instead.

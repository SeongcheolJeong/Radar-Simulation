# Workflow Rules

## One-by-One Progression

1. Lock a contract before coding.
2. Add a deterministic check for the new behavior.
3. Run the check.
4. Log result and move to next checkpoint.

## Change Scope Rule

- Do not mix interface redesign and physics model change in one commit-sized step.
- Keep each validation script focused on one failure mode.

## Regression Rule

Whenever adding a new feature:

- re-run `scripts/validate_step1.py`
- ensure all baseline checkpoints still pass

## Review Rule

Before moving to `.ffd` and RT integration:

- verify canonical ADC shape remains `sample, chirp, tx, rx`
- verify `paths_by_chirp` remains backend-agnostic


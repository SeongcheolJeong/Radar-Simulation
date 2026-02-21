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

## Value-Gate Rule

Before starting each new checkpoint, define:

- decision to make (`adopt/reject/hold`)
- measurable signal that can change that decision

If a task cannot change a decision, skip it.

## Repetition Stop Rule

Stop and re-plan when the same loop repeats without new signal:

- two consecutive runs produce no meaningful metric change
- or same failure class repeats with no interface/model change

At stop point, propose one of:

- narrower hypothesis test
- data/metric change
- plan downgrade (defer low-yield branch)

## Efficiency Rule

Prefer one orchestrator + one summary over multiple manual commands.

- batch related validations together
- avoid creating duplicate report types with identical decision value
- keep one “decision report” per milestone

## Replan Trigger Rule

Update plan immediately when one of these happens:

- required measured input is unavailable
- target metric does not improve after two hypothesis changes
- milestone output does not map to final goal artifacts (`path list`, `raw ADC`, replay lock quality)

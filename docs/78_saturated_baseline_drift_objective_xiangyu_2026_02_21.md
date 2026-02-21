# Saturated Baseline Drift Objective Report (Xiangyu, 2026-02-21)

## Inputs

- Rerun-baseline fit-aware batch summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_rerun_baseline_2026_02_21.json`
- Drift-objective selection output:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_lock_drift_selection_xiangyu_rerun_baseline_2026_02_21.json`
- Drift-objective search probe output (1 case):
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_lock_search_drift_probe_bms512_2026_02_21.json`

## 3-Case Drift Ranking Result

- `selection_mode=fit`
- recommendation: `exploratory_fit_candidate_selected_by_drift`
- selected fit:
  - `path_power_fit_reflection_selected.json`

Score snapshot:

- reflection aggregate score: `139.3903`
- scattering aggregate score: `141.3810`

Both fits still show strong pass/fail degradation vs baseline; drift objective here is ranking for exploration, not adoption.

## Search Integration Probe (1 case)

`run_measured_replay_fit_lock_search.py` with `--objective-mode drift`:

- `short_circuit=false` even with `cases_with_improvement_headroom=0`
- policy gate remained failed (`reject_fit_lock_due_to_degradation`)
- drift selector produced exploratory fit choice (`reflection`) for analysis workflow

## Interpretation

For saturated baseline scenarios, drift objective can provide deterministic "least-distorting" candidate ranking.
Adoption remains blocked by policy gate unless non-degradation constraints are satisfied.

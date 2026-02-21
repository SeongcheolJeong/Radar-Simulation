# Constrained Refit Consistency Gate Report (Xiangyu Targets, 2026-02-21)

## Inputs

- Constrained refit multi-case summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_drift_search_xiangyu_targets_all_presets_2026_02_21.json`
- Consistency gate summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_consistency_gate_xiangyu_targets_2026_02_21.json`

Cases:

- `bms1000_512`
- `bms1000_full897`
- `cms1000_128`

## Constrained Search Snapshot

All presets completed (`fit_json_count=4` each):

- `flat`: recommendation `exploratory_fit_candidate_selected_by_drift`, score `42.7271`
- `balanced`: recommendation `exploratory_fit_candidate_selected_by_drift`, score `46.8954`
- `steep`: recommendation `exploratory_fit_candidate_selected_by_drift`, score `91.3187`

Search-best preset by score: `flat`.

## Consistency Gate Result

- `gate_failed=true`
- `recommendation=fallback_to_baseline_no_fit`
- `selection_mode=baseline_no_fit`
- `eligible_preset_count=0`

Main rejection signals:

- all presets exceeded degradation caps (`pass_rate_drop`, `pass_count_drop_ratio`, `fail_count_increase_ratio`)
- no preset had adopt-level drift recommendation (all exploratory)
- `balanced` and `steep` also exceeded `metric_drift_mean` cap (`0.1`)

## Interpretation

For the 3-case Xiangyu target set, constrained preset refit did not produce a non-degrading globally consistent candidate.
Decision remains baseline fallback, and next iteration should focus on narrowing search space around low-drift/low-degradation regions rather than broad preset sweeps.

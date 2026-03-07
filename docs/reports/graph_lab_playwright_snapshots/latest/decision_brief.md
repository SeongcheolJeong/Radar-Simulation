# Radar Decision Brief

- generated_at_utc: 2026-03-07T09:15:47.407Z
- graph_id: radar_minimal_v1

## Decision Snapshot
```text
generated_at_utc: 2026-03-07T09:15:47.128Z
decision: ADOPT
recommendation: adopt_candidate
baseline_id: playwright_baseline
current_run_id: grun_20260307_091546_bb9a0432
compare_run_id: grun_20260307_091545_d9ec5c35
compare_runner_status: ready
current_track: backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
compare_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
current_runtime: state:ready | sim:auto | license:none
compare_runtime: state:ready | modules:1/1 | sim:adc | adc:runtime | license:env
gate_failure_count: 0
path_count_delta(current-compare): +4
rd_peak_delta(range/doppler): +0/+12
ra_peak_delta(range/angle): +0/+3
```

## Runtime Compare
- current_track: backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
- compare_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
- compare_runner_status: track_compare_runner=ready | compare=grun_20260307_091545_d9ec5c35 | current=grun_20260307_091546_bb9a0432 | target=backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
- compare_status: compare_mode=runner_low_fidelity | run=grun_20260307_091545_d9ec5c35 | status=completed

### Current Runtime Diagnostics
```text
state: ready
backend: analytic_targets
provider: -
mode: -
simulation_used: -
adc_source: -
license_source: none
module_report:
- none
runtime_error: -
```

### Compare Runtime Diagnostics
```text
state: ready
backend: radarsimpy_rt
provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths
mode: runtime_provider
simulation_used: true
adc_source: runtime_payload_adc_sctr
license_source: env
module_report:
- radarsimpy: ok @15.0.1
runtime_error: -
```

## Current Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_1ff52u2w/store/graph_runs/grun_20260307_091546_bb9a0432/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_1ff52u2w/store/graph_runs/grun_20260307_091546_bb9a0432/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_1ff52u2w/store/graph_runs/grun_20260307_091546_bb9a0432/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_1ff52u2w/store/graph_runs/grun_20260307_091546_bb9a0432/output/path_list.json

## Compare Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_1ff52u2w/store/graph_runs/grun_20260307_091545_d9ec5c35/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_1ff52u2w/store/graph_runs/grun_20260307_091545_d9ec5c35/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_1ff52u2w/store/graph_runs/grun_20260307_091545_d9ec5c35/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_1ff52u2w/store/graph_runs/grun_20260307_091545_d9ec5c35/output/path_list.json

## Gate Evidence
- none

## Regression Session
- session_id: dssn_1772874947227
- session_recommendation: hold_some_candidates
- export_id: rexp_20260307_091547_e8d9863d
- export_package_json: /tmp/graph_lab_playwright_e2e_1ff52u2w/store/regression_exports/rexp_20260307_091547_e8d9863d/regression_package.json
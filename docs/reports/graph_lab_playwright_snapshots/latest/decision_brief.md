# Radar Decision Brief

- generated_at_utc: 2026-03-07T09:27:18.875Z
- graph_id: radar_minimal_v1

## Decision Snapshot
```text
generated_at_utc: 2026-03-07T09:27:18.624Z
decision: ADOPT
recommendation: adopt_candidate
baseline_id: playwright_baseline
current_run_id: grun_20260307_092717_d5e32f5b
compare_run_id: grun_20260307_092717_03fb6b08
compare_runner_status: ready
current_track: backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
compare_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
current_runtime: state:ready | sim:auto | license:none
compare_runtime: state:ready | modules:1/1 | sim:adc | adc:runtime | license:env
compare_assessment: review
compare_flags: path_delta:+4 | rd_peak_shift:+0/+12/0.00 | ra_peak_shift:+0/+3/0.00
gate_failure_count: 0
path_count_delta(current-compare): +4
rd_peak_delta(range/doppler): +0/+12
ra_peak_delta(range/angle): +0/+3
```

## Runtime Compare
- current_track: backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
- compare_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
- compare_runner_status: track_compare_runner=ready | compare=grun_20260307_092717_03fb6b08 | current=grun_20260307_092717_d5e32f5b | target=backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
- compare_status: compare_mode=runner_low_fidelity | run=grun_20260307_092717_03fb6b08 | status=completed

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

## Compare Assessment
```text
assessment: review
flags: path_delta:+4 | rd_peak_shift:+0/+12/0.00 | ra_peak_shift:+0/+3/0.00
shape_status(adc/rd/ra): match/match/match
shape(adc): 256x4x2x2 vs 256x4x2x2
shape(rd): 16x64 vs 16x64
shape(ra): 8x64 vs 8x64
adc_source(current/compare): -/runtime
path_count_delta(current-compare): +4
rd_peak_delta(range/doppler/rel_db): +0/+12/0.00
ra_peak_delta(range/angle/rel_db): +0/+3/0.00
required_artifacts(current/compare/total): 4/4/4
artifact_presence_delta: none
optional_artifact_delta: none
```

## Current Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_g37jsi8h/store/graph_runs/grun_20260307_092717_d5e32f5b/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_g37jsi8h/store/graph_runs/grun_20260307_092717_d5e32f5b/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_g37jsi8h/store/graph_runs/grun_20260307_092717_d5e32f5b/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_g37jsi8h/store/graph_runs/grun_20260307_092717_d5e32f5b/output/path_list.json

## Compare Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_g37jsi8h/store/graph_runs/grun_20260307_092717_03fb6b08/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_g37jsi8h/store/graph_runs/grun_20260307_092717_03fb6b08/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_g37jsi8h/store/graph_runs/grun_20260307_092717_03fb6b08/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_g37jsi8h/store/graph_runs/grun_20260307_092717_03fb6b08/output/path_list.json

## Gate Evidence
- none

## Regression Session
- session_id: dssn_1772875638728
- session_recommendation: hold_some_candidates
- export_id: rexp_20260307_092718_7dd0fcdc
- export_package_json: /tmp/graph_lab_playwright_e2e_g37jsi8h/store/regression_exports/rexp_20260307_092718_7dd0fcdc/regression_package.json
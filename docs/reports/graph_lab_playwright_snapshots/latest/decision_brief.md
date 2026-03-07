# Radar Decision Brief

- generated_at_utc: 2026-03-07T10:06:17.412Z
- graph_id: radar_minimal_v1

## Decision Snapshot
```text
generated_at_utc: 2026-03-07T10:06:17.107Z
decision: ADOPT
recommendation: adopt_candidate
baseline_id: playwright_baseline
current_run_id: grun_20260307_100616_2235020c
compare_run_id: grun_20260307_100615_ac9b5c3b
compare_runner_status: ready
selected_preset_pair: low_fidelity_radarsimpy_ffd -> current_config
selected_preset_pair_label: Low Fidelity: RadarSimPy + FFD -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
selected_preset_pair_forecast: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | sim:auto | license:none
compare_session_count: 2
latest_compare_session: 2026-03-07T10:06:16.973Z | source=preset_pair | status=ready | pair=Low Fidelity: RadarSimPy + FFD -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none | phase=current | compare=grun_20260307_100615_ac9b5c3b | current=grun_20260307_100616_2235020c | assessment=review
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
- selected_preset_pair: low_fidelity_radarsimpy_ffd -> current_config
- selected_preset_pair_label: Low Fidelity: RadarSimPy + FFD -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
- current_track: backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
- compare_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
- compare_runner_status: track_compare_runner=ready | mode=preset_pair | baseline_preset=low_fidelity_radarsimpy_ffd | target_preset=current_config | compare=grun_20260307_100615_ac9b5c3b | current=grun_20260307_100616_2235020c
- compare_status: compare_mode=runner_preset_pair | baseline_preset=low_fidelity_radarsimpy_ffd | run=grun_20260307_100615_ac9b5c3b | status=completed

## Selected Pair Forecast
```text
selected_pair: Low Fidelity: RadarSimPy + FFD -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none
target_forecast: state:planned | sim:auto | license:none
```

## Compare Session History
```text
[1] 2026-03-07T10:06:16.973Z | source=preset_pair | status=ready | pair=Low Fidelity: RadarSimPy + FFD -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none | phase=current | compare=grun_20260307_100615_ac9b5c3b | current=grun_20260307_100616_2235020c | assessment=review
[2] 2026-03-07T10:06:15.475Z | source=pin_current | status=pinned | pair=low_fidelity_radarsimpy_ffd -> current_config | compare=grun_20260307_100614_d9f7360a
```

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
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_5giegga9/store/graph_runs/grun_20260307_100616_2235020c/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_5giegga9/store/graph_runs/grun_20260307_100616_2235020c/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_5giegga9/store/graph_runs/grun_20260307_100616_2235020c/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_5giegga9/store/graph_runs/grun_20260307_100616_2235020c/output/path_list.json

## Compare Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_5giegga9/store/graph_runs/grun_20260307_100615_ac9b5c3b/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_5giegga9/store/graph_runs/grun_20260307_100615_ac9b5c3b/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_5giegga9/store/graph_runs/grun_20260307_100615_ac9b5c3b/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_5giegga9/store/graph_runs/grun_20260307_100615_ac9b5c3b/output/path_list.json

## Gate Evidence
- none

## Regression Session
- session_id: dssn_1772877977165
- session_recommendation: hold_some_candidates
- export_id: rexp_20260307_100617_9d51f18a
- export_package_json: /tmp/graph_lab_playwright_e2e_5giegga9/store/regression_exports/rexp_20260307_100617_9d51f18a/regression_package.json
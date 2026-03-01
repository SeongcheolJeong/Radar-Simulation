# Physics Accuracy Envelope Without PO-SBR (2026-02-26, updated 2026-03-01)

## Purpose

Define practical accuracy bounds for the current stack when high-fidelity PO-SBR runtime is unavailable on the active host/runtime.

Scope:

- available: `analytic_targets`, `hybrid_frames`, `sionna_rt` runtime path generation
- M14.6 baseline status: closed on Linux+NVIDIA (`po_sbr_rt` executed evidence archived)
- this envelope still applies for hosts/environments where PO-SBR runtime is not active

## Evidence Sources

- `/Users/seongcheoljeong/Documents/Codex_test/docs/115_radar_sim_midterm_report_2026_02_22.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/parity_drift_xiangyu_policy_strict_2026_02_21.json`
- `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/measured_replay_summary_policy_strict.json`
- `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/measured_replay_summary_policy_strict.json`
- `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/measured_replay_summary_policy_strict.json`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/m14_6_closure_readiness_2026_02_22.json`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_2026_02_22.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/m14_6_closure_readiness_linux.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_golden_path_local_2026_03_01.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_golden_path_local_2026_03_01_all3.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_campaign_local_2026_03_01_all3.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_golden_path_local_2026_03_01_all3_eqv2.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_campaign_local_2026_03_01_all3_eqv2.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_golden_path_local_2026_03_01_all3_eqv3.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_campaign_local_2026_03_01_all3_eqv3.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_v2.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_v3.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_v4.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_stability_local_2026_03_01.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_stability_local_2026_03_01_r3.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_realism_threshold_hardening_local_2026_03_01.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_realism_threshold_hardening_local_2026_03_01_gate_lock_v2.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01.json`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01_fresh.json`
- `/home/seongcheoljeong/workspace/myproject/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux_2026_03_01_abs.json`
- `/home/seongcheoljeong/workspace/myproject/docs/reports/m14_6_closure_readiness_linux_2026_03_01_abs.json`

## Bottom Line

- Current stack is usable for E2E algorithm development, regression, and pipeline validation.
- PO-SBR strict runtime baseline (M14.6) is now closed on Linux+NVIDIA (`pilot_status=executed`, `ready=true`).
- Scenario-family matrix gate split is active: strict equivalence profiles are gate-required, realism profiles are informational and tracked separately.
- Repeated full-track campaign evidence is stable on this PC (`stable_run_count=3/3`), supporting local self-contained execution confidence.
- Realism KPI thresholds are hardened in stepwise profiles (`realism_tight_v1/v2/v3`) with no parity regressions in the current profile set.
- Candidate lock is promoted locally with one-command gate summary (`realism_tight_v2`, `gate_lock_status=ready`).
- Even with M14.6 closed, dense multipath/material-sensitive angle conclusions should remain conservative when PO-SBR runtime is not active in the current environment.

## Scenario-Class Accuracy Envelope

| Scenario class | Current evidence | Observed envelope | Operational decision |
|---|---|---|---|
| S0: Sparse point-target / controlled scene | AVX-like runtime demo (2 targets, TDM-MIMO) | static range error `+0.0378 m`, moving range error `-0.0993 m`, moving Doppler error `+199.70 Hz` (`~4.86%`) | `GO` for waveform/DSP sanity and integration debug |
| S1: Automotive moderate multipath (BMS family) | Xiangyu strict parity drift (`bms1000_512`, `bms1000_897`) | pass_rate `1.0`; q90 `rd_shape_nmse=0.351~0.363`, q90 `ra_shape_nmse=0.231~0.253`, q90 `ra_centroid_angle_bin_abs_error=1.95~2.00` | `GO` for regression and model iteration |
| S2: Angle-complex / dense multipath (CMS family) | Xiangyu strict parity drift (`cms1000_128`) | pass_rate `1.0`; q90 `ra_shape_nmse=1.647`, q90 `ra_centroid_angle_bin_abs_error=11.78`, q90 `ra_peak_angle_bin_abs_error=44` | `CONDITIONAL`: RD-centric work is usable, angle-critical conclusions are high-risk |

## What Degrades Most Without PO-SBR

1. Angle fidelity under dense multipath/material interactions.
2. Absolute scattering power stability for weak targets near detection threshold.
3. High-confidence ghost/multipath realism claims in complex geometry.

What stays comparatively stable:

1. Basic path-to-ADC synthesis consistency.
2. RD-centric trend comparison and regression gating against fixed baselines.
3. Deterministic reproducibility and workflow automation.

## Go / No-Go by Development Objective

| Objective | Decision (without PO-SBR runtime) | Notes |
|---|---|---|
| Signal-chain development (ADC, FFT, RD/RA plumbing) | `GO` | Core pipeline is stable and validated |
| Baseline-vs-candidate regression gate | `GO` | Strict policy and replay lock flows are operational |
| TDM motion compensation tuning | `GO` | Use scenario-profile lock and replay evidence |
| Angle estimator final tuning for complex urban multipath | `CONDITIONAL` | Require extra safety margin and per-scene review |
| Material-specific scattering realism claim (AVX-level) | `CONDITIONAL` | Require PO-SBR runtime evidence on target environment and scenario-specific review |
| Final physics sign-off for release | `CONDITIONAL` | M14.6 baseline is closed; keep scenario-family parity evidence and guardrails |

## Required Guardrails When PO-SBR Runtime Is Unavailable

1. Treat angle-related KPIs in dense scenes as provisional, not final sign-off evidence.
2. Keep strict replay policy enabled and monitor `ra_shape_nmse`, `ra_centroid_angle_bin_abs_error`, `ra_peak_angle_bin_abs_error`.
3. Use scenario-specific lock profiles; avoid global claims from a single family.
4. Report confidence bands explicitly in external demos/reports ("RD-trust high, angular multipath trust medium/low").

## Closure Criteria for High-Fidelity Physics Claim

M14.6 closure requires:

1. Linux+NVIDIA host strict pilot executed report (`pilot_status=executed`).
2. Runtime blockers cleared (`missing_required_modules`, `unsupported_platform`, `missing_nvidia_runtime` absent).
3. Parity harness rerun with PO-SBR runtime provider and archived comparison report.

Current status:

- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json` -> `pilot_status=executed`, `path_count=8`, `runtime_resolution.mode=runtime_provider`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/m14_6_closure_readiness_linux.json` -> `ready=true`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_golden_path_local_2026_03_01.json` -> `executed=[analytic_targets,po_sbr_rt]`, `blocked=[sionna_rt]`, `po_sbr_migration_status=closed_local_runtime`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_golden_path_local_2026_03_01_all3.json` -> `executed=[analytic_targets,sionna_rt,po_sbr_rt]`, `blocked=[]`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_campaign_local_2026_03_01_all3.json` -> `campaign_status=blocked` (`parity_failure_detected`, strict RD/RA thresholds)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_golden_path_local_2026_03_01_all3_eqv2.json` -> `executed=[analytic_targets,sionna_rt,po_sbr_rt]`, `blocked=[]`, `scene_equivalence_profile=single_target_range25_v1`
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_campaign_local_2026_03_01_all3_eqv2.json` -> `campaign_status=ready` (`parity_fail_count=0`, strict KPI gate pass)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01.json` -> `matrix_status=blocked` (`ready=2`, `blocked=1`, divergence at azimuth profile power delta)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_golden_path_local_2026_03_01_all3_eqv3.json` -> `executed=[analytic_targets,sionna_rt,po_sbr_rt]`, `blocked=[]`, `po_sbr_amp_target_abs` policy active
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_campaign_local_2026_03_01_all3_eqv3.json` -> `campaign_status=ready` (`parity_fail_count=0`, strict KPI gate pass)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_v2.json` -> `matrix_status=ready` (`ready=3`, `blocked=0`, `failed=0`)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_v3.json` -> `matrix_status=ready` (`profile_count=5`, `gate_profile_count=3`, `gate_blocked_profile_count=0`, `informational_profile_count=2`)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_v4.json` -> `matrix_status=ready` (`profile_count=7`, `gate_profile_count=3`, `gate_blocked_profile_count=0`, `informational_profile_count=4`)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json` -> `full_track_status=ready` (`required_profile_count=7`, `missing_profile_count=0`, `po_sbr_executed_profile_count=7`)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_stability_local_2026_03_01.json` -> `campaign_status=stable` (`requested_runs=2`, `stable_run_count=2`, `gate_blocked_run_count=0`)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_stability_local_2026_03_01_r3.json` -> `campaign_status=stable` (`requested_runs=3`, `stable_run_count=3`, `gate_blocked_run_count=0`)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_realism_threshold_hardening_local_2026_03_01.json` -> `hardening_status=hardened` (`threshold_profile_count=3`, `threshold_ready_count=3`, `threshold_failed_count=0`)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_realism_threshold_hardening_local_2026_03_01_gate_lock_v2.json` -> `hardening_status=hardened` (`threshold_profile_count=1`, `realism_gate_candidate=realism_tight_v2`, `realism_gate_candidate_status=ready`)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01.json` -> `gate_lock_status=ready` (`stability_status=stable`, `hardening_status=hardened`, `realism_gate_candidate_status=ready`)
- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01_fresh.json` -> `gate_lock_status=ready` (`stability_status=stable`, `hardening_status=hardened`, `realism_gate_candidate_status=ready`, chained mode)
- `/home/seongcheoljeong/workspace/myproject/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux_2026_03_01_abs.json` -> `pilot_status=executed`, `path_count=8`, `runtime_resolution.mode=runtime_provider`
- `/home/seongcheoljeong/workspace/myproject/docs/reports/m14_6_closure_readiness_linux_2026_03_01_abs.json` -> `ready=true`

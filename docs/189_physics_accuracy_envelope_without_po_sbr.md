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
- `/home/seongcheoljeong/workspace/myproject/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux_2026_03_01_abs.json`
- `/home/seongcheoljeong/workspace/myproject/docs/reports/m14_6_closure_readiness_linux_2026_03_01_abs.json`

## Bottom Line

- Current stack is usable for E2E algorithm development, regression, and pipeline validation.
- PO-SBR strict runtime baseline (M14.6) is now closed on Linux+NVIDIA (`pilot_status=executed`, `ready=true`).
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
- `/home/seongcheoljeong/workspace/myproject/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux_2026_03_01_abs.json` -> `pilot_status=executed`, `path_count=8`, `runtime_resolution.mode=runtime_provider`
- `/home/seongcheoljeong/workspace/myproject/docs/reports/m14_6_closure_readiness_linux_2026_03_01_abs.json` -> `ready=true`

# PO-SBR Linux Runtime Runbook

## Objective

Execute `M14.6` real runtime pilot on a Linux host with NVIDIA GPU runtime.

## Required Host Baseline

1. OS: Linux
2. GPU runtime: `nvidia-smi` available
3. Python modules:
   - `rtxpy` (modified PO-SBR-required build)
   - `igl` (libigl python bindings)
4. reference repo available:
   - `/Users/seongcheoljeong/Documents/Codex_test/external/PO-SBR-Python`

## Preflight Check (same pilot runner)

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_po_sbr_pilot.py \
  --output-root /Users/seongcheoljeong/Documents/Codex_test/data/runtime_pilot/po_sbr_runtime_pilot_v1 \
  --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  --allow-blocked
```

Expected on ready Linux host:

- `pilot_status` becomes `executed` (not `blocked`)

## Environment Bootstrap (Linux)

If `rtxpy`/`igl` are missing, run:

```bash
bash /Users/seongcheoljeong/Documents/Codex_test/scripts/bootstrap_po_sbr_linux_env.sh \
  /Users/seongcheoljeong/Documents/Codex_test/.venv-po-sbr \
  /Users/seongcheoljeong/Documents/Codex_test/external/rtxpy-mod
```

This script:

1. creates/updates a Python venv
2. installs baseline modules (`numpy`, `matplotlib`, `libigl`)
3. clones/updates modified `rtxpy` and installs it editable
4. optionally installs `cupy` when CUDA toolkit is detectable

## Real Pilot Run (strict)

```bash
bash /Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_po_sbr_linux_strict.sh \
  /Users/seongcheoljeong/Documents/Codex_test/data/runtime_pilot/po_sbr_runtime_pilot_v1 \
  /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  /Users/seongcheoljeong/Documents/Codex_test/external/PO-SBR-Python \
  geometries/plate.obj
```

Strict wrapper path handling:

1. script normalizes `output-root`, `summary-json`, and `po-sbr-repo-root` to absolute paths before validation
2. for reproducible logs across hosts, keep passing explicit absolute paths as shown above

## macOS -> Linux Remote One-Shot (SSH)

From local macOS, run remote bootstrap + strict pilot + report download:

```bash
bash /Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_remote_linux_over_ssh.sh \
  --ssh-host <user>@<linux-host> \
  --remote-repo /absolute/path/to/Codex_test \
  --apply-finalize-local
```

Optional flags:

1. `--ssh-port <port>`
2. `--identity-file <path>`
3. `--skip-bootstrap` (if Linux env already prepared)

## Success Criteria

1. summary JSON:
   - `pilot_status = executed`
   - `path_count > 0`
   - `runtime_resolution.mode = runtime_provider`
   - passes validator:
     - `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_runtime_po_sbr_executed_report.py --summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json`
2. artifacts generated:
   - `path_list.json`
   - `adc_cube.npz`
   - `radar_map.npz`
3. closure gate:
   - `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_closure_readiness.py --linux-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/m14_6_closure_readiness_linux.json`
   - output must include `ready=true`
4. optional finalization helper:
   - `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/finalize_m14_6_from_linux_report.py --linux-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json --closure-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/m14_6_closure_readiness_linux.json --apply`

## Myproject Local PO-SBR Full-Track Gate Lock (2026-03-01)

Unblock all-backend runtime modules (once):

```bash
cd /home/seongcheoljeong/workspace/myproject
PYTHONPATH=src .venv-po-sbr/bin/pip install drjit mitsuba
```

Run local all-backend golden-path proof:

```bash
cd /home/seongcheoljeong/workspace/myproject
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_scene_backend_golden_path.py \
  --strict-nonexecuted \
  --output-root data/runtime_golden_path/myproject_local_2026_03_01_all3 \
  --output-summary-json docs/reports/scene_backend_golden_path_myproject_local_2026_03_01_all3.json
```

Run local backend KPI readiness and strict scenario matrix:

```bash
cd /home/seongcheoljeong/workspace/myproject
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_scene_backend_kpi_campaign.py \
  --golden-path-summary-json docs/reports/scene_backend_golden_path_myproject_local_2026_03_01_all3.json \
  --output-summary-json docs/reports/scene_backend_kpi_campaign_myproject_local_2026_03_01_all3.json \
  --strict-ready
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_scene_backend_kpi_scenario_matrix.py \
  --output-root data/runtime_golden_path/scene_backend_kpi_scenario_matrix_myproject_local_2026_03_01_all3 \
  --output-summary-json docs/reports/scene_backend_kpi_scenario_matrix_myproject_local_2026_03_01_all3.json \
  --strict-all-ready
```

Validate migrated deterministic toolchain:

```bash
cd /home/seongcheoljeong/workspace/myproject
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_runtime_provider_stubbed.py
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_run_po_sbr_physical_full_track_gate_lock.py
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_scene_backend_kpi_campaign_report.py \
  --summary-json docs/reports/scene_backend_kpi_campaign_myproject_local_2026_03_01_all3.json \
  --require-ready
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_scene_backend_kpi_scenario_matrix_report.py \
  --summary-json docs/reports/scene_backend_kpi_scenario_matrix_myproject_local_2026_03_01_all3.json \
  --require-ready
```

Generate a myproject gate-lock summary from migrated local evidence:

```bash
cd /home/seongcheoljeong/workspace/myproject
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_po_sbr_physical_full_track_gate_lock.py \
  --strict-ready \
  --full-track-bundle-summary-json docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json \
  --reuse-stability-summary-json docs/reports/po_sbr_physical_full_track_stability_local_2026_03_01_r3.json \
  --reuse-hardening-summary-json docs/reports/po_sbr_realism_threshold_hardening_local_2026_03_01_gate_lock_v2.json \
  --output-root data/runtime_golden_path/po_sbr_physical_full_track_gate_lock_local_2026_03_01_myproject_reuse \
  --output-summary-json docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01_myproject_reuse.json \
  --stability-runs 3 \
  --threshold-profile realism_tight_v2 \
  --realism-gate-candidate realism_tight_v2
```

Run full chained local gate-lock on this PC (no reused summaries):

```bash
cd /home/seongcheoljeong/workspace/myproject
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_po_sbr_physical_full_track_gate_lock.py \
  --strict-ready \
  --full-track-bundle-summary-json docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json \
  --output-root data/runtime_golden_path/po_sbr_physical_full_track_gate_lock_local_2026_03_01_myproject_fresh \
  --output-summary-json docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01_myproject_fresh.json \
  --stability-runs 3 \
  --threshold-profile realism_tight_v2 \
  --realism-gate-candidate realism_tight_v2
```

Validate migrated local evidence reports:

```bash
cd /home/seongcheoljeong/workspace/myproject
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_physical_full_track_stability_report.py \
  --summary-json docs/reports/po_sbr_physical_full_track_stability_local_2026_03_01_r3.json \
  --require-stable
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_realism_threshold_hardening_report.py \
  --summary-json docs/reports/po_sbr_realism_threshold_hardening_local_2026_03_01_gate_lock_v2.json \
  --require-hardened
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_physical_full_track_gate_lock_report.py \
  --summary-json docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01_myproject_reuse.json \
  --require-ready
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_physical_full_track_gate_lock_report.py \
  --summary-json docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01_myproject_fresh.json \
  --require-ready
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_physical_full_track_stability_report.py \
  --summary-json data/runtime_golden_path/po_sbr_physical_full_track_gate_lock_local_2026_03_01_myproject_fresh/stability_campaign/po_sbr_physical_full_track_stability.json \
  --require-stable
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_realism_threshold_hardening_report.py \
  --summary-json data/runtime_golden_path/po_sbr_physical_full_track_gate_lock_local_2026_03_01_myproject_fresh/hardening_campaign/po_sbr_realism_threshold_hardening.json \
  --require-hardened
```

One-command local readiness regression + baseline freeze:

```bash
cd /home/seongcheoljeong/workspace/myproject
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_po_sbr_local_ready_regression.py \
  --strict-ready \
  --output-root data/runtime_golden_path/po_sbr_local_ready_regression_2026_03_01_pc_self \
  --output-summary-json docs/reports/po_sbr_local_ready_regression_2026_03_01_pc_self.json \
  --full-track-bundle-summary-json docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json \
  --stability-runs 3 \
  --threshold-profile realism_tight_v2 \
  --realism-gate-candidate realism_tight_v2
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_local_ready_regression_report.py \
  --summary-json docs/reports/po_sbr_local_ready_regression_2026_03_01_pc_self.json \
  --require-ready
PYTHONPATH=src .venv-po-sbr/bin/python scripts/freeze_po_sbr_local_ready_baseline.py \
  --local-ready-summary-json docs/reports/po_sbr_local_ready_regression_2026_03_01_pc_self.json \
  --output-dir docs/reports/baselines/po_sbr_local_ready_2026_03_01_pc_self \
  --manifest-json docs/reports/baselines/po_sbr_local_ready_2026_03_01_pc_self/baseline_manifest.json \
  --strict-ready
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_local_ready_baseline_manifest.py \
  --manifest-json docs/reports/baselines/po_sbr_local_ready_2026_03_01_pc_self/baseline_manifest.json \
  --require-ready
```

Baseline drift check (candidate local-ready vs frozen baseline):

```bash
cd /home/seongcheoljeong/workspace/myproject
PYTHONPATH=src .venv-po-sbr/bin/python scripts/check_po_sbr_local_ready_baseline_drift.py \
  --baseline-manifest-json docs/reports/baselines/po_sbr_local_ready_2026_03_01_pc_self/baseline_manifest.json \
  --candidate-summary-json docs/reports/po_sbr_local_ready_regression_2026_03_01_pc_self.json \
  --output-json docs/reports/po_sbr_local_ready_baseline_drift_2026_03_01_pc_self.json \
  --require-match \
  --require-candidate-ready
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_local_ready_baseline_drift_report.py \
  --report-json docs/reports/po_sbr_local_ready_baseline_drift_2026_03_01_pc_self.json \
  --require-match
```

Canonical merged-state one-command verifier (Radar-Simulation repo):

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
bash scripts/verify_po_sbr_physical_full_track_merged_ready.sh
```

Operator-handoff closure one-command verifier (frontend M17.97~M17.101 + merged readiness + snapshot):

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
bash scripts/verify_po_sbr_operator_handoff_closure.sh
```

Expected closure snapshot output:

- `docs/reports/po_sbr_operator_handoff_closure_YYYY_MM_DD.json`
- `overall_status=ready`

Post-change automatic gate (runs closure only when runtime-affecting files changed):

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
./scripts/install_po_sbr_pre_push_hook.sh
git config --get core.hooksPath
```

Local pre-push hook smoke check (simulates one branch update line from git pre-push stdin):

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
printf "refs/heads/codex/hybrid-adapter-real-parser %s refs/heads/codex/hybrid-adapter-real-parser %s\n" \
  "$(git rev-parse HEAD)" "$(git rev-parse HEAD~1)" | .githooks/pre-push
```

Hook local-only artifacts (do not dirty tracked files):

- `.git/po_sbr_post_change_gate_hook_latest.json`
- `.git/po_sbr_physical_full_track_merged_checkpoint_hook_latest.json`
- `.git/po_sbr_operator_handoff_closure_hook_latest.json`

Hook local-artifact validator:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
PYTHONPATH=src .venv/bin/python scripts/validate_po_sbr_pre_push_hook_local_artifacts.py
```

Progress snapshot (one command for PO-SBR readiness + myproject migration status + next actions):

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
PYTHONPATH=src .venv/bin/python scripts/show_po_sbr_progress.py \
  --strict-ready \
  --output-json docs/reports/po_sbr_progress_snapshot_2026_03_01.json
```

Full readiness checkpoint refresh (recommended one command):

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
bash scripts/run_po_sbr_readiness_checkpoint.sh
```

`run_po_sbr_readiness_checkpoint.sh` includes the pre-push local-artifact validator by default.  
Set `PO_SBR_SKIP_HOOK_SELFTEST=1` only when you explicitly want to skip that sub-check.

Physical full-track function test (fresh run for radar-developer workflow):

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
bash scripts/run_po_sbr_physical_full_track_function_test.sh
```

Myproject local physical full-track function test (fresh local evidence):

```bash
cd /home/seongcheoljeong/workspace/myproject
bash scripts/run_po_sbr_physical_full_track_function_test.sh
```

Myproject one-command readiness checkpoint (validate latest function-test + local-ready + baseline drift):

```bash
cd /home/seongcheoljeong/workspace/myproject
bash scripts/run_po_sbr_myproject_readiness_checkpoint.sh
```

Manual post-change gate run:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py \
  --base-ref HEAD~1 \
  --head-ref HEAD \
  --strict \
  --output-json docs/reports/po_sbr_post_change_gate_2026_03_01.json
```

Force-run mode (always execute closure gate):

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py \
  --force-run \
  --strict \
  --base-ref HEAD~1 \
  --head-ref HEAD \
  --output-json docs/reports/po_sbr_post_change_gate_2026_03_01.json
```

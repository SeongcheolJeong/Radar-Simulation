# Cross-PC Handoff Checklist

Updated: 2026-02-28
Workspace: `/Users/seongcheoljeong/Documents/Codex_test`
Branch: `codex/hybrid-adapter-real-parser`
Anchor commit: `f744f20`

## 1) Purpose

Use this checklist to continue the same project on another PC with minimal context loss.

What is portable:

- source code and docs (via git)
- run artifacts and reports (if copied)
- milestone and plan state (from docs)

What is not reliably portable:

- Codex app chat/session memory

## 2) Must-carry context files

Read these first on the new PC:

1. `/Users/seongcheoljeong/Documents/Codex_test/docs/01_execution_plan.md`
2. `/Users/seongcheoljeong/Documents/Codex_test/docs/115_radar_sim_midterm_report_2026_02_22.md`
3. `/Users/seongcheoljeong/Documents/Codex_test/docs/117_web_e2e_radar_dev_system_plan.md`
4. `/Users/seongcheoljeong/Documents/Codex_test/docs/189_physics_accuracy_envelope_without_po_sbr.md`
5. `/Users/seongcheoljeong/Documents/Codex_test/docs/113_po_sbr_linux_runtime_runbook.md`

## 3) Source sync from current PC

1. Verify clean/known working tree:

```bash
cd /Users/seongcheoljeong/Documents/Codex_test
git status --short
```

2. Decide about local-only file:

- untracked now: `radar_map_front.jsx.rtf`
- choose one:
  - keep local-only (do nothing)
  - commit it
  - add to `.gitignore`

3. Push branch and tags:

```bash
cd /Users/seongcheoljeong/Documents/Codex_test
git push origin codex/hybrid-adapter-real-parser
```

## 4) Setup on the new PC

1. Clone and checkout:

```bash
git clone <your-remote-url> /path/to/Codex_test
cd /path/to/Codex_test
git checkout codex/hybrid-adapter-real-parser
git pull --ff-only
```

2. Confirm anchor commit exists:

```bash
git log --oneline -n 10
```

3. Validate python entrypoint quickly:

```bash
PYTHONPATH=src python3 scripts/validate_step1.py
```

## 5) If target is Linux + NVIDIA for PO-SBR (M14.6)

1. Host prerequisites:

- Linux
- `nvidia-smi` works
- Python3 + git

2. Bootstrap:

```bash
bash scripts/bootstrap_po_sbr_linux_env.sh .venv-po-sbr external/rtxpy-mod
```

3. Pilot preflight (allow blocked):

```bash
PYTHONPATH=src python3 scripts/run_scene_runtime_po_sbr_pilot.py \
  --output-root data/runtime_pilot/po_sbr_runtime_pilot_v1 \
  --output-summary-json docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  --allow-blocked
```

4. Strict execution:

```bash
bash scripts/run_m14_6_po_sbr_linux_strict.sh \
  data/runtime_pilot/po_sbr_runtime_pilot_v1 \
  docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  external/PO-SBR-Python \
  geometries/plate.obj
```

5. Closure readiness:

```bash
PYTHONPATH=src python3 scripts/run_m14_6_closure_readiness.py \
  --linux-summary-json docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  --output-summary-json docs/reports/m14_6_closure_readiness_linux.json
```

Expected close signal:

- `pilot_status=executed`
- closure `ready=true`

## 6) Codex restart prompt template

Use this on the new PC as the first message:

```text
Continue AVX-like radar simulator work from branch codex/hybrid-adapter-real-parser.
Read docs/01_execution_plan.md, docs/189_physics_accuracy_envelope_without_po_sbr.md,
and docs/113_po_sbr_linux_runtime_runbook.md first.
Current priority: close M14.6 (PO-SBR Linux+NVIDIA executed evidence),
then update execution plan and reports.
```

## 7) Quick health check after handoff

Run:

```bash
git status --short
PYTHONPATH=src python3 scripts/validate_step1.py
PYTHONPATH=src python3 scripts/validate_object_scene_to_radar_map.py
```

If all pass, handoff is complete and work can continue from M14.6.

## 8) Myproject PO-SBR Full-Track Migration Snapshot (2026-03-01)

Must-read added contracts:

1. `docs/251_scene_backend_golden_path_contract.md`
2. `docs/252_scene_backend_kpi_campaign_contract.md`
3. `docs/253_scene_backend_kpi_scenario_matrix_contract.md`
4. `docs/260_po_sbr_physical_full_track_bundle_contract.md`
5. `docs/261_po_sbr_physical_full_track_stability_contract.md`
6. `docs/262_po_sbr_realism_threshold_hardening_contract.md`
7. `docs/263_po_sbr_physical_full_track_gate_lock_contract.md`

Current backend priority on this PC:

- keep `campaign_status=stable` + `hardening_status=hardened` + `gate_lock_status=ready` green in `/home/seongcheoljeong/workspace/myproject/docs/reports`
- use local Linux execution only (no macOS<->Linux remote orchestration)

Latest local-only execution proof (no cross-PC linkage):

- `/home/seongcheoljeong/workspace/myproject/docs/reports/scene_backend_golden_path_myproject_local_2026_03_01_all3.json` (`executed_backends=[analytic_targets,sionna_rt,po_sbr_rt]`)
- `/home/seongcheoljeong/workspace/myproject/docs/reports/scene_backend_kpi_campaign_myproject_local_2026_03_01_all3.json` (`campaign_status=ready`, `parity_fail_count=0`)
- `/home/seongcheoljeong/workspace/myproject/docs/reports/scene_backend_kpi_scenario_matrix_myproject_local_2026_03_01_all3.json` (`matrix_status=ready`, `profile_count=7`)
- `/home/seongcheoljeong/workspace/myproject/docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01_myproject_fresh.json` (`gate_lock_status=ready`, `stability_status=stable`, `hardening_status=hardened`)
- `/home/seongcheoljeong/workspace/myproject/docs/reports/po_sbr_local_ready_regression_2026_03_01_pc_self.json` (`overall_status=ready`, one-command local chain)
- `/home/seongcheoljeong/workspace/myproject/docs/reports/baselines/po_sbr_local_ready_2026_03_01_pc_self/baseline_manifest.json` (`baseline_status=ready`, frozen_file_count=8)
- `/home/seongcheoljeong/workspace/myproject/docs/reports/po_sbr_local_ready_baseline_drift_2026_03_01_pc_self.json` (`drift_verdict=match`, `difference_count=0`)

## 9) Current Merged Checkpoint on This Linux PC (2026-03-01)

Canonical workspace now:

- `/home/seongcheoljeong/workspace/Radar-Simulation`

Canonical branch now:

- `codex/hybrid-adapter-real-parser` (clean, tracking `origin/codex/hybrid-adapter-real-parser`)

Merged readiness commit:

- merge commit: `406146d` (PR #4 merged into `codex/hybrid-adapter-real-parser`)

Pinned readiness tags:

- `po-sbr-physical-full-track-ready-2026-03-01` -> commit `6406e9e` (snapshot commit)
- `po-sbr-physical-full-track-ready-merged-2026-03-01` -> commit `406146d` (merged-base checkpoint)

Merged checkpoint artifact:

- `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json` (`ready=true`, includes PR/commit/tag pointers)

Minimum post-handoff verification on this repo:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
git checkout codex/hybrid-adapter-real-parser
git pull --ff-only
git status --short

PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_scene_backend_kpi_scenario_matrix_report.py \
  --summary-json docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_fresh.json \
  --require-ready

PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_physical_full_track_bundle_report.py \
  --summary-json docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01_fresh.json \
  --require-ready

PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_physical_full_track_gate_lock_report.py \
  --summary-json docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01_fresh3.json \
  --require-ready
```

Expected green state:

- `matrix_status=ready`
- `full_track_status=ready`
- `gate_lock_status=ready`

One-file readiness check:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path('/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json')
d = json.loads(p.read_text())
print('ready=', d.get('ready'))
print('head_commit=', d.get('head_commit'))
print('merged_readiness_commit=', d.get('merged_readiness_commit'))
PY
```

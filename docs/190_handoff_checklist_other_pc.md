# Cross-PC Handoff Checklist

Updated: 2026-03-01
Workspace: `/home/seongcheoljeong/workspace/Radar-Simulation`
Branch: `codex/hybrid-adapter-real-parser`
Anchor commit (canonical tag): `5d03d06` (`po-sbr-physical-full-track-canonical-2026-03-01`)

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

1. `/home/seongcheoljeong/workspace/Radar-Simulation/docs/01_execution_plan.md`
2. `/home/seongcheoljeong/workspace/Radar-Simulation/docs/113_po_sbr_linux_runtime_runbook.md`
3. `/home/seongcheoljeong/workspace/Radar-Simulation/docs/189_physics_accuracy_envelope_without_po_sbr.md`
4. `/home/seongcheoljeong/workspace/Radar-Simulation/docs/190_handoff_checklist_other_pc.md`
5. `/home/seongcheoljeong/workspace/Radar-Simulation/docs/reports/po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json`

## 3) Source sync from current PC

1. Verify clean/known working tree:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
git status --short
```

2. Refresh remotes and confirm branch tracking:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
git fetch origin
git checkout codex/hybrid-adapter-real-parser
git pull --ff-only origin codex/hybrid-adapter-real-parser
```

3. Push branch and tags:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
git push origin codex/hybrid-adapter-real-parser
git push origin --tags
```

## 4) Setup on the new PC

1. Clone and checkout:

```bash
git clone https://github.com/SeongcheolJeong/Radar-Simulation.git /path/to/Radar-Simulation
cd /path/to/Radar-Simulation
git checkout codex/hybrid-adapter-real-parser
git pull --ff-only
```

2. Confirm anchor commit exists:

```bash
git log --oneline -n 10
```

3. Validate python entrypoint quickly:

```bash
bash scripts/verify_po_sbr_physical_full_track_merged_ready.sh
bash scripts/verify_po_sbr_operator_handoff_closure.sh
./scripts/install_po_sbr_pre_push_hook.sh
git config --get core.hooksPath
bash scripts/run_po_sbr_readiness_checkpoint.sh
printf "refs/heads/codex/hybrid-adapter-real-parser %s refs/heads/codex/hybrid-adapter-real-parser %s\n" \
  "$(git rev-parse HEAD)" "$(git rev-parse HEAD~1)" | .githooks/pre-push
PYTHONPATH=src .venv/bin/python scripts/show_po_sbr_progress.py --strict-ready --output-json docs/reports/po_sbr_progress_snapshot_2026_03_01.json
PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py --base-ref HEAD~1 --head-ref HEAD --strict
```

## 5) If target must rebuild Linux + NVIDIA runtime from scratch

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

After runtime/bootstrap is rebuilt, run the canonical merged-state verifier:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
bash scripts/verify_po_sbr_physical_full_track_merged_ready.sh
```

## 6) Codex restart prompt template

Use this on the new PC as the first message:

```text
Continue AVX-like radar simulator work from branch codex/hybrid-adapter-real-parser.
Read docs/01_execution_plan.md, docs/189_physics_accuracy_envelope_without_po_sbr.md,
and docs/113_po_sbr_linux_runtime_runbook.md first.
Current priority: keep merged PO-SBR physical full-track readiness green on this Linux PC
using scripts/verify_po_sbr_physical_full_track_merged_ready.sh, then continue feature work.
```

## 7) Quick health check after handoff

Run:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
git status --short
./scripts/install_po_sbr_pre_push_hook.sh
git config --get core.hooksPath
bash scripts/run_po_sbr_readiness_checkpoint.sh
bash scripts/verify_po_sbr_physical_full_track_merged_ready.sh
bash scripts/verify_po_sbr_operator_handoff_closure.sh
printf "refs/heads/codex/hybrid-adapter-real-parser %s refs/heads/codex/hybrid-adapter-real-parser %s\n" \
  "$(git rev-parse HEAD)" "$(git rev-parse HEAD~1)" | .githooks/pre-push
PYTHONPATH=src .venv/bin/python scripts/show_po_sbr_progress.py --strict-ready --output-json docs/reports/po_sbr_progress_snapshot_2026_03_01.json
PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py --base-ref HEAD~1 --head-ref HEAD --strict
```

If all pass, handoff is complete and work can continue from merged full-track readiness baseline.

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
- `po-sbr-physical-full-track-canonical-2026-03-01` -> canonical branch tip at tagging time (post-merge ops/docs lock)

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

One-command equivalent:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
bash scripts/verify_po_sbr_physical_full_track_merged_ready.sh
```

Checkpoint refresh only:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
PYTHONPATH=src .venv-po-sbr/bin/python scripts/generate_po_sbr_physical_full_track_merged_checkpoint.py \
  --output-json docs/reports/po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json
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
print('generated_from_head_commit=', d.get('generated_from_head_commit'))
print('merged_readiness_commit=', d.get('merged_readiness_commit'))
PY
```

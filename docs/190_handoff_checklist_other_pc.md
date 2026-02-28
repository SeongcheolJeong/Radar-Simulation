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

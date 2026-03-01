# Cross-PC Handoff Checklist

Updated: 2026-03-01
Workspace: `/home/seongcheoljeong/workspace/Radar-Simulation`
Branch: `codex/hybrid-adapter-real-parser`

## 1) Purpose

Use this checklist to continue the same project on another PC with minimal context loss.

Portable:

- source code + docs (git)
- generated reports/artifacts (if copied)
- milestone state (`docs/01_execution_plan.md`)

Non-portable:

- Codex chat/session memory

## 2) Must-Read Context Files

1. `docs/01_execution_plan.md`
2. `docs/115_radar_sim_midterm_report_2026_02_22.md`
3. `docs/117_web_e2e_radar_dev_system_plan.md`
4. `docs/189_physics_accuracy_envelope_without_po_sbr.md`
5. `docs/113_po_sbr_linux_runtime_runbook.md`

## 3) Source Sync from Current PC

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
git status --short
git push origin codex/hybrid-adapter-real-parser
```

## 4) Setup on New PC

```bash
git clone <your-remote-url> /home/seongcheoljeong/workspace/Radar-Simulation
cd /home/seongcheoljeong/workspace/Radar-Simulation
git checkout codex/hybrid-adapter-real-parser
git pull --ff-only
PYTHONPATH=src python3 scripts/validate_step1.py
```

## 5) Local Linux+NVIDIA PO-SBR Run (No Remote Dependency)

Run fully on the Linux PC itself:

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
bash scripts/run_m14_6_local_linux_full.sh
```

This local one-shot includes:

1. Linux bootstrap (`rtxpy`/`igl` runtime prep)
2. strict pilot execution
3. closure readiness generation
4. optional finalize `--apply`

Expected close signal:

- `pilot_status=executed`
- closure `ready=true`

## 6) Codex Restart Prompt Template

```text
Continue work from branch codex/hybrid-adapter-real-parser.
Read docs/01_execution_plan.md, docs/189_physics_accuracy_envelope_without_po_sbr.md,
and docs/113_po_sbr_linux_runtime_runbook.md first.
Use local Linux execution only (no macOS<->Linux remote orchestration).
Current priority: continue frontend hardening from latest open M17 milestone.
```

## 7) Quick Health Check

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
git status --short
PYTHONPATH=src python3 scripts/validate_step1.py
PYTHONPATH=src python3 scripts/validate_object_scene_to_radar_map.py
```

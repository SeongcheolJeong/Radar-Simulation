# Worktree Commit Partition Plan (2026-03-04)

## Snapshot
- Branch: `main` (synced with `origin/main` at `edb5ecb`)
- Uncommitted files: `123`
- Modified tracked files: `23`
- Untracked files: `100`

Current dirty-set distribution:
- `docs_specs`: `4`
- `frontend`: `9`
- `scripts`: `22`
- `src_runtime`: `5`
- `docs_reports`: `83`

## Current Progress Status (from latest reports)
- Frontend Playwright E2E strict report: `pass` (`docs/reports/graph_lab_playwright_e2e_latest.json`)
- Production release gate (`paid_6m`): `ready` and `blockers=0`
- Readiness checkpoint (`paid_6m`): `overall_status=ready`
- Final status summary: `overall_ready=true`

## Recommended Commit Sequence
1. Frontend workbench + frontend API bridge
2. Runtime core/provider/API implementation
3. Runner/validator scripts
4. Contracts and policy docs
5. Generated reports (final evidence bundle)

## Commit 1: Frontend Workbench
Paths:
- `frontend/graph_lab_reactflow.html`
- `frontend/graph_lab/api_client.mjs`
- `frontend/graph_lab/app.mjs`
- `frontend/graph_lab/contracts.mjs`
- `frontend/graph_lab/deps.mjs`
- `frontend/graph_lab/hooks/use_gate_ops.mjs`
- `frontend/graph_lab/hooks/use_graph_run_ops.mjs`
- `frontend/graph_lab/panels.mjs`
- `frontend/graph_lab/panels/`
- `src/avxsim/web_e2e_api.py`

Commands:
```bash
git add \
  frontend/graph_lab_reactflow.html \
  frontend/graph_lab/api_client.mjs \
  frontend/graph_lab/app.mjs \
  frontend/graph_lab/contracts.mjs \
  frontend/graph_lab/deps.mjs \
  frontend/graph_lab/hooks/use_gate_ops.mjs \
  frontend/graph_lab/hooks/use_graph_run_ops.mjs \
  frontend/graph_lab/panels.mjs \
  frontend/graph_lab/panels \
  src/avxsim/web_e2e_api.py
git commit -m "feat(frontend): advance graph lab workbench and e2e api bridge"
```

Quick checks:
```bash
node --check frontend/graph_lab/app.mjs
node --check frontend/graph_lab/panels.mjs
PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py --require-playwright --strict-visual
```

## Commit 2: Runtime Core and Provider
Paths:
- `src/avxsim/radarsimpy_api.py`
- `src/avxsim/radarsimpy_core_model.py`
- `src/avxsim/radarsimpy_core_simulator.py`
- `src/avxsim/runtime_providers/radarsimpy_rt_provider.py`

Commands:
```bash
git add \
  src/avxsim/radarsimpy_api.py \
  src/avxsim/radarsimpy_core_model.py \
  src/avxsim/radarsimpy_core_simulator.py \
  src/avxsim/runtime_providers/radarsimpy_rt_provider.py
git commit -m "feat(runtime): add RadarSimPy core model/simulator and provider integration"
```

## Commit 3: Runners and Validators
Paths:
- `scripts/build_radarsimpy_native_parity_fixtures.py`
- `scripts/build_radarsimpy_signature_manifest.py`
- `scripts/run_radarsimpy_integration_smoke_gate.py`
- `scripts/run_radarsimpy_layered_parity_suite.py`
- `scripts/run_radarsimpy_production_gate_from_order.py`
- `scripts/run_radarsimpy_production_release_gate.py`
- `scripts/run_radarsimpy_readiness_checkpoint.py`
- `scripts/run_radarsimpy_wrapper_integration_gate.py`
- `scripts/validate_build_radarsimpy_native_parity_fixtures.py`
- `scripts/validate_build_radarsimpy_signature_manifest.py`
- `scripts/validate_radarsimpy_layered_reference_parity_optional.py`
- `scripts/validate_radarsimpy_readiness_checkpoint_report.py`
- `scripts/validate_radarsimpy_root_model_core_fallback.py`
- `scripts/validate_radarsimpy_runtime_license_policy.py`
- `scripts/validate_radarsimpy_simulator_core_fallback.py`
- `scripts/validate_radarsimpy_simulator_reference_parity_optional.py`
- `scripts/validate_run_radarsimpy_integration_smoke_gate.py`
- `scripts/validate_run_radarsimpy_layered_parity_suite.py`
- `scripts/validate_run_radarsimpy_production_gate_from_order.py`
- `scripts/validate_run_radarsimpy_production_release_gate.py`
- `scripts/validate_run_radarsimpy_simulator_reference_parity_optional.py`
- `scripts/validate_run_radarsimpy_wrapper_integration_gate.py`

Commands:
```bash
git add scripts/
git commit -m "feat(radarsimpy): expand layered parity, release gate, and validator suite"
```

## Commit 4: Contracts and Policy Docs
Paths:
- `docs/274_radarsimpy_real_functional_migration_contract.md`
- `docs/275_radarsimpy_api_coverage_excluding_sim_lidar.md`
- `docs/276_radarsimpy_native_migration_status_2026_03_03.md`
- `docs/radarsimpy_runtime_license_policy.json`

Commands:
```bash
git add \
  docs/274_radarsimpy_real_functional_migration_contract.md \
  docs/275_radarsimpy_api_coverage_excluding_sim_lidar.md \
  docs/276_radarsimpy_native_migration_status_2026_03_03.md \
  docs/radarsimpy_runtime_license_policy.json
git commit -m "docs(radarsimpy): update migration contracts and runtime license policy"
```

## Commit 5: Evidence Reports Bundle
Paths:
- `docs/reports/*` (current dirty set contains 83 files)

Commands:
```bash
git add docs/reports
git commit -m "chore(reports): snapshot latest RadarSimPy gate/parity/readiness evidence"
```

## Post-Sequence Push
```bash
git push origin main
```

## Notes
- The reports commit is intentionally last so it captures final post-change evidence.
- If you want smaller report commits, split by family prefix:
  - `radarsimpy_function_*`
  - `radarsimpy_production_*`
  - `radarsimpy_layered_*`
  - `radarsimpy_wrapper_*`
  - `radarsimpy_integration_*`

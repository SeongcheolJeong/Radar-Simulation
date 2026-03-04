# RadarSimPy CI Workflow Template

This repository stores the RadarSimPy CI workflow as a template:

- `docs/ci/radarsimpy-integration-smoke.workflow.yml`

Use this command to install/sync it into GitHub Actions workflow location:

```bash
python scripts/install_radarsimpy_ci_workflow.py
```

Check-only mode (for local/CI policy checks):

```bash
python scripts/install_radarsimpy_ci_workflow.py --check
```

Layered parity suite policy used by CI:

- Trial track runs always, but runtime-required mode is enabled only when the trial package root exists:
  - `external/radarsimpy_trial/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU/radarsimpy`
- Production track runtime-required mode is enabled only when both conditions are true:
  - `RADARSIMPY_LICENSE_FILE` is set
  - trial runtime package root above exists

Example local command (policy-equivalent):

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_layered_parity_suite.py \
  --output-json docs/reports/radarsimpy_layered_parity_suite_ci_summary.json \
  --require-runtime-trial \
  --trial-package-root external/radarsimpy_trial/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU \
  --libcompat-dir external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu
```

Graph Lab frontend strict visual policy used by CI:

- Run Playwright E2E with hard runtime requirement:
  - `--require-playwright --strict-visual`
- Output report:
  - `docs/reports/graph_lab_playwright_e2e_ci_summary.json`

Example local command (policy-equivalent):

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py \
  --require-playwright \
  --strict-visual \
  --output-json docs/reports/graph_lab_playwright_e2e_ci_summary.json
```

RadarSimPy readiness checkpoint (single report with ready/blocked status):

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_readiness_checkpoint.py \
  --output-json docs/reports/radarsimpy_readiness_checkpoint_latest.json
```

RadarSimPy production release gate (auto-discover `.lic`, then run strict production checkpoint):

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_production_release_gate.py \
  --output-json docs/reports/radarsimpy_production_release_gate_latest.json
```

RadarSimPy production gate from order URL (parse downloads -> pull assets -> detect `.lic` -> chain production gate):

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_production_gate_from_order.py \
  --order-received-url "https://radarsimx.com/checkout/order-received/<ID>/?key=wc_order_<KEY>" \
  --download-label Ubuntu24_x86_64_CPU.zip \
  --run-production-gate \
  --allow-blocked \
  --output-json docs/reports/radarsimpy_production_gate_from_order_latest.json
```

Notes:

- Writing `.github/workflows/*` on GitHub requires a token with `workflow` scope.
- If push is blocked due workflow scope, keep using the template file and run the install command from an environment that has required permission.

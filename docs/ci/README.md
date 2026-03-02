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

RadarSimPy readiness checkpoint (single report with ready/blocked status):

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_readiness_checkpoint.py \
  --output-json docs/reports/radarsimpy_readiness_checkpoint_latest.json
```

Notes:

- Writing `.github/workflows/*` on GitHub requires a token with `workflow` scope.
- If push is blocked due workflow scope, keep using the template file and run the install command from an environment that has required permission.

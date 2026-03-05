# RadarSimPy Report Retention Policy (2026-03-05)

## Why

`docs/reports` accumulates timestamped checkpoint JSON files from repeated gate/parity runs.
This can grow quickly and inflate repository churn/size.

## Scope

Retention automation targets timestamped RadarSimPy checkpoint artifacts:

- `radarsimpy_*_checkpoint_*.json`
- `radarsimpy_progress_snapshot_*.json`

Non-checkpoint canonical files (for example `*_latest.json`, `*_current.json`, `*_paid_6m.json`) are not targeted.

## Policy

- Keep latest `N` files per checkpoint group (`N=8` default).
- Audit-only mode is default (no deletion).
- Deletion requires explicit opt-in (`--apply` / `APPLY_MODE=1`).

## Commands

Dry-run audit:

```bash
scripts/run_radarsimpy_report_retention_audit.sh
```

Explicit prune (destructive):

```bash
APPLY_MODE=1 KEEP_PER_GROUP=8 scripts/run_radarsimpy_report_retention_audit.sh
```

Direct script usage:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_radarsimpy_report_retention.py \
  --reports-root docs/reports \
  --keep-per-group 8 \
  --output-json docs/reports/radarsimpy_report_retention_audit_latest.json \
  --output-md docs/reports/radarsimpy_report_retention_audit_latest.md
```

## CI

Workflow:

- `.github/workflows/radarsimpy-report-retention-audit.yml`

Behavior:

- scheduled weekly dry-run audit
- manual dispatch with configurable `keep_per_group`
- uploads audit JSON/MD as workflow artifacts

## Outputs

- `docs/reports/radarsimpy_report_retention_audit_latest.json`
- `docs/reports/radarsimpy_report_retention_audit_latest.md`

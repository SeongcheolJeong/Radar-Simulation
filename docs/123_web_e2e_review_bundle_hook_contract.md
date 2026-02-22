# Web E2E Review Bundle Hook Contract (M15.10)

## Goal

Enable one-click review handoff from dashboard by exporting a regression bundle (if needed) and copying the package path to clipboard.

Implementation:

- dashboard: `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`

## UI Controls

- `copyReviewBundleBtn`
- `reviewBundleStatus`
- `reviewBundlePathBox`

## Hook Flow

1. resolve active `session_id` from input/selection
2. create/reuse export via `POST /api/regression-exports`
   - `include_policy_payload=true`
   - `tag=dashboard_review_bundle`
3. resolve review bundle path from export artifacts
   - preferred: `artifacts.package_json`
   - fallback: `artifacts.artifact_dir`
4. copy path to clipboard (`navigator.clipboard` fallback included)
5. update status/path UI and refresh history

## Validation

```bash
scripts/run_web_e2e_dashboard_local.sh 8098 8118
curl -s http://127.0.0.1:8118/health
curl -s "http://127.0.0.1:8098/frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json"
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. dashboard HTML contains review-bundle controls (`copyReviewBundleBtn`, `reviewBundlePathBox`)
2. dashboard JS contains hook functions (`runReviewBundleCopyHook`, `copyTextToClipboard`)
3. hook uses `regression-exports` API and updates copied path/status

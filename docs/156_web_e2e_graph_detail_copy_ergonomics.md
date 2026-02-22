# Web E2E Graph Detail Copy Ergonomics (M17.23)

## Goal

Reduce friction when sharing contract-detail evidence during triage.

1. copy a single row detail quickly
2. copy current visible row-window detail as one payload
3. expose explicit copy success/failure status

Implementation:

- detail copy helpers + row/window actions + status line:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- overlay-level copy:
  - action: `Copy Visible`
  - payload scope: current row-window (`visibleRows`) only
  - payload includes row header (`row#, run, source`) + selected detail fields
- row-level copy:
  - action: `Copy` on compact/full row actions (including non-run rows)
  - payload includes row header + selected detail fields
- clipboard behavior:
  - helper: `copyTextToClipboard(text, label)`
  - status line: `co_detail_copy_status` (`detail_copy: ...`)
  - fallback statuses when clipboard API unavailable or write fails
- field-toggle interaction:
  - copied text is produced via `formatRowDetailText(row)`
  - current field toggle/preset selection is respected

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8154 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8134
curl -s "http://127.0.0.1:8134/frontend/graph_lab/panels.mjs" | rg -n "detailCopyStatus|copyTextToClipboard|copyVisibleDetailRows|copySingleRowDetails|Copy Visible|co_copy_visible_details|co_detail_copy_status|co_row_copy_|co_row_copy_compact_|co_row_copy_only_|detail_copy:"
```

Pass criteria:

1. detail copy helper/action/status tokens are present
2. row/window copy action tokens are present
3. backend regression remains pass

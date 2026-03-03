# Graph Lab Playwright Snapshots

This folder stores visual-regression artifacts for `scripts/validate_graph_lab_playwright_e2e.py`.

- `baseline/`: reference screenshots used for visual comparison.
- `latest/`: most recent captured screenshots and exported decision brief.

Notes:
- Strict visual comparison currently targets stable anchors only:
  - `topbar.png`
  - `decision_pane.png`
  - `artifact_inspector.png`
- Other captures (`page_full.png`, `left_panel.png`, `right_panel.png`) are still generated for manual inspection.

Typical workflow:

1. Capture and refresh baseline:
   - `PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py --update-baseline`
2. Run normal E2E + visual diff:
   - `PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py`
3. Enforce strict visual gating:
   - `PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py --strict-visual --require-playwright`

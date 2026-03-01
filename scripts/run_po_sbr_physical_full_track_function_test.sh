#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "${ROOT_DIR}"

DATE_STAMP="${1:-$(date -u +%Y_%m_%d)}"
HEAD_SHORT="$(git rev-parse --short HEAD)"

PY_BIN=""
for candidate in \
  "${ROOT_DIR}/.venv-po-sbr/bin/python" \
  "${ROOT_DIR}/.venv/bin/python" \
  "python3"; do
  if [[ "${candidate}" == "python3" ]]; then
    if command -v python3 >/dev/null 2>&1; then
      PY_BIN="python3"
      break
    fi
  elif [[ -x "${candidate}" ]]; then
    PY_BIN="${candidate}"
    break
  fi
done

if [[ -z "${PY_BIN}" ]]; then
  echo "[function-test] error: python runtime not found (.venv-po-sbr/.venv/python3)" >&2
  exit 1
fi

RUN_ID="${DATE_STAMP}_${HEAD_SHORT}"
OUTPUT_ROOT="${ROOT_DIR}/data/runtime_golden_path/po_sbr_physical_full_track_function_test_${RUN_ID}"
BUNDLE_OUTPUT_ROOT="${OUTPUT_ROOT}/bundle"
GATE_LOCK_OUTPUT_ROOT="${OUTPUT_ROOT}/gate_lock"

BUNDLE_JSON="${ROOT_DIR}/docs/reports/po_sbr_physical_full_track_bundle_function_test_${RUN_ID}.json"
GATE_LOCK_JSON="${ROOT_DIR}/docs/reports/po_sbr_physical_full_track_gate_lock_function_test_${RUN_ID}.json"
PROGRESS_JSON="${ROOT_DIR}/docs/reports/po_sbr_progress_snapshot_function_test_${RUN_ID}.json"
FUNCTION_TEST_JSON="${ROOT_DIR}/docs/reports/po_sbr_physical_full_track_function_test_${RUN_ID}.json"

mkdir -p "${BUNDLE_OUTPUT_ROOT}" "${GATE_LOCK_OUTPUT_ROOT}" "${ROOT_DIR}/docs/reports"

echo "[function-test] start run_id=${RUN_ID}"
echo "[function-test] python=${PY_BIN}"

echo "[function-test] run full-track bundle (fresh)"
PYTHONPATH=src "${PY_BIN}" scripts/run_po_sbr_physical_full_track_bundle.py \
  --strict-ready \
  --output-root "${BUNDLE_OUTPUT_ROOT}" \
  --output-summary-json "${BUNDLE_JSON}"

echo "[function-test] validate full-track bundle"
PYTHONPATH=src "${PY_BIN}" scripts/validate_po_sbr_physical_full_track_bundle_report.py \
  --summary-json "${BUNDLE_JSON}" \
  --require-ready

echo "[function-test] run full-track gate lock (fresh)"
PYTHONPATH=src "${PY_BIN}" scripts/run_po_sbr_physical_full_track_gate_lock.py \
  --strict-ready \
  --full-track-bundle-summary-json "${BUNDLE_JSON}" \
  --output-root "${GATE_LOCK_OUTPUT_ROOT}" \
  --output-summary-json "${GATE_LOCK_JSON}" \
  --stability-runs 3 \
  --realism-gate-candidate realism_tight_v2 \
  --threshold-profile realism_tight_v2

echo "[function-test] validate full-track gate lock"
PYTHONPATH=src "${PY_BIN}" scripts/validate_po_sbr_physical_full_track_gate_lock_report.py \
  --summary-json "${GATE_LOCK_JSON}" \
  --require-ready

echo "[function-test] progress snapshot"
PYTHONPATH=src "${PY_BIN}" scripts/show_po_sbr_progress.py \
  --strict-ready \
  --output-json "${PROGRESS_JSON}"

echo "[function-test] write summary report"
PYTHONPATH=src "${PY_BIN}" - "${ROOT_DIR}" "${BUNDLE_JSON}" "${GATE_LOCK_JSON}" "${PROGRESS_JSON}" "${FUNCTION_TEST_JSON}" "${RUN_ID}" <<'PY'
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    bundle_json = Path(sys.argv[2]).resolve()
    gate_lock_json = Path(sys.argv[3]).resolve()
    progress_json = Path(sys.argv[4]).resolve()
    out_json = Path(sys.argv[5]).resolve()
    run_id = str(sys.argv[6])

    bundle = _load(bundle_json)
    gate_lock = _load(gate_lock_json)
    progress = _load(progress_json)

    full_track_status = str(bundle.get("full_track_status", "")).strip()
    gate_lock_status = str(gate_lock.get("gate_lock_status", "")).strip()
    progress_ready = bool(progress.get("overall_ready", False))

    overall_status = (
        "ready"
        if (
            full_track_status == "ready"
            and gate_lock_status == "ready"
            and progress_ready
        )
        else "blocked"
    )

    report = {
        "report_name": "po_sbr_physical_full_track_function_test",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(root),
        "run_id": run_id,
        "branch": _git(root, "branch", "--show-current"),
        "head_commit": _git(root, "rev-parse", "HEAD"),
        "bundle_summary_json": str(bundle_json),
        "gate_lock_summary_json": str(gate_lock_json),
        "progress_summary_json": str(progress_json),
        "full_track_status": full_track_status,
        "gate_lock_status": gate_lock_status,
        "progress_overall_ready": progress_ready,
        "overall_status": overall_status,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"overall_status={overall_status}")

    if overall_status != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
PY

echo "[function-test] done"
echo "[function-test] bundle_json=${BUNDLE_JSON}"
echo "[function-test] gate_lock_json=${GATE_LOCK_JSON}"
echo "[function-test] progress_json=${PROGRESS_JSON}"
echo "[function-test] function_test_json=${FUNCTION_TEST_JSON}"

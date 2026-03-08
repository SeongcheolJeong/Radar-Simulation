#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/4] validate release-closure handoff bundle"
python3 scripts/validate_release_closure_handoff_bundle.py

echo "[2/4] validate release announcement pack"
python3 scripts/validate_release_announcement_pack.py \
  --pack-json docs/reports/release_announcement_pack_latest.json

echo "[3/4] verify canonical release-candidate subset status"
python3 - <<'PY'
import json
from pathlib import Path

path = Path("docs/reports/canonical_release_candidate_subset_latest.json")
payload = json.loads(path.read_text(encoding="utf-8"))
if not bool(payload.get("pass", False)):
    raise SystemExit("canonical release-candidate subset is not pass=true")
print(json.dumps(
    {
        "status": "pass",
        "path": str(path),
        "pass": bool(payload.get("pass", False)),
        "step_count": int(payload.get("step_count", 0) or 0),
        "pass_count": int(payload.get("pass_count", 0) or 0),
        "with_sionna": bool(payload.get("with_sionna", False)),
    },
    indent=2,
))
PY

echo "[4/4] print handoff deliverables"
python3 - <<'PY'
import json
from pathlib import Path

files = [
    "docs/294_release_closure_handoff_2026_03_08.md",
    "docs/295_release_closure_handoff_2026_03_08_ko.md",
    "docs/296_release_closure_final_announcement_2026_03_08.md",
    "docs/297_release_closure_final_announcement_2026_03_08_ko.md",
    "docs/291_release_candidate_snapshot_2026_03_08.md",
    "docs/292_release_candidate_snapshot_2026_03_08_ko.md",
    "docs/reports/README.md",
    "docs/reports/canonical_release_candidate_subset_latest.json",
    "docs/reports/release_announcement_pack_latest.md",
    "docs/reports/release_closure_handoff_bundle_latest.tar.gz",
    "docs/reports/release_closure_handoff_bundle_latest_manifest.json",
]
rows = []
for raw in files:
    path = Path(raw)
    rows.append(
        {
            "path": raw,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
        }
    )
print(json.dumps({"deliverables": rows}, indent=2))
PY

echo "release-closure handoff pre-send check: ready"

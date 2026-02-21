#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import numpy as np

from avxsim.parity import compare_hybrid_estimation_payloads
from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run object-scene pipelines for two backends and evaluate RD/RA parity "
            "using shared parity metrics."
        )
    )
    p.add_argument("--reference-scene-json", required=True)
    p.add_argument("--candidate-scene-json", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--output-summary-json", default=None)
    p.add_argument(
        "--thresholds-json",
        default=None,
        help="Optional parity threshold override JSON object.",
    )
    p.add_argument(
        "--allow-failures",
        action="store_true",
        help="Return 0 even when parity check fails.",
    )
    return p.parse_args()


def _load_thresholds(path: Optional[str]) -> Optional[Dict[str, float]]:
    if path is None:
        return None
    p = Path(path).expanduser().resolve()
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("--thresholds-json must contain JSON object")
    out: Dict[str, float] = {}
    for key, value in payload.items():
        out[str(key)] = float(value)
    return out


def _load_radar_map_payload(radar_map_npz: str) -> Dict[str, Any]:
    with np.load(str(radar_map_npz), allow_pickle=False) as payload:
        out: Dict[str, Any] = {
            "fx_dop_win": np.asarray(payload["fx_dop_win"]),
            "fx_ang": np.asarray(payload["fx_ang"]),
        }
        if "metadata_json" in payload:
            try:
                out["metadata_json"] = json.loads(str(payload["metadata_json"].tolist()))
            except Exception:
                out["metadata_json"] = str(payload["metadata_json"])
    return out


def main() -> None:
    args = parse_args()
    out_root = Path(args.output_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    ref_out = out_root / "reference"
    cand_out = out_root / "candidate"
    ref = run_object_scene_to_radar_map_json(
        scene_json_path=str(Path(args.reference_scene_json).expanduser().resolve()),
        output_dir=str(ref_out),
        run_hybrid_estimation=False,
    )
    cand = run_object_scene_to_radar_map_json(
        scene_json_path=str(Path(args.candidate_scene_json).expanduser().resolve()),
        output_dir=str(cand_out),
        run_hybrid_estimation=False,
    )

    thresholds = _load_thresholds(args.thresholds_json)
    ref_payload = _load_radar_map_payload(str(ref["radar_map_npz"]))
    cand_payload = _load_radar_map_payload(str(cand["radar_map_npz"]))
    parity = compare_hybrid_estimation_payloads(
        reference=ref_payload,
        candidate=cand_payload,
        thresholds=thresholds,
    )

    ref_scene = json.loads(Path(args.reference_scene_json).read_text(encoding="utf-8"))
    cand_scene = json.loads(Path(args.candidate_scene_json).read_text(encoding="utf-8"))
    ref_backend = str(ref_scene.get("backend", {}).get("type", ""))
    cand_backend = str(cand_scene.get("backend", {}).get("type", ""))

    out = {
        "version": 1,
        "reference_scene_json": str(Path(args.reference_scene_json).expanduser().resolve()),
        "candidate_scene_json": str(Path(args.candidate_scene_json).expanduser().resolve()),
        "reference_backend_type": ref_backend,
        "candidate_backend_type": cand_backend,
        "reference_radar_map_npz": str(ref["radar_map_npz"]),
        "candidate_radar_map_npz": str(cand["radar_map_npz"]),
        "parity": parity,
    }

    out_summary_json = (
        out_root / "scene_backend_parity_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json).expanduser().resolve()
    )
    out_summary_json.parent.mkdir(parents=True, exist_ok=True)
    out_summary_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Scene backend parity completed.")
    print(f"  reference_backend: {ref_backend}")
    print(f"  candidate_backend: {cand_backend}")
    print(f"  parity_pass: {parity['pass']}")
    print(f"  output_summary_json: {out_summary_json}")

    if (not parity["pass"]) and (not args.allow_failures):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

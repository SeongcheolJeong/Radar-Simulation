#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from avxsim.parity import compare_hybrid_estimation_payloads


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run backend KPI/parity campaign from a golden-path runtime report "
            "and emit radar-developer readiness summary."
        )
    )
    p.add_argument(
        "--golden-path-summary-json",
        required=True,
        help="Input summary from scripts/run_scene_backend_golden_path.py",
    )
    p.add_argument("--output-summary-json", required=True, help="Output KPI campaign summary JSON")
    p.add_argument(
        "--reference-backend",
        default="analytic_targets",
        help="Reference backend for comparisons (default: analytic_targets)",
    )
    p.add_argument(
        "--thresholds-json",
        default=None,
        help="Optional parity threshold override JSON object",
    )
    p.add_argument(
        "--strict-ready",
        action="store_true",
        help="Exit non-zero when campaign_status is not ready",
    )
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _load_thresholds(path: Optional[str]) -> Optional[Dict[str, float]]:
    if path is None:
        return None
    p = Path(path).expanduser().resolve()
    payload = _load_json(p)
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


def _executed_backends(results: Mapping[str, Any], requested_backends: Iterable[str]) -> List[str]:
    out: List[str] = []
    for name in requested_backends:
        status = str(results.get(name, {}).get("status", "")).strip()
        if status == "executed":
            out.append(str(name))
    return out


def _kpi_subset(metrics: Mapping[str, Any]) -> Dict[str, float]:
    keys = (
        "rd_shape_nmse",
        "ra_shape_nmse",
        "rd_peak_range_bin_abs_error",
        "ra_peak_angle_bin_abs_error",
        "rd_centroid_range_bin_abs_error",
        "ra_centroid_angle_bin_abs_error",
    )
    out: Dict[str, float] = {}
    for key in keys:
        if key in metrics:
            out[key] = float(metrics[key])
    return out


def _compare_pair(
    reference_backend: str,
    candidate_backend: str,
    results: Mapping[str, Any],
    thresholds: Optional[Mapping[str, float]],
) -> Dict[str, Any]:
    ref_item = dict(results.get(reference_backend, {}) or {})
    cand_item = dict(results.get(candidate_backend, {}) or {})

    ref_status = str(ref_item.get("status", "")).strip()
    cand_status = str(cand_item.get("status", "")).strip()

    base = {
        "reference_backend": reference_backend,
        "candidate_backend": candidate_backend,
        "reference_status": ref_status,
        "candidate_status": cand_status,
        "compared": False,
        "parity": None,
        "kpi": None,
        "reason": None,
    }

    if ref_status != "executed":
        base["reason"] = f"reference_not_executed:{reference_backend}"
        return base
    if cand_status != "executed":
        base["reason"] = f"candidate_not_executed:{candidate_backend}"
        return base

    ref_map = _load_radar_map_payload(str(ref_item["radar_map_npz"]))
    cand_map = _load_radar_map_payload(str(cand_item["radar_map_npz"]))
    parity = compare_hybrid_estimation_payloads(
        reference=ref_map,
        candidate=cand_map,
        thresholds=thresholds,
    )

    base["compared"] = True
    base["parity"] = parity
    base["kpi"] = _kpi_subset(parity.get("metrics", {}))
    return base


def _campaign_summary(
    requested_backends: Sequence[str],
    executed_backends: Sequence[str],
    comparisons: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    compared_rows = [row for row in comparisons if bool(row.get("compared", False))]
    passed = [row for row in compared_rows if bool((row.get("parity") or {}).get("pass", False))]
    failed = [row for row in compared_rows if not bool((row.get("parity") or {}).get("pass", False))]

    return {
        "requested_backend_count": int(len(requested_backends)),
        "executed_backend_count": int(len(executed_backends)),
        "executed_backends": [str(x) for x in executed_backends],
        "compared_pair_count": int(len(compared_rows)),
        "parity_pass_count": int(len(passed)),
        "parity_fail_count": int(len(failed)),
        "parity_pass_pairs": [
            f"{row['reference_backend']}->{row['candidate_backend']}" for row in passed
        ],
        "parity_fail_pairs": [
            f"{row['reference_backend']}->{row['candidate_backend']}" for row in failed
        ],
    }


def _classify_campaign_status(
    reference_backend: str,
    requested_backends: Sequence[str],
    executed_backends: Sequence[str],
    comparisons: Sequence[Mapping[str, Any]],
) -> Tuple[str, List[str]]:
    blockers: List[str] = []

    if reference_backend not in requested_backends:
        blockers.append("reference_backend_not_requested")
    if reference_backend not in executed_backends:
        blockers.append("reference_backend_not_executed")

    compared_rows = [row for row in comparisons if bool(row.get("compared", False))]
    if len(compared_rows) == 0:
        blockers.append("no_comparable_candidates")

    fail_rows = [row for row in compared_rows if not bool((row.get("parity") or {}).get("pass", False))]
    if len(fail_rows) > 0:
        blockers.append("parity_failure_detected")

    if len(blockers) == 0:
        return "ready", []
    return "blocked", blockers


def main() -> None:
    args = parse_args()

    golden_path = Path(args.golden_path_summary_json).expanduser().resolve()
    if not golden_path.exists():
        raise FileNotFoundError(f"golden-path summary not found: {golden_path}")

    output_json = Path(args.output_summary_json).expanduser().resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)

    thresholds = _load_thresholds(args.thresholds_json)

    payload = _load_json(golden_path)
    requested_backends = [str(x) for x in payload.get("requested_backends", [])]
    results = payload.get("results")
    if not isinstance(results, Mapping):
        raise ValueError("golden-path report missing results object")

    reference_backend = str(args.reference_backend).strip().lower()
    executed_backends = _executed_backends(results=results, requested_backends=requested_backends)

    candidates = [name for name in requested_backends if name != reference_backend]
    comparisons: List[Dict[str, Any]] = []
    for cand in candidates:
        comparisons.append(
            _compare_pair(
                reference_backend=reference_backend,
                candidate_backend=cand,
                results=results,
                thresholds=thresholds,
            )
        )

    campaign_summary = _campaign_summary(
        requested_backends=requested_backends,
        executed_backends=executed_backends,
        comparisons=comparisons,
    )
    campaign_status, blockers = _classify_campaign_status(
        reference_backend=reference_backend,
        requested_backends=requested_backends,
        executed_backends=executed_backends,
        comparisons=comparisons,
    )

    report = {
        "version": 1,
        "source_golden_path_summary_json": str(golden_path),
        "reference_backend": reference_backend,
        "requested_backends": requested_backends,
        "executed_backends": executed_backends,
        "campaign_status": campaign_status,
        "blockers": blockers,
        "threshold_overrides": thresholds,
        "comparisons": comparisons,
        "summary": campaign_summary,
    }
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Scene backend KPI campaign completed.")
    print(f"  campaign_status: {campaign_status}")
    print(f"  blockers: {blockers}")
    print(f"  compared_pair_count: {campaign_summary['compared_pair_count']}")
    print(f"  parity_fail_count: {campaign_summary['parity_fail_count']}")
    print(f"  output_summary_json: {output_json}")

    if bool(args.strict_ready) and (campaign_status != "ready"):
        raise RuntimeError("backend KPI campaign is not ready")


if __name__ == "__main__":
    main()

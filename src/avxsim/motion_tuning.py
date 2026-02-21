import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .parity import compare_hybrid_estimation_npz


DEFAULT_MOTION_SCORE_WEIGHTS: Dict[str, float] = {
    "ra_peak_angle_bin_abs_error": 1.0,
    "ra_centroid_angle_bin_abs_error": 0.5,
    "ra_shape_nmse": 0.25,
    "ra_peak_power_db_abs_error": 0.2,
    "rd_peak_doppler_bin_abs_error": 0.2,
}


def load_motion_tuning_manifest_json(path: str) -> List[Dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        items = payload.get("candidates", None)
    else:
        items = payload
    if not isinstance(items, list) or len(items) == 0:
        raise ValueError("motion tuning manifest must contain non-empty candidates list")

    out: List[Dict[str, Any]] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"manifest candidates[{i}] must be object")
        if "estimation_npz" not in item:
            raise ValueError(f"manifest candidates[{i}] missing estimation_npz")
        motion = item.get("motion_compensation", {})
        if not isinstance(motion, dict):
            raise ValueError(f"manifest candidates[{i}].motion_compensation must be object")
        out.append(
            {
                "name": str(item.get("name", f"candidate_{i+1}")),
                "estimation_npz": str(item["estimation_npz"]),
                "motion_compensation": {
                    "enabled": bool(motion.get("enabled", True)),
                    "fd_hz": None if motion.get("fd_hz", None) is None else float(motion["fd_hz"]),
                    "chirp_interval_s": None
                    if motion.get("chirp_interval_s", None) is None
                    else float(motion["chirp_interval_s"]),
                    "reference_tx": None
                    if motion.get("reference_tx", None) is None
                    else int(motion["reference_tx"]),
                },
            }
        )
    return out


def score_motion_metrics(
    metrics: Mapping[str, float],
    score_weights: Mapping[str, float] = DEFAULT_MOTION_SCORE_WEIGHTS,
) -> float:
    score = 0.0
    for key, w in score_weights.items():
        score += float(w) * float(metrics.get(str(key), 0.0))
    return float(score)


def evaluate_motion_tuning_candidates(
    reference_estimation_npz: str,
    candidates: Sequence[Mapping[str, Any]],
    score_weights: Mapping[str, float] = DEFAULT_MOTION_SCORE_WEIGHTS,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, cand in enumerate(candidates):
        est = str(cand["estimation_npz"])
        rep = compare_hybrid_estimation_npz(
            reference_npz=str(reference_estimation_npz),
            candidate_npz=est,
            thresholds=None,
        )
        metrics = rep["metrics"]
        score = score_motion_metrics(metrics, score_weights=score_weights)
        out.append(
            {
                "index": int(i),
                "name": str(cand.get("name", f"candidate_{i+1}")),
                "estimation_npz": est,
                "motion_compensation": dict(cand.get("motion_compensation", {})),
                "score": float(score),
                "metrics": metrics,
            }
        )
    return out


def select_best_motion_tuning_candidate(
    reference_estimation_npz: str,
    candidates: Sequence[Mapping[str, Any]],
    score_weights: Mapping[str, float] = DEFAULT_MOTION_SCORE_WEIGHTS,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    rows = evaluate_motion_tuning_candidates(
        reference_estimation_npz=reference_estimation_npz,
        candidates=candidates,
        score_weights=score_weights,
    )
    if len(rows) == 0:
        raise ValueError("no candidates to select")
    rows_sorted = sorted(
        rows,
        key=lambda x: (
            float(x["score"]),
            float(x["metrics"].get("ra_peak_angle_bin_abs_error", 0.0)),
            float(x["metrics"].get("rd_peak_doppler_bin_abs_error", 0.0)),
            str(x["name"]),
        ),
    )
    return rows_sorted[0], rows_sorted


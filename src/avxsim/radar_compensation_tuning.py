import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from .parity import compare_hybrid_estimation_npz
from .scene_pipeline import run_object_scene_to_radar_map


DEFAULT_COMPENSATION_SCORE_WEIGHTS: Dict[str, float] = {
    "rd_shape_nmse": 1.0,
    "ra_shape_nmse": 1.0,
    "rd_peak_range_bin_abs_error": 0.6,
    "ra_peak_angle_bin_abs_error": 0.6,
    "rd_centroid_range_bin_abs_error": 0.3,
    "ra_centroid_angle_bin_abs_error": 0.3,
}


def load_compensation_candidates_json(path: str) -> List[Dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    items = payload.get("candidates") if isinstance(payload, Mapping) else payload
    if not isinstance(items, list) or len(items) == 0:
        raise ValueError("compensation candidates json must contain non-empty list")

    out: List[Dict[str, Any]] = []
    for idx, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise ValueError(f"candidates[{idx}] must be object")
        patch = item.get("patch", {})
        if not isinstance(patch, Mapping):
            raise ValueError(f"candidates[{idx}].patch must be object")
        out.append(
            {
                "name": str(item.get("name", f"candidate_{idx+1}")),
                "patch": dict(patch),
            }
        )
    return out


def tune_radar_compensation_candidates(
    scene_payload_template: Mapping[str, Any],
    reference_radar_map_npz: str,
    output_dir: str,
    candidates: Sequence[Mapping[str, Any]],
    score_weights: Mapping[str, float] = DEFAULT_COMPENSATION_SCORE_WEIGHTS,
) -> Dict[str, Any]:
    scene_payload = _deepcopy_mapping(scene_payload_template)
    backend = _as_obj(scene_payload, "backend")
    base_comp = _as_obj(backend, "radar_compensation")
    if not bool(base_comp.get("enabled", False)):
        raise ValueError("template backend.radar_compensation.enabled must be true")
    _ = _as_obj(scene_payload, "radar")

    out_root = Path(output_dir).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    reference_npz = str(Path(reference_radar_map_npz).expanduser().resolve())

    rows: List[Dict[str, Any]] = []
    for idx, cand in enumerate(candidates):
        if not isinstance(cand, Mapping):
            raise ValueError(f"candidates[{idx}] must be object")
        name = str(cand.get("name", f"candidate_{idx+1}")).strip()
        if name == "":
            name = f"candidate_{idx+1}"
        patch = cand.get("patch", {})
        if not isinstance(patch, Mapping):
            raise ValueError(f"candidates[{idx}].patch must be object")

        comp_cfg = _deep_merge_dicts(base=_deepcopy_mapping(base_comp), patch=dict(patch))
        run_scene = _deepcopy_mapping(scene_payload)
        run_scene_backend = _as_obj(run_scene, "backend")
        run_scene_backend["radar_compensation"] = comp_cfg
        run_scene["backend"] = run_scene_backend

        cand_root = out_root / f"{idx:03d}_{_safe_name(name)}"
        cand_root.mkdir(parents=True, exist_ok=True)
        run_out = run_object_scene_to_radar_map(
            scene_payload=run_scene,
            output_dir=str(cand_root),
            run_hybrid_estimation=False,
        )
        candidate_radar_map = str(Path(run_out["radar_map_npz"]).expanduser().resolve())
        radar_meta = _load_radar_map_metadata(candidate_radar_map)
        parity = compare_hybrid_estimation_npz(
            reference_npz=reference_npz,
            candidate_npz=candidate_radar_map,
            thresholds=None,
        )
        score = score_compensation_metrics(
            metrics=parity.get("metrics", {}),
            score_weights=score_weights,
        )

        rows.append(
            {
                "index": int(idx),
                "name": name,
                "score": float(score),
                "pass_unthresholded": bool(parity.get("pass", False)),
                "metrics": dict(parity.get("metrics", {})),
                "radar_map_npz": candidate_radar_map,
                "path_list_json": str(run_out["path_list_json"]),
                "adc_cube_npz": str(run_out["adc_cube_npz"]),
                "compensation_summary": dict(radar_meta.get("compensation_summary", {})),
                "path_contract_summary": dict(radar_meta.get("path_contract_summary", {})),
                "patch": dict(patch),
                "compensation_config": comp_cfg,
            }
        )

    if len(rows) == 0:
        raise ValueError("no tuning candidates")
    rows_sorted = sorted(
        rows,
        key=lambda x: (
            float(x["score"]),
            float(x["metrics"].get("rd_shape_nmse", 0.0)),
            float(x["metrics"].get("ra_shape_nmse", 0.0)),
            str(x["name"]),
        ),
    )
    best = rows_sorted[0]
    return {
        "version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "reference_radar_map_npz": reference_npz,
        "score_weights": {str(k): float(v) for k, v in score_weights.items()},
        "candidate_count": int(len(rows_sorted)),
        "selected_candidate_name": str(best["name"]),
        "selected_candidate_index": int(best["index"]),
        "selected_score": float(best["score"]),
        "selected_metrics": dict(best["metrics"]),
        "selected_compensation_config": dict(best["compensation_config"]),
        "ranked_candidates": rows_sorted,
    }


def score_compensation_metrics(
    metrics: Mapping[str, Any],
    score_weights: Mapping[str, float] = DEFAULT_COMPENSATION_SCORE_WEIGHTS,
) -> float:
    score = 0.0
    for key, weight in score_weights.items():
        score += float(weight) * float(metrics.get(str(key), 0.0))
    return float(score)


def save_compensation_tuning_report_json(path: str, payload: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(_to_jsonable(payload), indent=2), encoding="utf-8")


def build_profile_compensation_lock_payload(
    profile_id: str,
    tuning_report: Mapping[str, Any],
    source_tuning_report_json: Optional[str] = None,
) -> Dict[str, Any]:
    report = dict(tuning_report)
    selected_cfg = report.get("selected_compensation_config")
    if not isinstance(selected_cfg, Mapping):
        raise ValueError("tuning report missing selected_compensation_config")
    return {
        "version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_tuning_report_json": None
        if source_tuning_report_json is None
        else str(source_tuning_report_json),
        "profiles": {
            str(profile_id): {
                "radar_compensation": dict(selected_cfg),
                "selected_candidate_name": str(report.get("selected_candidate_name", "")),
                "selected_score": float(report.get("selected_score", 0.0)),
            }
        },
    }


def load_profile_compensation_lock_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("profile compensation lock must be object")
    profiles = payload.get("profiles")
    if not isinstance(profiles, Mapping) or len(profiles) == 0:
        raise ValueError("profile compensation lock missing non-empty profiles map")
    out: Dict[str, Any] = {}
    for profile_id, row in profiles.items():
        if not isinstance(row, Mapping):
            raise ValueError(f"profiles.{profile_id} must be object")
        cfg = row.get("radar_compensation", row)
        if not isinstance(cfg, Mapping):
            raise ValueError(f"profiles.{profile_id}.radar_compensation must be object")
        out[str(profile_id)] = dict(cfg)
    return out


def _as_obj(payload: Mapping[str, Any], key: str) -> Dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be object")
    return dict(value)


def _deepcopy_mapping(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return json.loads(json.dumps(payload))


def _deep_merge_dicts(base: MutableMapping[str, Any], patch: Mapping[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(base)
    for key, value in patch.items():
        k = str(key)
        if isinstance(value, Mapping) and isinstance(out.get(k), Mapping):
            out[k] = _deep_merge_dicts(dict(out[k]), dict(value))
        else:
            out[k] = value
    return out


def _safe_name(text: str) -> str:
    chars = []
    for ch in str(text):
        if ch.isalnum() or ch in {"-", "_"}:
            chars.append(ch)
        else:
            chars.append("_")
    out = "".join(chars).strip("_")
    return out if out != "" else "candidate"


def _load_radar_map_metadata(radar_map_npz: str) -> Dict[str, Any]:
    import numpy as np

    with np.load(str(radar_map_npz), allow_pickle=False) as payload:
        raw = payload.get("metadata_json")
        if raw is None:
            return {}
        value = raw.tolist() if hasattr(raw, "tolist") else raw
        parsed = json.loads(str(value))
        if not isinstance(parsed, Mapping):
            return {}
        return dict(parsed)


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value

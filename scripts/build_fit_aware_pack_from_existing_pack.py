#!/usr/bin/env python3
import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from avxsim.adc_pack_builder import build_measured_pack_from_adc_npz


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Rebuild a measured pack from an existing pack's source ADC list while applying "
            "path-power fit proxy weighting to candidate estimation maps."
        )
    )
    p.add_argument("--source-pack-root", required=True)
    p.add_argument("--output-pack-root", required=True)
    p.add_argument("--path-power-fit-json", required=True)
    p.add_argument("--scenario-id", default=None)
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--max-candidates", type=int, default=None)
    p.add_argument(
        "--adc-order",
        default="auto",
        help="adc order permutation (s,c,t,r) or auto",
    )
    p.add_argument(
        "--adc-key",
        default="auto",
        help="adc key in source NPZ or auto",
    )
    p.add_argument("--reference-index", type=int, default=None)
    p.add_argument("--output-summary-json", default=None)
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json must be object: {path}")
    return payload


def _resolve_profile_json(source_pack_root: Path, case: Mapping[str, Any]) -> Path:
    pj = case.get("profile_json", None)
    if isinstance(pj, str) and pj.strip() != "":
        p = Path(pj)
        if not p.is_absolute():
            p = source_pack_root / p
        if p.exists() and p.is_file():
            return p
    for c in [
        source_pack_root / "scenario_profile.locked.json",
        source_pack_root / "scenario_profile.json",
    ]:
        if c.exists() and c.is_file():
            return c
    raise FileNotFoundError("could not resolve source profile json")


def _candidate_npz_metadata(est_npz: Path) -> Dict[str, Any]:
    if not est_npz.exists():
        return {}
    with np.load(str(est_npz), allow_pickle=False) as payload:
        if "metadata_json" not in payload:
            return {}
        try:
            raw = payload["metadata_json"].tolist()
            data = json.loads(str(raw))
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    return {}


def _candidate_source_adc(source_pack_root: Path, cand: Mapping[str, Any]) -> str:
    meta = cand.get("metadata", {})
    if isinstance(meta, Mapping):
        src = meta.get("source_adc_npz", None)
        if isinstance(src, str) and src.strip() != "":
            return str(src)
    est = cand.get("estimation_npz", None)
    if isinstance(est, str) and est.strip() != "":
        ep = Path(est)
        if not ep.is_absolute():
            ep = source_pack_root / ep
        m = _candidate_npz_metadata(ep)
        src = m.get("source_adc_npz", None)
        if isinstance(src, str) and src.strip() != "":
            return str(src)
    raise ValueError("candidate is missing source_adc_npz metadata")


def _candidate_estimation_meta(source_pack_root: Path, cand: Mapping[str, Any]) -> Dict[str, Any]:
    meta = cand.get("metadata", {})
    if isinstance(meta, Mapping):
        est = meta.get("estimation", None)
        if isinstance(est, Mapping):
            return dict(est)
    est_npz = cand.get("estimation_npz", None)
    if isinstance(est_npz, str) and est_npz.strip() != "":
        ep = Path(est_npz)
        if not ep.is_absolute():
            ep = source_pack_root / ep
        m = _candidate_npz_metadata(ep)
        est = m.get("estimation", None)
        if isinstance(est, Mapping):
            return dict(est)
    return {}


def _candidate_adc_info(source_pack_root: Path, cand: Mapping[str, Any]) -> Dict[str, Any]:
    meta = cand.get("metadata", {})
    if isinstance(meta, Mapping):
        adc_info = meta.get("adc_info", None)
        if isinstance(adc_info, Mapping):
            return dict(adc_info)
    est_npz = cand.get("estimation_npz", None)
    if isinstance(est_npz, str) and est_npz.strip() != "":
        ep = Path(est_npz)
        if not ep.is_absolute():
            ep = source_pack_root / ep
        m = _candidate_npz_metadata(ep)
        out = {}
        for key in ["adc_key", "adc_shape"]:
            if key in m:
                out[key] = m[key]
        if out:
            return out
    return {}


def _infer_adc_order(raw_shape: Sequence[int], sctr_shape: Sequence[int]) -> Optional[str]:
    if len(raw_shape) != 4 or len(sctr_shape) != 4:
        return None
    used = set()
    perm: List[int] = []
    for target in sctr_shape:
        found = None
        for idx, val in enumerate(raw_shape):
            if idx in used:
                continue
            if int(val) == int(target):
                found = idx
                break
        if found is None:
            return None
        perm.append(found)
        used.add(found)

    # perm maps output [s,c,t,r] axis -> raw axis.
    labels = ["s", "c", "t", "r"]
    order_chars = ["?"] * 4
    for out_axis, raw_axis in enumerate(perm):
        order_chars[raw_axis] = labels[out_axis]
    if any(ch == "?" for ch in order_chars):
        return None
    order = "".join(order_chars)
    if set(order) != {"s", "c", "t", "r"}:
        return None
    return order


def _pick_reference_index(
    selected_candidates: Sequence[Mapping[str, Any]],
    selected_original_indices: Sequence[int],
    source_profile: Mapping[str, Any],
    source_pack_root: Path,
) -> int:
    ref = source_profile.get("reference_estimation_npz", None)
    if not isinstance(ref, str) or ref.strip() == "":
        return 0

    ref_path = Path(ref)
    if not ref_path.is_absolute():
        ref_path = source_pack_root / ref_path
    ref_abs = str(ref_path.resolve())

    for new_i, cand in enumerate(selected_candidates):
        est = cand.get("estimation_npz", None)
        if not isinstance(est, str):
            continue
        ep = Path(est)
        if not ep.is_absolute():
            ep = source_pack_root / ep
        try:
            est_abs = str(ep.resolve())
        except Exception:
            est_abs = str(ep)
        if est_abs == ref_abs:
            return int(new_i)

    # If source reference candidate was filtered out, prefer first surviving candidate.
    _ = selected_original_indices
    return 0


def main() -> None:
    args = parse_args()
    if int(args.stride) <= 0:
        raise ValueError("--stride must be positive")

    src_root = Path(args.source_pack_root).expanduser().resolve()
    out_root = Path(args.output_pack_root).expanduser().resolve()
    manifest_json = src_root / "replay_manifest.json"
    if not manifest_json.exists() or not manifest_json.is_file():
        raise FileNotFoundError(f"missing source replay_manifest.json: {manifest_json}")

    manifest = _load_json(manifest_json)
    cases = manifest.get("cases", [])
    if not isinstance(cases, list) or len(cases) == 0:
        raise ValueError("source manifest must contain non-empty cases")
    case = cases[0]
    if not isinstance(case, Mapping):
        raise ValueError("source cases[0] must be object")

    cands = case.get("candidates", None)
    if not isinstance(cands, list) or len(cands) == 0:
        raise ValueError("source case must contain non-empty candidates")

    selected_pairs = list(enumerate(cands))[:: int(args.stride)]
    if args.max_candidates is not None:
        selected_pairs = selected_pairs[: int(args.max_candidates)]
    if len(selected_pairs) == 0:
        raise ValueError("candidate selection is empty")

    selected_original_indices = [int(i) for i, _ in selected_pairs]
    selected_candidates = [c for _, c in selected_pairs]

    adc_files: List[str] = []
    for c in selected_candidates:
        adc_files.append(_candidate_source_adc(src_root, c))

    est_meta0 = _candidate_estimation_meta(src_root, selected_candidates[0])
    adc_info0 = _candidate_adc_info(src_root, selected_candidates[0])

    if args.adc_order == "auto":
        adc_order = None
        raw_shape = adc_info0.get("shape", None)
        sctr_shape = est_meta0.get("input_shape_sctr", None)
        if isinstance(raw_shape, Sequence) and isinstance(sctr_shape, Sequence):
            adc_order = _infer_adc_order(raw_shape=raw_shape, sctr_shape=sctr_shape)
        if adc_order is None:
            adc_order = "sctr"
    else:
        adc_order = str(args.adc_order)

    if args.adc_key == "auto":
        adc_key = str(adc_info0.get("adc_key", "adc"))
    else:
        adc_key = str(args.adc_key)

    source_profile_json = _resolve_profile_json(src_root, case)
    source_profile = _load_json(source_profile_json)

    if args.reference_index is None:
        reference_index = _pick_reference_index(
            selected_candidates=selected_candidates,
            selected_original_indices=selected_original_indices,
            source_profile=source_profile,
            source_pack_root=src_root,
        )
    else:
        reference_index = int(args.reference_index)

    scenario_id = (
        str(args.scenario_id)
        if args.scenario_id is not None
        else str(case.get("scenario_id", src_root.name))
    )

    summary = build_measured_pack_from_adc_npz(
        adc_npz_files=adc_files,
        output_pack_root=str(out_root),
        scenario_id=scenario_id,
        adc_order=adc_order,
        adc_key=adc_key,
        reference_index=int(reference_index),
        nfft_range=None if est_meta0.get("nfft_range", None) is None else int(est_meta0["nfft_range"]),
        nfft_doppler=None if est_meta0.get("nfft_doppler", None) is None else int(est_meta0["nfft_doppler"]),
        nfft_angle=None if est_meta0.get("nfft_angle", None) is None else int(est_meta0["nfft_angle"]),
        range_window=str(est_meta0.get("range_window", "hann")),
        doppler_window=str(est_meta0.get("doppler_window", "hann")),
        angle_window=str(est_meta0.get("angle_window", "hann")),
        range_bin_limit=None
        if est_meta0.get("range_bin_limit", None) is None
        else int(est_meta0["range_bin_limit"]),
        path_power_fit_json=str(args.path_power_fit_json),
    )

    # Preserve source profile thresholds/calibration defaults while updating reference path.
    new_profile_json = Path(summary["profile_json"])
    preserved_profile = dict(source_profile)
    preserved_profile["scenario_id"] = str(scenario_id)
    preserved_profile["reference_estimation_npz"] = str(summary["reference_estimation_npz"])
    preserved_profile["fit_aware_rebuild"] = {
        "source_pack_root": str(src_root),
        "source_profile_json": str(source_profile_json),
        "path_power_fit_json": str(args.path_power_fit_json),
        "selected_candidate_count": int(len(adc_files)),
        "selected_original_indices": selected_original_indices,
        "adc_order": str(adc_order),
        "adc_key": str(adc_key),
    }
    new_profile_json.write_text(json.dumps(preserved_profile, indent=2), encoding="utf-8")

    src_lock_policy = src_root / "lock_policy.json"
    if src_lock_policy.exists() and src_lock_policy.is_file():
        shutil.copy2(str(src_lock_policy), str(out_root / "lock_policy.json"))

    out_summary = {
        "version": 1,
        "source_pack_root": str(src_root),
        "source_manifest_json": str(manifest_json),
        "source_profile_json": str(source_profile_json),
        "output_pack_root": str(out_root),
        "path_power_fit_json": str(args.path_power_fit_json),
        "scenario_id": str(scenario_id),
        "selected_candidate_count": int(len(adc_files)),
        "selected_original_indices": selected_original_indices,
        "adc_order": str(adc_order),
        "adc_key": str(adc_key),
        "reference_index": int(reference_index),
        "build_summary": summary,
    }

    out_summary_json = (
        out_root / "fit_aware_pack_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )
    out_summary_json.parent.mkdir(parents=True, exist_ok=True)
    out_summary_json.write_text(json.dumps(out_summary, indent=2), encoding="utf-8")

    print("Fit-aware pack rebuild completed.")
    print(f"  source_pack_root: {src_root}")
    print(f"  output_pack_root: {out_root}")
    print(f"  selected_candidate_count: {len(adc_files)}")
    print(f"  adc_order: {adc_order}")
    print(f"  adc_key: {adc_key}")
    print(f"  reference_index: {reference_index}")
    print(f"  path_power_fit_json: {args.path_power_fit_json}")
    print(f"  output_summary_json: {out_summary_json}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, Optional

from avxsim.radar_compensation_tuning import (
    DEFAULT_COMPENSATION_SCORE_WEIGHTS,
    build_profile_compensation_lock_payload,
    load_compensation_candidates_json,
    save_compensation_tuning_report_json,
    tune_radar_compensation_candidates,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Tune backend.radar_compensation candidates against a measured/reference "
            "radar_map.npz and freeze selected profile defaults as lock JSON."
        )
    )
    p.add_argument("--profile-id", required=True)
    p.add_argument("--scene-json-template", required=True)
    p.add_argument("--reference-radar-map-npz", required=True)
    p.add_argument("--candidates-json", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--output-tuning-report-json", required=True)
    p.add_argument("--output-lock-json", required=True)
    p.add_argument(
        "--score-weight",
        action="append",
        default=[],
        help="Override metric weight as key=value",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    scene_json = Path(args.scene_json_template).expanduser().resolve()
    reference_npz = Path(args.reference_radar_map_npz).expanduser().resolve()
    candidates_json = Path(args.candidates_json).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    tuning_report_json = Path(args.output_tuning_report_json).expanduser().resolve()
    lock_json = Path(args.output_lock_json).expanduser().resolve()

    if not scene_json.exists():
        raise FileNotFoundError(f"scene template not found: {scene_json}")
    if not reference_npz.exists():
        raise FileNotFoundError(f"reference radar map not found: {reference_npz}")
    if not candidates_json.exists():
        raise FileNotFoundError(f"candidates json not found: {candidates_json}")

    scene_payload = json.loads(scene_json.read_text(encoding="utf-8"))
    if not isinstance(scene_payload, dict):
        raise ValueError("scene template must be json object")

    score_weights = _resolve_score_weights(args.score_weight)
    candidates = load_compensation_candidates_json(str(candidates_json))
    report = tune_radar_compensation_candidates(
        scene_payload_template=scene_payload,
        reference_radar_map_npz=str(reference_npz),
        output_dir=str(output_root),
        candidates=candidates,
        score_weights=score_weights,
    )
    report["profile_id"] = str(args.profile_id)
    report["scene_json_template"] = str(scene_json)
    report["candidates_json"] = str(candidates_json)
    report["output_root"] = str(output_root)

    tuning_report_json.parent.mkdir(parents=True, exist_ok=True)
    save_compensation_tuning_report_json(str(tuning_report_json), report)

    lock_payload = build_profile_compensation_lock_payload(
        profile_id=str(args.profile_id),
        tuning_report=report,
        source_tuning_report_json=str(tuning_report_json),
    )
    lock_json.parent.mkdir(parents=True, exist_ok=True)
    lock_json.write_text(json.dumps(lock_payload, indent=2), encoding="utf-8")

    print("Radar compensation preset tuning completed.")
    print(f"  profile_id: {args.profile_id}")
    print(f"  candidate_count: {report['candidate_count']}")
    print(f"  selected_candidate_name: {report['selected_candidate_name']}")
    print(f"  selected_score: {report['selected_score']:.8f}")
    print(f"  output_tuning_report_json: {tuning_report_json}")
    print(f"  output_lock_json: {lock_json}")


def _resolve_score_weights(items) -> Dict[str, float]:
    out = dict(DEFAULT_COMPENSATION_SCORE_WEIGHTS)
    for raw in items:
        text = str(raw)
        if "=" not in text:
            raise ValueError(f"invalid --score-weight: {raw}")
        key, value = text.split("=", 1)
        k = str(key).strip()
        if k == "":
            raise ValueError(f"invalid --score-weight key: {raw}")
        out[k] = float(value)
    return out


if __name__ == "__main__":
    main()

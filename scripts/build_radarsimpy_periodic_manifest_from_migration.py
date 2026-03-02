#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

import numpy as np

from avxsim.adc_pack_builder import load_adc_from_npz, reorder_adc_to_sctr
from avxsim.adapters import to_radarsimpy_view


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Build RadarSimPy periodic-lock manifest from migration-stepwise summary "
            "(reference ADC -> reference view, candidate ADC -> case list)."
        )
    )
    p.add_argument("--migration-summary-json", required=True)
    p.add_argument("--output-manifest-json", required=True)
    p.add_argument("--output-reference-view-npz", required=True)
    p.add_argument(
        "--include-backend",
        action="append",
        default=[],
        help="Restrict included backends (repeatable or comma-separated). Default: all",
    )
    p.add_argument(
        "--require-compared",
        action="store_true",
        help="Include only steps with status=compared",
    )
    p.add_argument(
        "--require-parity-pass",
        action="store_true",
        help="Include only steps with parity_pass=true",
    )
    p.add_argument("--reference-adc-key", default="adc")
    p.add_argument("--reference-adc-order", default="sctr")
    p.add_argument("--candidate-adc-key", default="adc")
    p.add_argument("--candidate-adc-order", default="sctr")
    p.add_argument("--reference-view-key", default="view")
    p.add_argument("--case-id-prefix", default="migration")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Fail when no candidate cases are selected",
    )
    return p.parse_args()


def _parse_backend_filters(items: Sequence[str]) -> Set[str]:
    out: Set[str] = set()
    for raw in items:
        for token in str(raw).split(","):
            name = str(token).strip()
            if name != "":
                out.add(name)
    return out


def _resolve_path(raw: Any, *, base_dir: Path) -> Path:
    p = Path(str(raw)).expanduser()
    if not p.is_absolute():
        p = (base_dir / p).resolve()
    else:
        p = p.resolve()
    return p


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _build_reference_view_npz(
    summary_payload: Mapping[str, Any],
    output_reference_view_npz: Path,
    *,
    reference_adc_key: str,
    reference_adc_order: str,
    reference_view_key: str,
    summary_dir: Path,
) -> Dict[str, Any]:
    reference = summary_payload.get("reference")
    if not isinstance(reference, Mapping):
        raise ValueError("migration summary missing object: reference")
    ref_adc_raw = reference.get("adc_cube_npz")
    if ref_adc_raw is None:
        raise ValueError("migration summary reference missing adc_cube_npz")
    ref_adc_npz = _resolve_path(ref_adc_raw, base_dir=summary_dir)
    if not ref_adc_npz.exists():
        raise FileNotFoundError(f"reference adc npz not found: {ref_adc_npz}")

    adc_raw, _ = load_adc_from_npz(str(ref_adc_npz), adc_key=str(reference_adc_key))
    adc_sctr = reorder_adc_to_sctr(adc_raw, adc_order=str(reference_adc_order))
    ref_view = np.asarray(to_radarsimpy_view(adc_sctr), dtype=np.complex64)

    output_reference_view_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(str(output_reference_view_npz), **{str(reference_view_key): ref_view})
    return {
        "reference_adc_npz": str(ref_adc_npz),
        "reference_adc_shape_sctr": [int(x) for x in np.asarray(adc_sctr).shape],
        "reference_view_shape": [int(x) for x in ref_view.shape],
        "reference_view_key": str(reference_view_key),
    }


def main() -> None:
    args = parse_args()

    summary_json = Path(args.migration_summary_json).expanduser().resolve()
    output_manifest_json = Path(args.output_manifest_json).expanduser().resolve()
    output_reference_view_npz = Path(args.output_reference_view_npz).expanduser().resolve()

    summary_payload = json.loads(summary_json.read_text(encoding="utf-8"))
    if not isinstance(summary_payload, Mapping):
        raise ValueError("migration summary json must be object")

    summary_dir = summary_json.parent
    backend_filters = _parse_backend_filters(args.include_backend)
    require_compared = bool(args.require_compared)
    require_parity_pass = bool(args.require_parity_pass)

    ref_info = _build_reference_view_npz(
        summary_payload=summary_payload,
        output_reference_view_npz=output_reference_view_npz,
        reference_adc_key=str(args.reference_adc_key),
        reference_adc_order=str(args.reference_adc_order),
        reference_view_key=str(args.reference_view_key),
        summary_dir=summary_dir,
    )

    steps = summary_payload.get("steps")
    if not isinstance(steps, Sequence) or isinstance(steps, (str, bytes)):
        raise ValueError("migration summary missing list: steps")

    cases: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    used_case_ids: Set[str] = set()

    for idx, row in enumerate(steps):
        if not isinstance(row, Mapping):
            skipped.append({"step_index": int(idx), "reason": "step_not_object"})
            continue

        backend = str(row.get("backend", "")).strip()
        status = str(row.get("status", "")).strip()
        parity_pass = _to_bool(row.get("parity_pass"))
        adc_cube_raw = row.get("adc_cube_npz")

        if backend_filters and (backend not in backend_filters):
            skipped.append({"step_index": int(idx), "backend": backend, "reason": "backend_filtered"})
            continue
        if require_compared and (status != "compared"):
            skipped.append({"step_index": int(idx), "backend": backend, "reason": "status_not_compared"})
            continue
        if require_parity_pass and (not parity_pass):
            skipped.append({"step_index": int(idx), "backend": backend, "reason": "parity_not_pass"})
            continue
        if adc_cube_raw is None:
            skipped.append({"step_index": int(idx), "backend": backend, "reason": "missing_adc_cube_npz"})
            continue

        candidate_adc_npz = _resolve_path(adc_cube_raw, base_dir=summary_dir)
        if not candidate_adc_npz.exists():
            skipped.append(
                {
                    "step_index": int(idx),
                    "backend": backend,
                    "reason": "candidate_adc_missing",
                    "candidate_adc_npz": str(candidate_adc_npz),
                }
            )
            continue

        base_case_id = f"{args.case_id_prefix}_{backend if backend != '' else f'step{idx:02d}'}"
        case_id = base_case_id
        suffix = 1
        while case_id in used_case_ids:
            suffix += 1
            case_id = f"{base_case_id}_{suffix}"
        used_case_ids.add(case_id)

        cases.append(
            {
                "case_id": case_id,
                "backend": backend,
                "candidate_adc_npz": str(candidate_adc_npz),
                "candidate_adc_key": str(args.candidate_adc_key),
                "candidate_adc_order": str(args.candidate_adc_order),
                "reference_view_npz": str(output_reference_view_npz),
                "reference_view_key": str(args.reference_view_key),
            }
        )

    if bool(args.strict) and len(cases) == 0:
        raise RuntimeError("no periodic-lock cases selected from migration summary")

    manifest_payload = {
        "version": 1,
        "source": {
            "migration_summary_json": str(summary_json),
            "reference_backend": summary_payload.get("reference_backend"),
            "migration_status": summary_payload.get("migration_status"),
        },
        "selection": {
            "backend_filters": sorted(list(backend_filters)),
            "require_compared": require_compared,
            "require_parity_pass": require_parity_pass,
        },
        "reference": ref_info,
        "case_count": int(len(cases)),
        "skipped_count": int(len(skipped)),
        "cases": cases,
        "skipped_steps": skipped,
    }

    output_manifest_json.parent.mkdir(parents=True, exist_ok=True)
    output_manifest_json.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")

    print("RadarSimPy periodic manifest build completed.")
    print(f"  migration_summary_json: {summary_json}")
    print(f"  output_manifest_json: {output_manifest_json}")
    print(f"  output_reference_view_npz: {output_reference_view_npz}")
    print(f"  case_count: {len(cases)}")
    print(f"  skipped_count: {len(skipped)}")


if __name__ == "__main__":
    main()

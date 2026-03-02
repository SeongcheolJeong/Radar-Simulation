#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from avxsim import load_radarsimpy_module
from avxsim.radarsimpy_periodic_lock import (
    evaluate_radarsimpy_periodic_manifest,
    load_radarsimpy_periodic_manifest_json,
    save_radarsimpy_periodic_summary_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run periodic RadarSimPy-view parity lock checks using locked reference view "
            "artifacts and candidate ADC NPZ files."
        )
    )
    p.add_argument("--manifest-json", required=True)
    p.add_argument("--output-summary-json", required=True)
    p.add_argument("--thresholds-json", default=None)
    p.add_argument(
        "--normalization-mode",
        default="none",
        choices=("none", "complex_l2"),
        help="Optional normalization mode before parity metrics",
    )
    p.add_argument(
        "--allow-failures",
        action="store_true",
        help="Return 0 even when periodic parity gate fails.",
    )
    return p.parse_args()


def _load_thresholds(path: Optional[str]) -> Optional[Dict[str, float]]:
    if path is None:
        return None
    p = Path(path).expanduser().resolve()
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("--thresholds-json must be object")
    out: Dict[str, float] = {}
    for key, value in payload.items():
        out[str(key)] = float(value)
    return out


def _detect_radarsimpy_runtime() -> Dict[str, Any]:
    try:
        radarsimpy = load_radarsimpy_module()

        return {
            "available": True,
            "version": str(getattr(radarsimpy, "__version__", "unknown")),
        }
    except Exception as exc:
        return {
            "available": False,
            "reason": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    args = parse_args()
    manifest_json = Path(args.manifest_json).expanduser().resolve()
    out_json = Path(args.output_summary_json).expanduser().resolve()
    thresholds = _load_thresholds(args.thresholds_json)

    manifest = load_radarsimpy_periodic_manifest_json(str(manifest_json))
    summary = evaluate_radarsimpy_periodic_manifest(
        manifest_payload=manifest,
        thresholds=thresholds,
        normalization_mode=str(args.normalization_mode),
    )
    summary["manifest_json"] = str(manifest_json)
    summary["runtime_info"] = {
        "radarsimpy": _detect_radarsimpy_runtime(),
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    save_radarsimpy_periodic_summary_json(str(out_json), summary)

    print("RadarSimPy periodic parity lock completed.")
    print(f"  case_count: {summary['case_count']}")
    print(f"  pass_count: {summary['pass_count']}")
    print(f"  fail_count: {summary['fail_count']}")
    print(f"  pass: {summary['pass']}")
    print(f"  output_summary_json: {out_json}")
    runtime = summary["runtime_info"]["radarsimpy"]
    print(f"  radarsimpy_available: {runtime.get('available')}")

    if (not bool(summary["pass"])) and (not args.allow_failures):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

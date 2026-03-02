#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate PO-SBR AVX developer gate report")
    p.add_argument("--summary-json", required=True, help="Gate summary JSON path")
    p.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail unless developer_gate_status=ready",
    )
    p.add_argument(
        "--require-function-better-all",
        action="store_true",
        help="Fail unless function_better_count == total_profiles",
    )
    p.add_argument(
        "--min-physics-better-count",
        type=int,
        default=None,
        help="Optional minimum required physics_better_count",
    )
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("summary json must be object")
    return payload


def _require_mapping(value: Any, key_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{key_name} must be object")
    return value


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"summary json not found: {summary_path}")

    payload = _load_json(summary_path)
    version = int(payload.get("version", 0))
    if version != 1:
        raise ValueError(f"version must be 1, got: {version}")

    status = str(payload.get("developer_gate_status", "")).strip()
    if status not in ("ready", "blocked"):
        raise ValueError(f"developer_gate_status invalid: {status}")

    blockers = payload.get("blockers")
    if not isinstance(blockers, list):
        raise ValueError("blockers must be list")
    if status == "ready" and len(blockers) != 0:
        raise ValueError("ready report must have empty blockers")
    if status == "blocked" and len(blockers) == 0:
        raise ValueError("blocked report must have non-empty blockers")

    matrix_run = _require_mapping(payload.get("matrix_run"), "matrix_run")
    matrix_counts = _require_mapping(payload.get("matrix_counts"), "matrix_counts")
    _require_mapping(payload.get("gate_checks"), "gate_checks")

    matrix_run_ok = bool(matrix_run.get("ok", False))
    if status == "ready" and not matrix_run_ok:
        raise ValueError("ready report requires matrix_run.ok=true")

    total = int(matrix_counts.get("total_profiles", 0))
    ready = int(matrix_counts.get("ready_count", 0))
    physics_better = int(matrix_counts.get("physics_better_count", 0))
    physics_worse = int(matrix_counts.get("physics_worse_count", 0))
    function_better = int(matrix_counts.get("function_better_count", 0))
    if total < 0 or ready < 0:
        raise ValueError("matrix counts must be non-negative")
    if ready > total:
        raise ValueError("ready_count cannot exceed total_profiles")
    if physics_worse < 0:
        raise ValueError("physics_worse_count must be non-negative")

    if args.require_ready and status != "ready":
        raise ValueError(f"developer_gate_status must be ready, got: {status}")
    if args.require_function_better_all and function_better != total:
        raise ValueError(
            "function_better_count must equal total_profiles, "
            f"got {function_better}/{total}"
        )
    if args.min_physics_better_count is not None and physics_better < int(args.min_physics_better_count):
        raise ValueError(
            "physics_better_count below minimum: "
            f"{physics_better} < {int(args.min_physics_better_count)}"
        )

    print("validate_po_sbr_avx_developer_gate_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  developer_gate_status: {status}")
    print(f"  matrix_total_profiles: {total}")
    print(f"  matrix_ready_count: {ready}")
    print(f"  physics_better/equivalent/worse: {physics_better}/{int(matrix_counts.get('physics_equivalent_count', 0))}/{physics_worse}")
    print(f"  function_better/equivalent/worse: {function_better}/{int(matrix_counts.get('function_equivalent_count', 0))}/{int(matrix_counts.get('function_worse_count', 0))}")


if __name__ == "__main__":
    main()

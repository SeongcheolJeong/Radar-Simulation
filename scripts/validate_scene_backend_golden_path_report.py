#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence


ALLOWED_BACKENDS = ("analytic_targets", "sionna_rt", "po_sbr_rt")
ALLOWED_STATUS = ("executed", "blocked", "failed")
EXECUTED_PATH_KEYS = (
    "scene_json",
    "output_dir",
    "path_list_json",
    "adc_cube_npz",
    "radar_map_npz",
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate scene backend golden-path report schema and consistency")
    p.add_argument("--summary-json", required=True, help="Path to golden-path summary JSON")
    p.add_argument(
        "--require-backend-executed",
        action="append",
        default=[],
        help="Backend that must have status=executed (repeatable, comma-separated allowed)",
    )
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("summary json must be object")
    return payload


def _parse_required_backends(items: Sequence[str]) -> List[str]:
    out: List[str] = []
    allowed = set(ALLOWED_BACKENDS)
    for raw in items:
        for token in str(raw).split(","):
            name = str(token).strip().lower()
            if name == "":
                continue
            if name not in allowed:
                raise ValueError(f"unsupported --require-backend-executed value: {name}")
            if name not in out:
                out.append(name)
    return out


def _assert_abs_existing_path(value: Any, key_name: str) -> None:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{key_name} must be non-empty string path")
    p = Path(value).expanduser()
    if not p.is_absolute():
        raise ValueError(f"{key_name} must be absolute path")
    if not p.exists():
        raise ValueError(f"{key_name} path not found: {value}")


def _assert_str_list(value: Any, key_name: str) -> List[str]:
    if not isinstance(value, list):
        raise ValueError(f"{key_name} must be list")
    out: List[str] = []
    for idx, item in enumerate(value):
        text = str(item).strip()
        if text == "":
            raise ValueError(f"{key_name}[{idx}] must be non-empty string")
        out.append(text)
    return out


def _assert_results_schema(results: Mapping[str, Any], requested_backends: Iterable[str]) -> None:
    for backend_name in requested_backends:
        if backend_name not in results:
            raise ValueError(f"results missing backend key: {backend_name}")
        item = results[backend_name]
        if not isinstance(item, Mapping):
            raise ValueError(f"results.{backend_name} must be object")

        status = str(item.get("status", "")).strip()
        if status not in ALLOWED_STATUS:
            raise ValueError(f"results.{backend_name}.status invalid: {status}")

        blockers = item.get("blockers")
        if not isinstance(blockers, list):
            raise ValueError(f"results.{backend_name}.blockers must be list")

        diagnostics = item.get("diagnostics")
        if not isinstance(diagnostics, Mapping):
            raise ValueError(f"results.{backend_name}.diagnostics must be object")

        frame_count = int(item.get("frame_count", 0))
        path_count = int(item.get("path_count", 0))
        if frame_count < 0:
            raise ValueError(f"results.{backend_name}.frame_count must be >= 0")
        if path_count < 0:
            raise ValueError(f"results.{backend_name}.path_count must be >= 0")

        runtime_resolution = item.get("runtime_resolution")
        if runtime_resolution is not None and not isinstance(runtime_resolution, Mapping):
            raise ValueError(f"results.{backend_name}.runtime_resolution must be object or null")

        if status == "executed":
            if len(blockers) != 0:
                raise ValueError(f"results.{backend_name}.blockers must be empty when executed")
            if frame_count <= 0:
                raise ValueError(f"results.{backend_name}.frame_count must be > 0 when executed")
            if path_count <= 0:
                raise ValueError(f"results.{backend_name}.path_count must be > 0 when executed")
            for key in EXECUTED_PATH_KEYS:
                _assert_abs_existing_path(item.get(key), f"results.{backend_name}.{key}")

        if status == "blocked":
            if len(blockers) == 0:
                raise ValueError(f"results.{backend_name}.blockers must be non-empty when blocked")

        if status == "failed":
            err = str(item.get("error", "")).strip()
            if err == "":
                raise ValueError(f"results.{backend_name}.error must be non-empty when failed")


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"summary report not found: {summary_path}")

    payload = _load_json(summary_path)

    version = int(payload.get("version", 0))
    if version != 1:
        raise ValueError(f"version must be 1, got: {version}")

    requested_backends = _assert_str_list(payload.get("requested_backends"), "requested_backends")
    for backend_name in requested_backends:
        if backend_name not in ALLOWED_BACKENDS:
            raise ValueError(f"requested_backends contains unsupported backend: {backend_name}")

    results = payload.get("results")
    if not isinstance(results, Mapping):
        raise ValueError("results must be object")
    _assert_results_schema(results=results, requested_backends=requested_backends)

    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("summary must be object")

    executed = [name for name in requested_backends if str(results[name].get("status", "")) == "executed"]
    blocked = [name for name in requested_backends if str(results[name].get("status", "")) == "blocked"]
    failed = [name for name in requested_backends if str(results[name].get("status", "")) == "failed"]

    requested_count = int(summary.get("requested_count", -1))
    executed_count = int(summary.get("executed_count", -1))
    blocked_count = int(summary.get("blocked_count", -1))
    failed_count = int(summary.get("failed_count", -1))
    if requested_count != len(requested_backends):
        raise ValueError("summary.requested_count mismatch")
    if executed_count != len(executed):
        raise ValueError("summary.executed_count mismatch")
    if blocked_count != len(blocked):
        raise ValueError("summary.blocked_count mismatch")
    if failed_count != len(failed):
        raise ValueError("summary.failed_count mismatch")

    executed_backends = _assert_str_list(summary.get("executed_backends"), "summary.executed_backends")
    blocked_backends = _assert_str_list(summary.get("blocked_backends"), "summary.blocked_backends")
    failed_backends = _assert_str_list(summary.get("failed_backends"), "summary.failed_backends")
    if sorted(executed_backends) != sorted(executed):
        raise ValueError("summary.executed_backends mismatch")
    if sorted(blocked_backends) != sorted(blocked):
        raise ValueError("summary.blocked_backends mismatch")
    if sorted(failed_backends) != sorted(failed):
        raise ValueError("summary.failed_backends mismatch")

    progress_ratio = float(summary.get("progress_ratio", -1.0))
    expected_progress = float(len(executed)) / float(len(requested_backends)) if len(requested_backends) > 0 else 0.0
    if abs(progress_ratio - expected_progress) > 1e-9:
        raise ValueError(
            f"summary.progress_ratio mismatch: got={progress_ratio}, expected={expected_progress}"
        )

    required_executed = _parse_required_backends(args.require_backend_executed)
    for backend_name in required_executed:
        if str(results.get(backend_name, {}).get("status", "")) != "executed":
            raise ValueError(f"required backend not executed: {backend_name}")

    print("validate_scene_backend_golden_path_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  requested_backends: {requested_backends}")
    print(f"  executed_backends: {executed}")
    print(f"  blocked_backends: {blocked}")
    print(f"  failed_backends: {failed}")


if __name__ == "__main__":
    main()

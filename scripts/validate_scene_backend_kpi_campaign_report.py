#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


ALLOWED_STATUS = ("ready", "blocked")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate scene backend KPI campaign report")
    p.add_argument("--summary-json", required=True, help="KPI campaign summary JSON path")
    p.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail validation if campaign_status != ready",
    )
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("summary json must be object")
    return payload


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


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"summary report not found: {summary_path}")

    payload = _load_json(summary_path)

    version = int(payload.get("version", 0))
    if version != 1:
        raise ValueError(f"version must be 1, got: {version}")

    source = str(payload.get("source_golden_path_summary_json", "")).strip()
    if source == "":
        raise ValueError("source_golden_path_summary_json must be non-empty")
    source_path = Path(source).expanduser()
    if not source_path.is_absolute() or (not source_path.exists()):
        raise ValueError("source_golden_path_summary_json must be absolute existing path")

    reference_backend = str(payload.get("reference_backend", "")).strip()
    if reference_backend == "":
        raise ValueError("reference_backend must be non-empty")

    requested_backends = _assert_str_list(payload.get("requested_backends"), "requested_backends")
    executed_backends = _assert_str_list(payload.get("executed_backends"), "executed_backends")

    campaign_status = str(payload.get("campaign_status", "")).strip()
    if campaign_status not in ALLOWED_STATUS:
        raise ValueError(f"campaign_status invalid: {campaign_status}")

    blockers = payload.get("blockers")
    if not isinstance(blockers, list):
        raise ValueError("blockers must be list")
    if campaign_status == "ready" and len(blockers) != 0:
        raise ValueError("ready report must have empty blockers")
    if campaign_status == "blocked" and len(blockers) == 0:
        raise ValueError("blocked report must have non-empty blockers")

    comparisons = payload.get("comparisons")
    if not isinstance(comparisons, list):
        raise ValueError("comparisons must be list")

    compared_count = 0
    fail_count = 0
    pass_count = 0
    for idx, row in enumerate(comparisons):
        if not isinstance(row, Mapping):
            raise ValueError(f"comparisons[{idx}] must be object")
        for key in (
            "reference_backend",
            "candidate_backend",
            "reference_status",
            "candidate_status",
            "compared",
            "parity",
            "kpi",
            "reason",
        ):
            if key not in row:
                raise ValueError(f"comparisons[{idx}] missing key: {key}")

        compared = bool(row.get("compared", False))
        parity = row.get("parity")
        if compared:
            if not isinstance(parity, Mapping):
                raise ValueError(f"comparisons[{idx}].parity must be object when compared=true")
            if "pass" not in parity:
                raise ValueError(f"comparisons[{idx}].parity.pass missing")
            if "metrics" not in parity or not isinstance(parity.get("metrics"), Mapping):
                raise ValueError(f"comparisons[{idx}].parity.metrics missing/invalid")
            compared_count += 1
            if bool(parity.get("pass", False)):
                pass_count += 1
            else:
                fail_count += 1
        else:
            reason = str(row.get("reason", "")).strip()
            if reason == "":
                raise ValueError(f"comparisons[{idx}].reason required when compared=false")

    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("summary must be object")

    if int(summary.get("requested_backend_count", -1)) != len(requested_backends):
        raise ValueError("summary.requested_backend_count mismatch")
    if int(summary.get("executed_backend_count", -1)) != len(executed_backends):
        raise ValueError("summary.executed_backend_count mismatch")
    if int(summary.get("compared_pair_count", -1)) != compared_count:
        raise ValueError("summary.compared_pair_count mismatch")
    if int(summary.get("parity_pass_count", -1)) != pass_count:
        raise ValueError("summary.parity_pass_count mismatch")
    if int(summary.get("parity_fail_count", -1)) != fail_count:
        raise ValueError("summary.parity_fail_count mismatch")

    if args.require_ready and campaign_status != "ready":
        raise ValueError(f"campaign_status must be ready, got: {campaign_status}")

    print("validate_scene_backend_kpi_campaign_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  campaign_status: {campaign_status}")
    print(f"  compared_pair_count: {compared_count}")
    print(f"  parity_fail_count: {fail_count}")


if __name__ == "__main__":
    main()

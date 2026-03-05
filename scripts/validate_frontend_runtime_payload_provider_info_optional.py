#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping

from avxsim.runtime_providers.radarsimpy_rt_provider import generate_radarsimpy_like_paths


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Optional contract validator: frontend-style runtime_input payload -> "
            "radarsimpy_rt provider_runtime_info multiplexing fields."
        )
    )
    p.add_argument(
        "--require-runtime",
        action="store_true",
        help="Fail instead of skipping when RadarSimPy runtime is unavailable.",
    )
    p.add_argument("--output-json", default="")
    return p.parse_args()


def _resolve_output_json(raw: str) -> Path | None:
    text = str(raw).strip()
    if text == "":
        return None
    p = Path(text).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    else:
        p = p.resolve()
    return p


def _write_report(path: Path | None, payload: Mapping[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2), encoding="utf-8")


def _is_runtime_unavailable(exc: Exception) -> bool:
    text = str(exc).lower()
    tokens = (
        "no module named 'radarsimpy'",
        'no module named "radarsimpy"',
        "required modules unavailable",
        "radarsimpy",
    )
    if ("no module named" in text) and ("radarsimpy" in text):
        return True
    if "required modules unavailable" in text:
        return True
    if ("runtime provider failed" in text) and ("radarsimpy" in text):
        return True
    return any(tok in text for tok in tokens[:2])


def _base_context(runtime_input: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "n_chirps": 4,
        "fc_hz": 77.0e9,
        "radar": {
            "fs_hz": 20.0e6,
            "samples_per_chirp": 256,
            "slope_hz_per_s": 20.0e12,
        },
        "backend": {
            "tx_pos_m": [[0.0, 0.0, 0.0], [0.06, 0.0, 0.0]],
            "rx_pos_m": [[0.0, 0.0, 0.0], [0.0, 0.05, 0.0]],
            "tx_schedule": [0, 1, 0, 1],
        },
        "runtime_input": dict(runtime_input),
    }


def run() -> None:
    args = _parse_args()
    out_json = _resolve_output_json(args.output_json)

    report: Dict[str, Any] = {
        "report_name": "frontend_runtime_payload_provider_info_optional",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "require_runtime": bool(args.require_runtime),
        "runtime_available": False,
        "skipped": False,
        "skip_reason": None,
        "pass": False,
        "cases": [],
        "error": None,
    }

    cases = [
        {
            "case_id": "frontend_runtime_tdm",
            "runtime_input": {
                "simulation_mode": "radarsimpy_adc",
                "device": "cpu",
                "multiplexing_mode": "tdm",
            },
            "expected_mode": "tdm",
            "expected_active_tx_per_chirp": [1, 1, 1, 1],
            "expected_plan_source": "runtime_input",
        },
        {
            "case_id": "frontend_runtime_bpm",
            "runtime_input": {
                "simulation_mode": "radarsimpy_adc",
                "device": "cpu",
                "multiplexing_mode": "bpm",
                "bpm_phase_code_deg": [0, 180, 0, 180],
            },
            "expected_mode": "bpm",
            "expected_active_tx_per_chirp": [2, 2, 2, 2],
            "expected_plan_source": "runtime_input",
        },
        {
            "case_id": "frontend_runtime_custom",
            "runtime_input": {
                "simulation_mode": "radarsimpy_adc",
                "device": "cpu",
                "multiplexing_mode": "custom",
                "tx_multiplexing_plan": {
                    "mode": "custom",
                    "pulse_amp": [[1.0, 0.5, 1.0, 0.5], [0.5, 1.0, 0.5, 1.0]],
                    "pulse_phs_deg": [[0.0, 45.0, 90.0, 135.0], [180.0, 225.0, 270.0, 315.0]],
                },
            },
            "expected_mode": "custom",
            "expected_active_tx_per_chirp": [2, 2, 2, 2],
            "expected_plan_source": "runtime_input.tx_multiplexing_plan",
        },
    ]

    try:
        for row in cases:
            context = _base_context(row["runtime_input"])
            result = generate_radarsimpy_like_paths(context)
            report["runtime_available"] = True
            info = (result or {}).get("provider_runtime_info")
            if not isinstance(info, Mapping):
                raise AssertionError("provider_runtime_info missing")

            observed_mode = str(info.get("multiplexing_mode", "")).strip().lower()
            observed_active = [int(x) for x in list(info.get("active_tx_per_chirp", []))]
            observed_source = str(info.get("multiplexing_plan_source", "")).strip()
            observed_amp_shape = [int(x) for x in list(info.get("pulse_amp_shape", []))]
            observed_phs_shape = [int(x) for x in list(info.get("pulse_phs_deg_shape", []))]

            case_pass = bool(
                observed_mode == str(row["expected_mode"])
                and observed_active == list(row["expected_active_tx_per_chirp"])
                and observed_source == str(row["expected_plan_source"])
                and observed_amp_shape == [2, 4]
                and observed_phs_shape == [2, 4]
            )
            report["cases"].append(
                {
                    "case_id": str(row["case_id"]),
                    "pass": bool(case_pass),
                    "expected_mode": str(row["expected_mode"]),
                    "observed_mode": observed_mode,
                    "expected_active_tx_per_chirp": list(row["expected_active_tx_per_chirp"]),
                    "observed_active_tx_per_chirp": observed_active,
                    "expected_plan_source": str(row["expected_plan_source"]),
                    "observed_plan_source": observed_source,
                    "observed_pulse_amp_shape": observed_amp_shape,
                    "observed_pulse_phs_deg_shape": observed_phs_shape,
                }
            )
            if not case_pass:
                raise AssertionError(f"provider info mismatch: {row['case_id']}")
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        runtime_missing = _is_runtime_unavailable(exc)
        if runtime_missing:
            report["runtime_available"] = False
            report["skip_reason"] = reason
            if bool(args.require_runtime):
                report["pass"] = False
                report["error"] = f"required runtime unavailable: {reason}"
                _write_report(out_json, report)
                raise AssertionError(report["error"])
            report["skipped"] = True
            report["pass"] = True
            _write_report(out_json, report)
            print("validate_frontend_runtime_payload_provider_info_optional: pass (skipped)")
            print(f"skip_reason={reason}")
            return
        report["pass"] = False
        report["error"] = reason
        _write_report(out_json, report)
        raise

    report["pass"] = bool(all(bool(x.get("pass", False)) for x in report["cases"]))
    _write_report(out_json, report)
    if not bool(report["pass"]):
        raise AssertionError("frontend runtime payload/provider info parity failed")

    print("validate_frontend_runtime_payload_provider_info_optional: pass")
    print(f"case_count={len(report['cases'])}")


if __name__ == "__main__":
    run()

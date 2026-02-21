#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _write_batch_summary(path: Path) -> None:
    payload = {
        "version": 1,
        "case_count": 2,
        "cases": [
            {
                "label": "saturated_case",
                "baseline_summary": {
                    "candidate_count": 512,
                    "pass_rate": 0.01,
                },
                "best_attempt": {
                    "replay_summary": {
                        "pass_rate": 1.0,
                    },
                    "delta": {
                        "pass_rate_delta": 0.99,
                    },
                    "candidate_pass_status_changed": 500,
                },
            },
            {
                "label": "normal_case",
                "baseline_summary": {
                    "candidate_count": 128,
                    "pass_rate": 0.2,
                },
                "best_attempt": {
                    "replay_summary": {
                        "pass_rate": 0.28,
                    },
                    "delta": {
                        "pass_rate_delta": 0.08,
                    },
                    "candidate_pass_status_changed": 20,
                },
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_fit_aware_saturation_") as td:
        root = Path(td)
        batch_json = root / "batch_summary.json"
        out_json = root / "saturation_summary.json"
        _write_batch_summary(batch_json)

        cmd = [
            "python3",
            "scripts/analyze_fit_aware_replay_saturation.py",
            "--batch-summary-json",
            str(batch_json),
            "--output-json",
            str(out_json),
            "--max-allowed-saturated-cases",
            "0",
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"analysis failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        result = json.loads(out_json.read_text(encoding="utf-8"))
        if int(result.get("saturated_case_count", 0)) != 1:
            raise AssertionError("expected exactly one saturated case")
        if bool(result.get("gate_failed", False)) is not True:
            raise AssertionError("expected gate_failed=true")
        if str(result.get("recommendation", "")) != "proxy_strength_review_required":
            raise AssertionError("unexpected recommendation")

        out_json_relaxed = root / "saturation_summary_relaxed.json"
        cmd_relaxed = [
            "python3",
            "scripts/analyze_fit_aware_replay_saturation.py",
            "--batch-summary-json",
            str(batch_json),
            "--output-json",
            str(out_json_relaxed),
            "--max-allowed-saturated-cases",
            "1",
        ]
        proc_relaxed = subprocess.run(
            cmd_relaxed, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False
        )
        if proc_relaxed.returncode != 0:
            raise RuntimeError(
                f"relaxed analysis failed:\nSTDOUT:\n{proc_relaxed.stdout}\nSTDERR:\n{proc_relaxed.stderr}"
            )

        result_relaxed = json.loads(out_json_relaxed.read_text(encoding="utf-8"))
        if bool(result_relaxed.get("gate_failed", True)) is not False:
            raise AssertionError("expected gate_failed=false when max_allowed_saturated_cases=1")

    print("validate_fit_aware_replay_saturation: pass")


if __name__ == "__main__":
    main()

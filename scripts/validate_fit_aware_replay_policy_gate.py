#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _write_batch_ok(path: Path) -> None:
    payload = {
        "version": 1,
        "baseline_mode": "rerun",
        "cases": [
            {
                "label": "c0",
                "baseline_summary": {"pass_count": 100, "fail_count": 0, "pass_rate": 1.0},
                "attempts": [
                    {
                        "attempt_index": 0,
                        "attempt_id": "a0",
                        "fit_json": "/tmp/fit0.json",
                        "delta": {
                            "pass_count_delta": 5,
                            "fail_count_delta": -5,
                            "pass_rate_delta": 0.05,
                        },
                    },
                    {
                        "attempt_index": 1,
                        "attempt_id": "a1",
                        "fit_json": "/tmp/fit1.json",
                        "delta": {
                            "pass_count_delta": -1,
                            "fail_count_delta": 1,
                            "pass_rate_delta": -0.01,
                        },
                    },
                ],
            },
            {
                "label": "c1",
                "baseline_summary": {"pass_count": 80, "fail_count": 20, "pass_rate": 0.8},
                "attempts": [
                    {
                        "attempt_index": 0,
                        "attempt_id": "a0",
                        "fit_json": "/tmp/fit0.json",
                        "delta": {
                            "pass_count_delta": 0,
                            "fail_count_delta": 0,
                            "pass_rate_delta": 0.0,
                        },
                    }
                ],
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_batch_bad(path: Path) -> None:
    payload = {
        "version": 1,
        "baseline_mode": "rerun",
        "cases": [
            {
                "label": "c0",
                "baseline_summary": {"pass_count": 100, "fail_count": 0, "pass_rate": 1.0},
                "attempts": [
                    {
                        "attempt_index": 0,
                        "attempt_id": "a0",
                        "fit_json": "/tmp/fit0.json",
                        "delta": {
                            "pass_count_delta": -10,
                            "fail_count_delta": 10,
                            "pass_rate_delta": -0.1,
                        },
                    }
                ],
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_fit_aware_policy_gate_") as td:
        root = Path(td)
        batch_ok = root / "batch_ok.json"
        out_ok = root / "out_ok.json"
        _write_batch_ok(batch_ok)

        cmd_ok = [
            "python3",
            "scripts/evaluate_fit_aware_replay_policy_gate.py",
            "--batch-summary-json",
            str(batch_ok),
            "--output-json",
            str(out_ok),
            "--require-non-degradation-all-cases",
            "--min-improved-cases",
            "1",
        ]
        p_ok = subprocess.run(cmd_ok, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if p_ok.returncode != 0:
            raise RuntimeError(f"policy gate (ok) failed:\nSTDOUT:\n{p_ok.stdout}\nSTDERR:\n{p_ok.stderr}")
        r_ok = json.loads(out_ok.read_text(encoding="utf-8"))
        if bool(r_ok.get("gate_failed", True)):
            raise AssertionError("expected gate_failed=false for non-degrading improved batch")
        if str(r_ok.get("recommendation", "")) != "accept_fit_lock":
            raise AssertionError("unexpected recommendation for ok batch")

        batch_bad = root / "batch_bad.json"
        out_bad = root / "out_bad.json"
        _write_batch_bad(batch_bad)

        cmd_bad = [
            "python3",
            "scripts/evaluate_fit_aware_replay_policy_gate.py",
            "--batch-summary-json",
            str(batch_bad),
            "--output-json",
            str(out_bad),
            "--require-non-degradation-all-cases",
            "--min-improved-cases",
            "1",
        ]
        p_bad = subprocess.run(cmd_bad, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if p_bad.returncode != 0:
            raise RuntimeError(
                f"policy gate (bad) failed unexpectedly:\nSTDOUT:\n{p_bad.stdout}\nSTDERR:\n{p_bad.stderr}"
            )
        r_bad = json.loads(out_bad.read_text(encoding="utf-8"))
        if bool(r_bad.get("gate_failed", False)) is not True:
            raise AssertionError("expected gate_failed=true for degradation-only batch")
        if str(r_bad.get("recommendation", "")) != "reject_fit_lock_due_to_degradation":
            raise AssertionError("unexpected recommendation for bad batch")

    print("validate_fit_aware_replay_policy_gate: pass")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _batch_for_select(path: Path) -> None:
    payload = {
        "version": 1,
        "baseline_mode": "rerun",
        "cases": [
            {
                "label": "case_a",
                "attempts": [
                    {
                        "fit_json": "/fit/fit_good.json",
                        "delta": {
                            "pass_count_delta": 3,
                            "fail_count_delta": -3,
                            "pass_rate_delta": 0.03,
                        },
                    },
                    {
                        "fit_json": "/fit/fit_bad.json",
                        "delta": {
                            "pass_count_delta": -2,
                            "fail_count_delta": 2,
                            "pass_rate_delta": -0.02,
                        },
                    },
                    {
                        "fit_json": "/fit/fit_flat.json",
                        "delta": {
                            "pass_count_delta": 0,
                            "fail_count_delta": 0,
                            "pass_rate_delta": 0.0,
                        },
                    },
                ],
            },
            {
                "label": "case_b",
                "attempts": [
                    {
                        "fit_json": "/fit/fit_good.json",
                        "delta": {
                            "pass_count_delta": 1,
                            "fail_count_delta": -1,
                            "pass_rate_delta": 0.01,
                        },
                    },
                    {
                        "fit_json": "/fit/fit_bad.json",
                        "delta": {
                            "pass_count_delta": -5,
                            "fail_count_delta": 5,
                            "pass_rate_delta": -0.05,
                        },
                    },
                    {
                        "fit_json": "/fit/fit_flat.json",
                        "delta": {
                            "pass_count_delta": 0,
                            "fail_count_delta": 0,
                            "pass_rate_delta": 0.0,
                        },
                    },
                ],
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_fit_lock_select_") as td:
        root = Path(td)
        batch_json = root / "batch.json"
        _batch_for_select(batch_json)

        out_ok = root / "select_ok.json"
        cmd_ok = [
            "python3",
            "scripts/select_measured_replay_fit_lock_by_policy.py",
            "--batch-summary-json",
            str(batch_json),
            "--output-json",
            str(out_ok),
            "--min-improved-cases",
            "1",
            "--require-full-case-coverage",
        ]
        p_ok = subprocess.run(cmd_ok, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if p_ok.returncode != 0:
            raise RuntimeError(
                f"selector (ok case) failed:\nSTDOUT:\n{p_ok.stdout}\nSTDERR:\n{p_ok.stderr}"
            )
        r_ok = json.loads(out_ok.read_text(encoding="utf-8"))
        sel_ok = r_ok["selection"]
        if str(sel_ok.get("selection_mode", "")) != "fit":
            raise AssertionError("expected fit selection mode for eligible fit")
        if str(sel_ok.get("selected_fit_json", "")) != "/fit/fit_good.json":
            raise AssertionError("expected fit_good selected")

        out_fallback = root / "select_fallback.json"
        cmd_fallback = [
            "python3",
            "scripts/select_measured_replay_fit_lock_by_policy.py",
            "--batch-summary-json",
            str(batch_json),
            "--output-json",
            str(out_fallback),
            "--min-improved-cases",
            "3",
            "--require-full-case-coverage",
        ]
        p_fb = subprocess.run(
            cmd_fallback, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False
        )
        if p_fb.returncode != 0:
            raise RuntimeError(
                f"selector (fallback case) failed:\nSTDOUT:\n{p_fb.stdout}\nSTDERR:\n{p_fb.stderr}"
            )
        r_fb = json.loads(out_fallback.read_text(encoding="utf-8"))
        sel_fb = r_fb["selection"]
        if str(sel_fb.get("selection_mode", "")) != "baseline_no_fit":
            raise AssertionError("expected baseline_no_fit fallback when no eligible fit")
        if sel_fb.get("selected_fit_json", None) is not None:
            raise AssertionError("selected_fit_json must be null in fallback mode")

    print("validate_select_measured_replay_fit_lock_by_policy: pass")


if __name__ == "__main__":
    main()

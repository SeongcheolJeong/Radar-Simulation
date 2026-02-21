#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _write_report(path: Path, rd_val: float, ra_val: float, pass_flag: bool = True) -> None:
    payload = {
        "version": 1,
        "summary": {
            "case_count": 1,
            "candidate_count": 1,
            "pass_count": 1 if pass_flag else 0,
            "fail_count": 0 if pass_flag else 1,
            "pass_rate": 1.0 if pass_flag else 0.0,
        },
        "cases": [
            {
                "scenario_id": "s0",
                "candidates": [
                    {
                        "name": "c0",
                        "pass": bool(pass_flag),
                        "metrics": {
                            "rd_shape_nmse": float(rd_val),
                            "ra_shape_nmse": float(ra_val),
                        },
                    }
                ],
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_batch(path: Path, base: Path, cand_good: Path, cand_bad: Path) -> None:
    payload = {
        "version": 1,
        "baseline_mode": "rerun",
        "cases": [
            {
                "label": "case0",
                "baseline_summary": {
                    "candidate_count": 1,
                    "pass_count": 1,
                    "fail_count": 0,
                    "pass_rate": 1.0,
                },
                "baseline_replay_report_json": str(base),
                "attempts": [
                    {
                        "attempt_index": 0,
                        "attempt_id": "a_good",
                        "fit_json": "/fit/good.json",
                        "replay_report_json": str(cand_good),
                        "delta": {
                            "pass_count_delta": 0.0,
                            "fail_count_delta": 0.0,
                            "pass_rate_delta": 0.0,
                        },
                    },
                    {
                        "attempt_index": 1,
                        "attempt_id": "a_bad",
                        "fit_json": "/fit/bad.json",
                        "replay_report_json": str(cand_bad),
                        "delta": {
                            "pass_count_delta": 0.0,
                            "fail_count_delta": 0.0,
                            "pass_rate_delta": 0.0,
                        },
                    },
                ],
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_fit_lock_drift_select_") as td:
        root = Path(td)
        base = root / "base.json"
        good = root / "good.json"
        bad = root / "bad.json"
        _write_report(base, rd_val=0.10, ra_val=0.20, pass_flag=True)
        _write_report(good, rd_val=0.11, ra_val=0.21, pass_flag=True)  # small drift
        _write_report(bad, rd_val=0.30, ra_val=0.50, pass_flag=True)   # large drift

        batch = root / "batch.json"
        _write_batch(batch, base=base, cand_good=good, cand_bad=bad)

        out_ok = root / "out_ok.json"
        cmd_ok = [
            "python3",
            "scripts/select_measured_replay_fit_lock_by_drift_objective.py",
            "--batch-summary-json",
            str(batch),
            "--output-json",
            str(out_ok),
            "--max-pass-rate-drop",
            "0.0",
            "--max-pass-count-drop-ratio",
            "0.0",
            "--max-fail-count-increase-ratio",
            "0.0",
            "--max-metric-drift",
            "10.0",
            "--require-full-case-coverage",
        ]
        p_ok = subprocess.run(cmd_ok, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if p_ok.returncode != 0:
            raise RuntimeError(f"drift selector failed:\nSTDOUT:\n{p_ok.stdout}\nSTDERR:\n{p_ok.stderr}")
        r_ok = json.loads(out_ok.read_text(encoding="utf-8"))
        sel_ok = r_ok["selection"]
        if str(sel_ok.get("selection_mode", "")) != "fit":
            raise AssertionError("expected fit selection mode")
        if str(sel_ok.get("selected_fit_json", "")) != "/fit/good.json":
            raise AssertionError("expected /fit/good.json selection")

        out_fb = root / "out_fb.json"
        cmd_fb = [
            "python3",
            "scripts/select_measured_replay_fit_lock_by_drift_objective.py",
            "--batch-summary-json",
            str(batch),
            "--output-json",
            str(out_fb),
            "--max-pass-rate-drop",
            "0.0",
            "--max-pass-count-drop-ratio",
            "0.0",
            "--max-fail-count-increase-ratio",
            "0.0",
            "--max-metric-drift",
            "0.01",
            "--require-full-case-coverage",
        ]
        p_fb = subprocess.run(cmd_fb, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if p_fb.returncode != 0:
            raise RuntimeError(
                f"drift selector fallback run failed:\nSTDOUT:\n{p_fb.stdout}\nSTDERR:\n{p_fb.stderr}"
            )
        r_fb = json.loads(out_fb.read_text(encoding="utf-8"))
        sel_fb = r_fb["selection"]
        if str(sel_fb.get("selection_mode", "")) != "baseline_no_fit":
            raise AssertionError("expected baseline_no_fit fallback")

    print("validate_select_measured_replay_fit_lock_by_drift_objective: pass")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _write_replay_report(path: Path, pass_count: int, fail_count: int) -> None:
    cand = int(pass_count + fail_count)
    payload = {
        "version": 1,
        "summary": {
            "case_count": 1,
            "candidate_count": cand,
            "pass_count": int(pass_count),
            "fail_count": int(fail_count),
            "pass_rate": (float(pass_count) / float(cand)) if cand > 0 else 0.0,
        },
        "cases": [],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_fit_lock_search_") as td:
        root = Path(td)
        pack_root = root / "packs" / "pack_a"
        pack_root.mkdir(parents=True, exist_ok=True)

        baseline_report = root / "baseline_report.json"
        _write_replay_report(baseline_report, pass_count=10, fail_count=0)

        fit1 = root / "path_power_fit_reflection_selected.json"
        fit2 = root / "path_power_fit_scattering_selected.json"
        fit_payload = {
            "version": 1,
            "fit": {"model": "reflection", "best_params": {"range_power_exponent": 4.0}},
        }
        fit1.write_text(json.dumps(fit_payload, indent=2), encoding="utf-8")
        fit2.write_text(json.dumps(fit_payload, indent=2), encoding="utf-8")

        out_json = root / "search_summary.json"
        cmd = [
            "python3",
            "scripts/run_measured_replay_fit_lock_search.py",
            "--baseline-mode",
            "provided",
            "--case",
            f"c0={pack_root}::{baseline_report}",
            "--fit-dir",
            str(root),
            "--output-root",
            str(root / "out"),
            "--output-summary-json",
            str(out_json),
            "--min-improved-cases",
            "1",
            "--require-full-case-coverage",
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(
                f"fit-lock search validation failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )

        result = json.loads(out_json.read_text(encoding="utf-8"))
        if bool(result.get("short_circuit", False)) is not True:
            raise AssertionError("expected short_circuit=true for zero-headroom baseline")
        if str(result.get("selection", {}).get("selection_mode", "")) != "baseline_no_fit":
            raise AssertionError("expected baseline_no_fit selection in short-circuit path")
        if str(result.get("selection", {}).get("recommendation", "")) != "fallback_to_baseline_no_fit":
            raise AssertionError("unexpected short-circuit recommendation")

    print("validate_measured_replay_fit_lock_search: pass")


if __name__ == "__main__":
    main()

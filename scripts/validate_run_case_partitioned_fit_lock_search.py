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


def _write_fit(path: Path, model: str) -> None:
    payload = {
        "version": 1,
        "fit": {
            "model": model,
            "best_params": {
                "range_power_exponent": 1.0,
                "gain_scale": 1.0,
            },
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run(cmd, cwd: Path, env):
    return subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, check=False)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_case_partitioned_search_") as td:
        root = Path(td)

        pack_a = root / "packs" / "pack_a"
        pack_b = root / "packs" / "pack_b"
        pack_a.mkdir(parents=True, exist_ok=True)
        pack_b.mkdir(parents=True, exist_ok=True)

        base_a = root / "baseline_a.json"
        base_b = root / "baseline_b.json"
        _write_replay_report(base_a, pass_count=10, fail_count=0)
        _write_replay_report(base_b, pass_count=8, fail_count=0)

        fit_ref = root / "fit_reflection.json"
        fit_sct = root / "fit_scattering.json"
        _write_fit(fit_ref, model="reflection")
        _write_fit(fit_sct, model="scattering")

        out_summary_json = root / "case_partitioned_summary.json"
        cmd = [
            "python3",
            "scripts/run_case_partitioned_fit_lock_search.py",
            "--baseline-mode",
            "provided",
            "--objective-mode",
            "improvement",
            "--case",
            f"a={pack_a}::{base_a}",
            "--case",
            f"b={pack_b}::{base_b}",
            "--case-family",
            "a=fam_a",
            "--case-family",
            "b=fam_b",
            "--fit-json",
            str(fit_ref),
            "--fit-json",
            str(fit_sct),
            "--output-root",
            str(root / "run"),
            "--output-summary-json",
            str(out_summary_json),
        ]
        proc = _run(cmd, cwd=repo_root, env=env)
        if proc.returncode != 0:
            raise RuntimeError(
                f"case-partitioned search validation failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )

        payload = json.loads(out_summary_json.read_text(encoding="utf-8"))
        if int(payload.get("case_count", 0)) != 2:
            raise AssertionError("unexpected case_count")
        if int(payload.get("family_count", 0)) != 2:
            raise AssertionError("unexpected family_count")
        if str(payload.get("global_selection", {}).get("selection_mode", "")) != "baseline_no_fit":
            raise AssertionError("expected global baseline_no_fit for zero-headroom synthetic baseline")
        fam_rows = payload.get("families", [])
        if not isinstance(fam_rows, list) or len(fam_rows) != 2:
            raise AssertionError("expected two family fallback rows")
        if str(payload.get("final", {}).get("strategy", "")) != "baseline_no_fit":
            raise AssertionError("expected baseline_no_fit final strategy")

    print("validate_run_case_partitioned_fit_lock_search: pass")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import csv
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _make_adc(shape, seed=0):
    rng = np.random.default_rng(seed)
    s, c, t, r = shape
    ys = np.arange(s, dtype=np.float64)[:, None, None, None]
    yc = np.arange(c, dtype=np.float64)[None, :, None, None]
    base = np.exp(1j * 2.0 * np.pi * ys / max(s, 1)) * np.exp(1j * 2.0 * np.pi * yc / max(c, 1))
    noise = 0.01 * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    return (base + noise).astype(np.complex64)


def _write_samples_csv(path: Path) -> None:
    cols = ["scenario_id", "range_m", "az_rad", "el_rad", "observed_amp"]
    rows = [
        {"scenario_id": "c0", "range_m": 20.0, "az_rad": 0.00, "el_rad": 0.00, "observed_amp": 1.00},
        {"scenario_id": "c0", "range_m": 28.0, "az_rad": 0.05, "el_rad": 0.01, "observed_amp": 0.84},
        {"scenario_id": "c0", "range_m": 36.0, "az_rad": 0.10, "el_rad": 0.02, "observed_amp": 0.72},
        {"scenario_id": "c0", "range_m": 44.0, "az_rad": 0.12, "el_rad": 0.03, "observed_amp": 0.60},
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def _run(cmd, cwd: Path, env):
    return subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, check=False)


def _resolve_replay_report(summary_json: Path) -> Path:
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    packs = payload.get("packs", [])
    if not isinstance(packs, list) or len(packs) == 0:
        raise AssertionError("baseline summary has no packs rows")
    replay_report = Path(str(packs[0].get("replay_report_json", ""))).expanduser().resolve()
    if not replay_report.exists():
        raise AssertionError(f"missing replay report from summary: {replay_report}")
    return replay_report


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_constrained_refit_") as td:
        root = Path(td)

        adc_root = root / "adc_npz"
        adc_root.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(adc_root / "frame_000.npz", adc=_make_adc((64, 16, 2, 4), seed=3))

        pack_root = root / "packs" / "pack_case"
        cmd_pack = [
            "python3",
            "scripts/build_pack_from_adc_npz_dir.py",
            "--input-root",
            str(adc_root),
            "--input-glob",
            "*.npz",
            "--output-pack-root",
            str(pack_root),
            "--scenario-id",
            "constrained_refit_validate_case",
            "--adc-order",
            "sctr",
            "--nfft-doppler",
            "64",
            "--nfft-angle",
            "16",
            "--range-bin-limit",
            "64",
        ]
        p_pack = _run(cmd_pack, cwd=repo_root, env=env)
        if p_pack.returncode != 0:
            raise RuntimeError(f"pack build failed:\nSTDOUT:\n{p_pack.stdout}\nSTDERR:\n{p_pack.stderr}")

        plan_json = root / "measured_replay_plan.json"
        cmd_plan = [
            "python3",
            "scripts/build_measured_replay_plan.py",
            "--packs-root",
            str(root / "packs"),
            "--output-plan-json",
            str(plan_json),
        ]
        p_plan = _run(cmd_plan, cwd=repo_root, env=env)
        if p_plan.returncode != 0:
            raise RuntimeError(f"plan build failed:\nSTDOUT:\n{p_plan.stdout}\nSTDERR:\n{p_plan.stderr}")

        baseline_summary_json = root / "measured_replay_summary.json"
        cmd_baseline = [
            "python3",
            "scripts/run_measured_replay_execution.py",
            "--plan-json",
            str(plan_json),
            "--output-root",
            str(root / "measured_replay_outputs"),
            "--output-summary-json",
            str(baseline_summary_json),
        ]
        p_base = _run(cmd_baseline, cwd=repo_root, env=env)
        if p_base.returncode != 0:
            raise RuntimeError(
                f"baseline replay failed:\nSTDOUT:\n{p_base.stdout}\nSTDERR:\n{p_base.stderr}"
            )

        baseline_report_json = _resolve_replay_report(baseline_summary_json)

        csv_path = root / "path_power_samples.csv"
        _write_samples_csv(csv_path)

        out_root = root / "constrained_refit_run"
        out_summary_json = root / "constrained_refit_summary.json"
        cmd = [
            "python3",
            "scripts/run_constrained_refit_drift_search.py",
            "--baseline-mode",
            "provided",
            "--case",
            f"c0={pack_root}::{baseline_report_json}",
            "--csv-case",
            f"c0={csv_path}",
            "--preset",
            "flat",
            "--allow-unlocked",
            "--output-root",
            str(out_root),
            "--output-summary-json",
            str(out_summary_json),
        ]
        p = _run(cmd, cwd=repo_root, env=env)
        if p.returncode != 0:
            raise RuntimeError(
                f"constrained refit search failed:\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
            )

        payload = json.loads(out_summary_json.read_text(encoding="utf-8"))
        if int(payload.get("preset_count", 0)) != 1:
            raise AssertionError("unexpected preset_count")
        if int(payload.get("case_count", 0)) != 1:
            raise AssertionError("unexpected case_count")
        if int(payload.get("csv_case_count", 0)) != 1:
            raise AssertionError("unexpected csv_case_count")

        rows = payload.get("rows", [])
        if not isinstance(rows, list) or len(rows) != 1:
            raise AssertionError("expected exactly one result row")
        row = rows[0]
        if str(row.get("preset", "")) != "flat":
            raise AssertionError("unexpected preset label")
        if bool(row.get("fit_batch_ok", False)) is not True:
            raise AssertionError("fit batch did not complete")
        if bool(row.get("search_ok", False)) is not True:
            raise AssertionError("fit-lock search did not complete")
        if str(row.get("objective_effective", "")) != "drift":
            raise AssertionError("objective_effective must be drift")

        rec = str(row.get("selection_recommendation", ""))
        if rec not in {
            "adopt_selected_fit_by_drift_objective",
            "exploratory_fit_candidate_selected_by_drift",
            "fallback_to_baseline_no_fit",
        }:
            raise AssertionError(f"unexpected selection recommendation: {rec}")

        fit_batch_summary_json = Path(str(row.get("fit_batch_summary_json", "")))
        search_summary_json = Path(str(row.get("search_summary_json", "")))
        if not fit_batch_summary_json.exists():
            raise AssertionError("missing fit batch summary json path")
        if not search_summary_json.exists():
            raise AssertionError("missing search summary json path")

        best = payload.get("best", None)
        if not isinstance(best, dict):
            raise AssertionError("best row must exist")
        if str(best.get("preset", "")) != "flat":
            raise AssertionError("unexpected best preset")

    print("validate_run_constrained_refit_drift_search: pass")


if __name__ == "__main__":
    main()

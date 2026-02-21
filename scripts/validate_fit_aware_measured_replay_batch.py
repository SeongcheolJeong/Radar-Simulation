#!/usr/bin/env python3
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


def _write_fit(path: Path, model: str, rexp: float) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "fit": {
                    "model": model,
                    "best_params": {
                        "range_power_exponent": float(rexp),
                        "gain_scale": 1.0,
                    },
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_fit_aware_batch_") as td:
        root = Path(td)
        run_root = root / "run_case"
        adc_root = run_root / "adc_npz"
        pack_root = run_root / "packs" / "pack_case"
        adc_root.mkdir(parents=True, exist_ok=True)

        # Single candidate => baseline pass_count cannot improve, enabling deterministic no-gain stop.
        np.savez_compressed(adc_root / "frame_000.npz", adc=_make_adc((64, 32, 2, 4), seed=1))

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
            "fit_aware_batch_case",
            "--adc-order",
            "sctr",
            "--nfft-doppler",
            "64",
            "--nfft-angle",
            "16",
            "--range-bin-limit",
            "64",
        ]
        p_pack = subprocess.run(cmd_pack, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if p_pack.returncode != 0:
            raise RuntimeError(f"pack build failed:\nSTDOUT:\n{p_pack.stdout}\nSTDERR:\n{p_pack.stderr}")

        baseline_plan = run_root / "measured_replay_plan.json"
        cmd_plan = [
            "python3",
            "scripts/build_measured_replay_plan.py",
            "--packs-root",
            str(run_root / "packs"),
            "--output-plan-json",
            str(baseline_plan),
        ]
        p_plan = subprocess.run(cmd_plan, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if p_plan.returncode != 0:
            raise RuntimeError(f"plan build failed:\nSTDOUT:\n{p_plan.stdout}\nSTDERR:\n{p_plan.stderr}")

        baseline_summary = run_root / "measured_replay_summary.json"
        cmd_replay = [
            "python3",
            "scripts/run_measured_replay_execution.py",
            "--plan-json",
            str(baseline_plan),
            "--output-root",
            str(run_root / "measured_replay_outputs"),
            "--output-summary-json",
            str(baseline_summary),
        ]
        p_replay = subprocess.run(cmd_replay, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if p_replay.returncode != 0:
            raise RuntimeError(f"baseline replay failed:\nSTDOUT:\n{p_replay.stdout}\nSTDERR:\n{p_replay.stderr}")

        fit1 = root / "fit1.json"
        fit2 = root / "fit2.json"
        _write_fit(fit1, model="scattering", rexp=2.5)
        _write_fit(fit2, model="reflection", rexp=5.0)

        out_root = root / "fit_aware_batch_out"
        out_json = root / "fit_aware_batch_summary.json"

        cmd_batch = [
            "python3",
            "scripts/run_fit_aware_measured_replay_batch.py",
            "--case",
            f"c0={pack_root}",
            "--fit-json",
            str(fit1),
            "--fit-json",
            str(fit2),
            "--max-no-gain-attempts",
            "1",
            "--output-root",
            str(out_root),
            "--output-summary-json",
            str(out_json),
        ]
        p_batch = subprocess.run(cmd_batch, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if p_batch.returncode != 0:
            raise RuntimeError(f"fit-aware batch failed:\nSTDOUT:\n{p_batch.stdout}\nSTDERR:\n{p_batch.stderr}")

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        if int(payload.get("case_count", 0)) != 1:
            raise AssertionError("unexpected case_count")
        case = payload["cases"][0]
        if int(case.get("fit_attempt_count", 0)) != 1:
            raise AssertionError("no-gain stop gate did not trigger at attempt 1")
        if str(case.get("stop_reason", "")) != "max_no_gain_reached":
            raise AssertionError("unexpected stop reason")

    print("validate_fit_aware_measured_replay_batch: pass")


if __name__ == "__main__":
    main()

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
    sig = np.exp(1j * 2.0 * np.pi * (ys / max(s, 1))) * np.exp(
        1j * 2.0 * np.pi * (yc / max(c, 1))
    )
    noise = 0.02 * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    return (sig + noise).astype(np.complex64)


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        adc_root = tmp_path / "adc_npz"
        adc_root.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(adc_root / "a0.npz", adc=_make_adc((64, 32, 2, 4), seed=1))
        np.savez_compressed(adc_root / "a1.npz", adc=_make_adc((64, 32, 2, 4), seed=2))

        work_root = tmp_path / "onboard_work"
        proc = subprocess.run(
            [
                "python3",
                "scripts/run_dataset_onboarding_pipeline.py",
                "--input-type",
                "adc_npz",
                "--input-root",
                str(adc_root),
                "--scenario-id",
                "onboard_mock_v1",
                "--work-root",
                str(work_root),
                "--adc-order",
                "sctr",
                "--allow-unlocked",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Dataset onboarding pipeline completed." in proc.stdout, proc.stdout

        summary_json = work_root / "measured_replay_summary.json"
        onboard_json = work_root / "onboarding_summary.json"
        plan_json = work_root / "measured_replay_plan.json"
        pack_root = work_root / "packs" / "pack_onboard_mock_v1"

        assert summary_json.exists()
        assert onboard_json.exists()
        assert plan_json.exists()
        assert (pack_root / "replay_manifest.json").exists()

        summary = json.loads(summary_json.read_text(encoding="utf-8"))
        assert summary["summary"]["pack_count"] == 1
        assert summary["summary"]["case_count"] == 1

        onboard = json.loads(onboard_json.read_text(encoding="utf-8"))
        assert onboard["input_type"] == "adc_npz"
        assert onboard["scenario_id"] == "onboard_mock_v1"

    print("Dataset onboarding pipeline validation passed.")


if __name__ == "__main__":
    run()

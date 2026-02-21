#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _write_case(root: Path, near_amp: float, far_amp: float) -> tuple[Path, Path]:
    pair = root / "frames" / "Tx0Rx0"
    pair.mkdir(parents=True, exist_ok=True)
    for idx, dnear in enumerate([20.0, 21.0, 22.0, 23.0], start=1):
        amp = np.zeros((16, 16), dtype=np.float32)
        dist = np.zeros((16, 16), dtype=np.float32)
        amp[4, 4] = near_amp
        dist[4, 4] = dnear
        amp[11, 11] = far_amp
        dist[11, 11] = 60.0 + idx
        np.save(pair / f"AmplitudeOutput{idx:04d}.npy", amp)
        np.save(pair / f"DistanceOutput{idx:04d}.npy", dist)

    radar_json = root / "radar_parameters_hybrid.json"
    radar_json.write_text(
        json.dumps(
            {
                "antenna_offsets_tx": {"Tx0": [0, 0, 0]},
                "antenna_offsets_rx": {"Rx0": [0, 0.00185, 0]},
            }
        ),
        encoding="utf-8",
    )
    return root / "frames", radar_json


def _fit_json(path: Path, rexp: float) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "fit": {
                    "model": "reflection",
                    "best_params": {
                        "range_power_exponent": float(rexp),
                        "gain_scale": 1.0,
                    },
                    "fc_hz": 77e9,
                    "p_t_dbm": 0.0,
                    "pixel_width": 1,
                    "pixel_height": 1,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "run_path_power_fit_lock_ab_comparison.py"

    with tempfile.TemporaryDirectory(prefix="validate_fit_lock_ab_") as td:
        root = Path(td)
        a_frames, a_radar = _write_case(root / "case_a", near_amp=1.0, far_amp=1.0)
        b_frames, b_radar = _write_case(root / "case_b", near_amp=1.0, far_amp=2.0)

        rmse_fit = root / "rmse_fit.json"
        cross_fit = root / "cross_fit.json"
        _fit_json(rmse_fit, rexp=5.0)
        _fit_json(cross_fit, rexp=0.1)

        out_root = root / "out"
        out_json = root / "ab_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        cmd = [
            "python3",
            str(cli),
            "--case-a-id",
            "a",
            "--case-a-frames-root",
            str(a_frames),
            "--case-a-radar-json",
            str(a_radar),
            "--case-b-id",
            "b",
            "--case-b-frames-root",
            str(b_frames),
            "--case-b-radar-json",
            str(b_radar),
            "--mode",
            "reflection",
            "--rmse-fit-json",
            str(rmse_fit),
            "--cross-family-fit-json",
            str(cross_fit),
            "--path-power-apply-mode",
            "shape_only",
            "--frame-start",
            "1",
            "--frame-end",
            "4",
            "--camera-fov-deg",
            "90",
            "--file-ext",
            ".npy",
            "--amplitude-threshold",
            "0.01",
            "--top-k-per-chirp",
            "8",
            "--estimation-nfft",
            "64",
            "--estimation-range-bin-length",
            "8",
            "--output-root",
            str(out_root),
            "--output-summary-json",
            str(out_json),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"fit lock A/B CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        runs = payload.get("runs", {})
        if "rmse_lock" not in runs or "cross_family_lock" not in runs:
            raise AssertionError("missing runs in A/B summary")

        rmse_score = float(runs["rmse_lock"]["score"])
        cross_score = float(runs["cross_family_lock"]["score"])
        winner = str(payload.get("ab_comparison", {}).get("winner_run_id", ""))
        score_tie = bool(payload.get("ab_comparison", {}).get("score_tie", False))
        expected = "cross_family_lock" if cross_score <= rmse_score else "rmse_lock"
        if winner != expected:
            raise AssertionError(f"winner mismatch: winner={winner}, expected={expected}")
        if score_tie != (abs(cross_score - rmse_score) <= 1e-12):
            raise AssertionError("score_tie flag mismatch")

        delta = payload.get("ab_comparison", {}).get("metric_delta_cross_minus_rmse", {})
        rm = runs["rmse_lock"]["b_tuned_metrics"]
        cm = runs["cross_family_lock"]["b_tuned_metrics"]
        keys = sorted(set(rm.keys()) & set(cm.keys()))
        if len(keys) == 0:
            raise AssertionError("no intersecting tuned metrics")
        for k in keys:
            d = float(delta[k]["delta"])
            expected_d = float(cm[k]) - float(rm[k])
            if abs(d - expected_d) > 1e-9:
                raise AssertionError(f"delta mismatch for {k}: {d} vs {expected_d}")

    print("validate_path_power_fit_lock_ab_comparison: pass")


if __name__ == "__main__":
    main()

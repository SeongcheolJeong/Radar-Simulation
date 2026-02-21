#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _prepare_frames(root: Path) -> None:
    pair = root / "frames" / "Tx0Rx0"
    pair.mkdir(parents=True, exist_ok=True)
    # Keep map amplitudes nearly flat across range so fitted model effect is visible.
    configs = [
        (20.0, 60.0, 1.0, 1.0),
        (22.0, 62.0, 1.0, 1.0),
        (24.0, 64.0, 1.0, 1.0),
        (26.0, 66.0, 1.0, 1.0),
    ]
    for idx, (d1, d2, a1, a2) in enumerate(configs, start=1):
        amp = np.zeros((16, 16), dtype=np.float32)
        dist = np.zeros((16, 16), dtype=np.float32)
        amp[4, 4] = a1
        dist[4, 4] = d1
        amp[11, 11] = a2
        dist[11, 11] = d2
        np.save(pair / f"AmplitudeOutput{idx:04d}.npy", amp)
        np.save(pair / f"DistanceOutput{idx:04d}.npy", dist)

    radar = {
        "antenna_offsets_tx": {"Tx0": [0, 0, 0]},
        "antenna_offsets_rx": {"Rx0": [0, 0.00185, 0]},
    }
    (root / "radar_parameters_hybrid.json").write_text(json.dumps(radar), encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "run_path_power_fit_cycle.py"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_path_power_fit_cycle_") as td:
        root = Path(td)
        _prepare_frames(root)
        summary_json = root / "cycle_summary.json"
        work_root = root / "work"
        cmd = [
            "python3",
            str(cli),
            "--frames-root",
            str(root / "frames"),
            "--radar-json",
            str(root / "radar_parameters_hybrid.json"),
            "--frame-start",
            "1",
            "--frame-end",
            "4",
            "--camera-fov-deg",
            "90",
            "--mode",
            "reflection",
            "--file-ext",
            ".npy",
            "--amplitude-threshold",
            "0.01",
            "--top-k-per-chirp",
            "4",
            "--fit-model",
            "reflection",
            "--path-power-apply-mode",
            "replace",
            "--work-root",
            str(work_root),
            "--scenario-id",
            "validate_cycle_demo",
            "--output-summary-json",
            str(summary_json),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"fit cycle failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        summary = json.loads(summary_json.read_text(encoding="utf-8"))
        base_slope = float(summary["path_amplitude_vs_range"]["baseline"]["log_slope"])
        tuned_slope = float(summary["path_amplitude_vs_range"]["tuned"]["log_slope"])
        delta = float(summary["path_amplitude_vs_range"]["delta_log_slope"])

        # Baseline is nearly flat. Tuned with reflection model should tilt downward with range.
        assert abs(base_slope) < 0.6, base_slope
        assert tuned_slope < base_slope - 0.3, (base_slope, tuned_slope)
        assert delta < -0.3, delta

        assert Path(summary["samples_csv"]).exists()
        assert Path(summary["fit_json"]).exists()
        assert Path(summary["baseline_output_dir"]).exists()
        assert Path(summary["tuned_output_dir"]).exists()

    print("validate_path_power_fit_cycle: pass")


if __name__ == "__main__":
    main()

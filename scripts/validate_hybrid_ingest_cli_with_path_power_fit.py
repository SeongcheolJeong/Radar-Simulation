#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _load_path_amplitudes(path_list_json: Path):
    payload = json.loads(path_list_json.read_text(encoding="utf-8"))
    chirp0 = payload[0]
    rows = []
    for p in chirp0:
        delay = float(p["delay_s"])
        amp = complex(float(p["amp_complex"]["re"]), float(p["amp_complex"]["im"]))
        rows.append((delay, abs(amp)))
    return sorted(rows, key=lambda x: x[0])


def run() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        frames_root = tmp / "frames"
        pair = frames_root / "Tx0Rx0"
        pair.mkdir(parents=True, exist_ok=True)

        amp = np.zeros((8, 8), dtype=np.float32)
        dist = np.zeros((8, 8), dtype=np.float32)
        amp[1, 1] = 1.0
        amp[6, 6] = 1.0
        dist[1, 1] = 20.0
        dist[6, 6] = 60.0
        np.save(pair / "AmplitudeOutput0001.npy", amp)
        np.save(pair / "DistanceOutput0001.npy", dist)

        radar_json = tmp / "radar_parameters_hybrid.json"
        radar_json.write_text(
            json.dumps(
                {
                    "antenna_offsets_tx": {"Tx0": [0, 0, 0]},
                    "antenna_offsets_rx": {"Rx0": [0, 0.00185, 0]},
                }
            ),
            encoding="utf-8",
        )

        fit_json = tmp / "path_power_fit.json"
        fit_json.write_text(
            json.dumps(
                {
                    "version": 1,
                    "fit": {
                        "model": "reflection",
                        "best_params": {
                            "range_power_exponent": 5.0,
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

        out_base = tmp / "out_base"
        cmd_base = [
            "python3",
            "scripts/run_hybrid_ingest_to_adc.py",
            "--frames-root",
            str(frames_root),
            "--radar-json",
            str(radar_json),
            "--frame-start",
            "1",
            "--frame-end",
            "1",
            "--camera-fov-deg",
            "90",
            "--mode",
            "reflection",
            "--file-ext",
            ".npy",
            "--amplitude-threshold",
            "0.1",
            "--output-dir",
            str(out_base),
        ]
        proc_base = subprocess.run(
            cmd_base,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "path power fit enabled: False" in proc_base.stdout, proc_base.stdout

        out_fit = tmp / "out_fit"
        cmd_fit = [
            "python3",
            "scripts/run_hybrid_ingest_to_adc.py",
            "--frames-root",
            str(frames_root),
            "--radar-json",
            str(radar_json),
            "--frame-start",
            "1",
            "--frame-end",
            "1",
            "--camera-fov-deg",
            "90",
            "--mode",
            "reflection",
            "--file-ext",
            ".npy",
            "--amplitude-threshold",
            "0.1",
            "--path-power-fit-json",
            str(fit_json),
            "--path-power-apply-mode",
            "shape_only",
            "--output-dir",
            str(out_fit),
        ]
        proc_fit = subprocess.run(
            cmd_fit,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "path power fit enabled: True" in proc_fit.stdout, proc_fit.stdout
        assert "path power fit model: reflection" in proc_fit.stdout, proc_fit.stdout

        base_rows = _load_path_amplitudes(out_base / "path_list.json")
        fit_rows = _load_path_amplitudes(out_fit / "path_list.json")
        assert len(base_rows) == 2
        assert len(fit_rows) == 2

        base_ratio = base_rows[0][1] / (base_rows[1][1] + 1e-12)
        fit_ratio = fit_rows[0][1] / (fit_rows[1][1] + 1e-12)
        # Baseline amplitudes are equal; fitted shape should emphasize near range path.
        assert abs(base_ratio - 1.0) < 1e-6, base_ratio
        assert fit_ratio > 5.0, fit_ratio

    print("Hybrid ingest CLI with path-power fit validation passed.")


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _write_case(root: Path, near_amp: float, far_amp: float) -> tuple[Path, Path]:
    frames = root / "frames" / "Tx0Rx0"
    frames.mkdir(parents=True, exist_ok=True)

    for idx, dnear in enumerate([20.0, 21.0, 22.0, 23.0], start=1):
        amp = np.zeros((16, 16), dtype=np.float32)
        dist = np.zeros((16, 16), dtype=np.float32)
        amp[4, 4] = float(near_amp)
        dist[4, 4] = float(dnear)
        amp[11, 11] = float(far_amp)
        dist[11, 11] = float(60.0 + idx)
        np.save(frames / f"AmplitudeOutput{idx:04d}.npy", amp)
        np.save(frames / f"DistanceOutput{idx:04d}.npy", dist)

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


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "run_hybrid_cross_family_fit_comparison.py"

    with tempfile.TemporaryDirectory(prefix="validate_cross_family_fit_cmp_") as td:
        root = Path(td)
        case_a_root = root / "case_a"
        case_b_root = root / "case_b"
        a_frames, a_radar = _write_case(case_a_root, near_amp=1.0, far_amp=1.0)
        b_frames, b_radar = _write_case(case_b_root, near_amp=1.0, far_amp=2.0)

        fit_json = root / "path_power_fit_reflection.json"
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

        out_root = root / "out"
        out_json = root / "summary.json"

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
            "--path-power-fit-json",
            str(fit_json),
            "--path-power-apply-mode",
            "shape_only",
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
            raise RuntimeError(f"cross-family fit comparison failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        delta = payload["cross_family_improvement"]["metric_delta"]

        # Expect at least one RD or RA metric to improve (tuned value < baseline value).
        improved = [k for k, v in delta.items() if bool(v.get("improved", False))]
        if len(improved) == 0:
            raise AssertionError("expected at least one improved metric")

    print("validate_hybrid_cross_family_fit_comparison: pass")


if __name__ == "__main__":
    main()

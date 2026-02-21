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


def _fit_json(path: Path, model: str, rexp: float) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "fit": {
                    "model": str(model),
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
    cli = repo_root / "scripts" / "rank_path_power_fits_by_cross_family.py"

    with tempfile.TemporaryDirectory(prefix="validate_fit_ranking_") as td:
        root = Path(td)
        a_frames, a_radar = _write_case(root / "case_a", near_amp=1.0, far_amp=1.0)
        b_frames, b_radar = _write_case(root / "case_b", near_amp=1.0, far_amp=2.0)

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        def _run_case(model: str, extra: list[str]) -> None:
            fit_neutral = root / f"fit_{model}_neutral.json"
            fit_aggr = root / f"fit_{model}_aggressive.json"
            _fit_json(fit_neutral, model=model, rexp=0.1)  # near-flat but valid (>0)
            _fit_json(fit_aggr, model=model, rexp=5.0)     # strong range-shape bias

            out_root = root / f"out_{model}"
            out_json = root / f"ranking_{model}.json"

            cmd = [
                "python3",
                str(cli),
                "--candidate-fit-json",
                str(fit_neutral),
                "--candidate-fit-json",
                str(fit_aggr),
                "--model",
                str(model),
                "--case-a-frames-root",
                str(a_frames),
                "--case-a-radar-json",
                str(a_radar),
                "--case-b-frames-root",
                str(b_frames),
                "--case-b-radar-json",
                str(b_radar),
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
            ] + list(extra)

            proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"fit ranking CLI failed ({model}):\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
                )

            payload = json.loads(out_json.read_text(encoding="utf-8"))
            assert payload["ok_count"] == 2
            ranked = payload["ranked"]
            assert len(ranked) == 2

            # Ranking should be sorted in ascending score.
            if float(ranked[0]["score"]) > float(ranked[1]["score"]):
                raise AssertionError(f"ranking is not sorted ({model}): {ranked}")

        _run_case("reflection", extra=[])
        _run_case(
            "scattering",
            extra=["--distance-prefix", "DistanceOutput", "--distance-scale", "1.0"],
        )

    print("validate_path_power_fit_cross_family_ranking: pass")


if __name__ == "__main__":
    main()

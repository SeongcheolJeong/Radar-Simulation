#!/Library/Developer/CommandLineTools/usr/bin/python3
import json
import tempfile
from pathlib import Path

import numpy as np

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_scene_analytic_") as td:
        root = Path(td)
        scene_json = root / "scene_analytic.json"
        scene_json.write_text(
            json.dumps(
                {
                    "scene_id": "analytic_scene_v1",
                    "backend": {
                        "type": "analytic_targets",
                        "n_chirps": 8,
                        "chirp_interval_s": 4.0e-5,
                        "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                        "rx_pos_m": [
                            [0.0, 0.00185, 0.0],
                            [0.0, 0.0037, 0.0],
                            [0.0, 0.00555, 0.0],
                            [0.0, 0.0074, 0.0],
                        ],
                        "targets": [
                            {
                                "range_m": 25.0,
                                "radial_velocity_mps": 3.0,
                                "az_deg": 5.0,
                                "el_deg": 0.0,
                                "amp": 1.0,
                                "range_amp_exponent": 2.0,
                            },
                            {
                                "range_m": 32.0,
                                "radial_velocity_mps": 0.0,
                                "az_deg": -8.0,
                                "el_deg": 0.0,
                                "amp": {"re": 0.7, "im": 0.1},
                                "range_amp_exponent": 2.0,
                            },
                        ],
                        "noise_sigma": 0.0,
                    },
                    "radar": {
                        "fc_hz": 77e9,
                        "slope_hz_per_s": 20e12,
                        "fs_hz": 20e6,
                        "samples_per_chirp": 1024,
                    },
                    "map_config": {
                        "nfft_range": 1024,
                        "nfft_doppler": 64,
                        "nfft_angle": 32,
                        "range_bin_limit": 128,
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        out_dir = root / "outputs"
        out = run_object_scene_to_radar_map_json(
            scene_json_path=str(scene_json),
            output_dir=str(out_dir),
            run_hybrid_estimation=False,
        )

        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        assert (out_dir / "radar_map.npz").exists()
        assert out["hybrid_estimation_npz"] is None
        assert out["frame_count"] == 8
        assert len(out["tx_schedule"]) == 8

        adc_payload = np.load(out_dir / "adc_cube.npz")
        adc = np.asarray(adc_payload["adc"])
        assert adc.shape == (1024, 8, 2, 4), adc.shape

        map_payload = np.load(out_dir / "radar_map.npz")
        rd = np.asarray(map_payload["fx_dop_win"])
        ra = np.asarray(map_payload["fx_ang"])
        assert rd.shape == (64, 128), rd.shape
        assert ra.shape == (32, 128), ra.shape

        meta = json.loads(str(map_payload["metadata_json"]))
        assert meta["backend_type"] == "analytic_targets"
        assert meta["frame_count"] == 8

    print("validate_object_scene_analytic_backend: pass")


if __name__ == "__main__":
    run()

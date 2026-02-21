#!/usr/bin/env python3
import json
import os
import tempfile
from pathlib import Path

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_scene_po_sbr_backend_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        os.environ.setdefault("PYTHONPATH", str(repo_root / "src"))

        po_sbr_paths_json = root / "po_sbr_paths.json"
        po_sbr_paths_json.write_text(
            json.dumps(
                {
                    "version": 1,
                    "paths": [
                        {
                            "chirp_index": 0,
                            "range_m": 20.0,
                            "range_mode": "one_way",
                            "radial_velocity_mps": 0.0,
                            "az_deg": 0.0,
                            "el_deg": 0.0,
                            "rcs_dbsm": -5.0,
                            "path_loss_db": 70.0,
                            "bounce_loss_db": 3.0,
                            "phase_rad": 0.1,
                            "path_id": "po_sbr_path_0",
                            "material_tag": "metal",
                            "bounce_count": 1,
                        },
                        {
                            "chirp_index": 1,
                            "delay_s": 2.0 * 22.0 / 299_792_458.0,
                            "doppler_hz": 0.0,
                            "unit_direction": [1.0, 0.0, 0.0],
                            "amp_complex": {"re": 2.0e-4, "im": -1.0e-5},
                            "path_id": "po_sbr_path_1",
                            "material_tag": "metal",
                            "reflection_order": 2,
                        },
                        {
                            "chirp_index": 2,
                            "delay_s": 2.0 * 24.0 / 299_792_458.0,
                            "doppler_hz": 0.0,
                            "u": [1.0, 0.0, 0.0],
                            "amp": [1.0e-4, 0.0],
                            "path_id": "po_sbr_path_2",
                            "material_tag": "metal",
                            "reflection_order": 1,
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        scene_json = root / "scene_po_sbr.json"
        scene_json.write_text(
            json.dumps(
                {
                    "scene_id": "po_sbr_scene_v1",
                    "backend": {
                        "type": "po_sbr_rt",
                        "n_chirps": 3,
                        "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                        "rx_pos_m": [
                            [0.0, 0.00185, 0.0],
                            [0.0, 0.0037, 0.0],
                            [0.0, 0.00555, 0.0],
                            [0.0, 0.0074, 0.0],
                        ],
                        "po_sbr_paths_json": str(po_sbr_paths_json),
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
        assert out["frame_count"] == 3
        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        assert (out_dir / "radar_map.npz").exists()

        path_payload = json.loads((out_dir / "path_list.json").read_text(encoding="utf-8"))
        assert len(path_payload) == 3
        assert path_payload[0][0]["path_id"] == "po_sbr_path_0"
        assert path_payload[1][0]["path_id"] == "po_sbr_path_1"
        assert path_payload[2][0]["path_id"] == "po_sbr_path_2"

    print("validate_object_scene_po_sbr_backend: pass")


if __name__ == "__main__":
    run()

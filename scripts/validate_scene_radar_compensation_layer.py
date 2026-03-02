#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

import numpy as np

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_scene_radar_comp_") as td:
        root = Path(td)
        scene_json = root / "scene_radar_compensation.json"
        scene_json.write_text(
            json.dumps(
                {
                    "scene_id": "radar_compensation_layer_v1",
                    "backend": {
                        "type": "analytic_targets",
                        "n_chirps": 4,
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
                                "radial_velocity_mps": 0.0,
                                "az_deg": 8.0,
                                "el_deg": 0.0,
                                "amp": 1.0,
                                "range_amp_exponent": 2.0,
                                "material_tag": "vehicle_metal",
                                "reflection_order": 1,
                                "path_id": "target_primary",
                            }
                        ],
                        "noise_sigma": 0.0,
                        "radar_compensation": {
                            "enabled": True,
                            "random_seed": 20260302,
                            "default_material_model": {
                                "reflectivity": 1.0,
                                "rcs_scale_linear": 1.0,
                                "reflection_decay": 1.0,
                                "wideband_slope_db_per_ghz": 0.0,
                            },
                            "material_models": {
                                "vehicle_metal": {
                                    "reflectivity": 0.92,
                                    "rcs_scale_linear": 1.35,
                                    "reflection_decay": 0.95,
                                    "wideband_slope_db_per_ghz": -0.6,
                                }
                            },
                            "wideband": {"enabled": True, "phase_weight": 1.0},
                            "manifold": {
                                "enabled": True,
                                "mag_db_bias": -0.2,
                                "mag_db_per_abs_az_deg": -0.004,
                                "mag_db_per_abs_el_deg": -0.002,
                                "phase_deg_bias": 3.0,
                                "phase_deg_per_az_deg": 0.35,
                                "phase_deg_per_el_deg": 0.1,
                                "phase_deg_per_reflection_order": 6.0,
                            },
                            "diffuse": {
                                "enabled": True,
                                "paths_per_specular": 2,
                                "amp_ratio": 0.2,
                                "delay_jitter_std": 0.01,
                                "doppler_sigma_hz": 3.0,
                                "direction_sigma_deg": 4.0,
                            },
                            "clutter": {
                                "enabled": True,
                                "paths_per_chirp": 3,
                                "range_min_m": 4.0,
                                "range_max_m": 35.0,
                                "az_min_deg": -35.0,
                                "az_max_deg": 35.0,
                                "el_mean_deg": 0.0,
                                "el_sigma_deg": 1.5,
                                "doppler_sigma_hz": 18.0,
                                "amp_abs": 1.5e-4,
                                "amp_db_sigma": 2.0,
                                "material_tag": "clutter",
                                "reflection_order": 1,
                            },
                        },
                    },
                    "radar": {
                        "fc_hz": 77e9,
                        "slope_hz_per_s": 20e12,
                        "fs_hz": 20e6,
                        "samples_per_chirp": 512,
                    },
                    "map_config": {
                        "nfft_range": 512,
                        "nfft_doppler": 32,
                        "nfft_angle": 16,
                        "range_bin_limit": 96,
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
        assert out["frame_count"] == 4
        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        assert (out_dir / "radar_map.npz").exists()

        summary = dict(out.get("path_contract_summary") or {})
        assert int(summary.get("path_count", -1)) == 24

        path_payload = json.loads((out_dir / "path_list.json").read_text(encoding="utf-8"))
        assert len(path_payload) == 4
        for chirp_idx, row in enumerate(path_payload):
            assert len(row) == 6, f"chirp[{chirp_idx}] path count mismatch: {len(row)}"
            ids = {str(p.get("path_id", "")) for p in row}
            assert "target_primary" in ids
            assert any(x.endswith("_df00") for x in ids)
            assert any(x.startswith(f"clutter_c{chirp_idx:04d}_k") for x in ids)

        map_payload = np.load(out_dir / "radar_map.npz")
        meta = json.loads(str(map_payload["metadata_json"]))
        comp = dict(meta.get("compensation_summary") or {})
        assert bool(comp.get("enabled", False)) is True
        assert int(comp.get("input_path_count", -1)) == 4
        assert int(comp.get("added_diffuse_path_count", -1)) == 8
        assert int(comp.get("added_clutter_path_count", -1)) == 12
        assert int(comp.get("output_path_count", -1)) == 24
        assert bool(comp.get("manifold_enabled", False)) is True
        assert bool(comp.get("wideband_enabled", False)) is True

    print("validate_scene_radar_compensation_layer: pass")


if __name__ == "__main__":
    run()

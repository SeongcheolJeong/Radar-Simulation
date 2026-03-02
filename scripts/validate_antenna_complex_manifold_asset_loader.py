#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

from avxsim.antenna_manifold_asset import load_complex_manifold_asset
from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_manifold_asset_") as td:
        root = Path(td)
        asset_path = root / "manifold_asset_openems_like.npz"
        _write_synthetic_asset_npz(asset_path)

        asset = load_complex_manifold_asset(str(asset_path))
        g0 = asset.monostatic_gain_from_azel(frequency_hz=77e9, az_deg=0.0, el_deg=0.0)
        g90 = asset.monostatic_gain_from_azel(frequency_hz=77e9, az_deg=90.0, el_deg=0.0)
        g45 = asset.monostatic_gain_from_azel(frequency_hz=77e9, az_deg=45.0, el_deg=0.0)
        g360 = asset.monostatic_gain_from_azel(frequency_hz=77e9, az_deg=360.0, el_deg=0.0)
        assert abs(g0 - (6.0 + 0.0j)) < 1.0e-12
        assert abs(g90 - (1.0 + 0.0j)) < 1.0e-12
        assert abs(g45 - (3.0 + 0.0j)) < 1.0e-12
        assert abs(g360 - g0) < 1.0e-12

        baseline_scene_json = root / "scene_baseline.json"
        _write_scene_json(
            out_json=baseline_scene_json,
            manifold_asset_path=None,
        )
        baseline_out = run_object_scene_to_radar_map_json(
            scene_json_path=str(baseline_scene_json),
            output_dir=str(root / "baseline_outputs"),
            run_hybrid_estimation=False,
        )
        base_amp = _load_path_amp_complex(Path(str(baseline_out["path_list_json"])), "target_primary")

        asset_scene_json = root / "scene_with_asset.json"
        _write_scene_json(
            out_json=asset_scene_json,
            manifold_asset_path="manifold_asset_openems_like.npz",
        )
        asset_out = run_object_scene_to_radar_map_json(
            scene_json_path=str(asset_scene_json),
            output_dir=str(root / "asset_outputs"),
            run_hybrid_estimation=False,
        )
        asset_amp = _load_path_amp_complex(Path(str(asset_out["path_list_json"])), "target_primary")
        ratio = abs(asset_amp / base_amp)
        assert abs(ratio - 6.0) < 1.0e-9, ratio

        with np.load(str(asset_out["radar_map_npz"]), allow_pickle=False) as map_payload:
            meta = json.loads(str(map_payload["metadata_json"]))
        comp = dict(meta.get("compensation_summary") or {})
        assert bool(comp.get("manifold_asset_enabled", False)) is True
        assert str(comp.get("manifold_asset_path", "")).endswith("manifold_asset_openems_like.npz")
        assert float(comp.get("manifold_asset_frequency_hz", 0.0)) == 77e9

    print("validate_antenna_complex_manifold_asset_loader: pass")


def _write_synthetic_asset_npz(path: Path) -> None:
    freq_hz = np.asarray([77e9], dtype=np.float64)
    theta_deg = np.asarray([0.0, 90.0, 180.0], dtype=np.float64)
    phi_deg = np.asarray([0.0, 90.0, 180.0, 270.0], dtype=np.float64)

    tx_by_phi = np.asarray([2.0, 1.0, 2.0, 3.0], dtype=np.float64)
    rx_by_phi = np.asarray([3.0, 1.0, 3.0, 5.0], dtype=np.float64)

    tx_re = np.tile(tx_by_phi.reshape(1, 1, -1), (1, theta_deg.size, 1))
    rx_re = np.tile(rx_by_phi.reshape(1, 1, -1), (1, theta_deg.size, 1))
    zeros = np.zeros_like(tx_re, dtype=np.float64)

    np.savez_compressed(
        str(path),
        freq_hz=freq_hz,
        theta_deg=theta_deg,
        phi_deg=phi_deg,
        Etheta_tx_re=tx_re,
        Etheta_tx_im=zeros,
        Ephi_tx_re=zeros,
        Ephi_tx_im=zeros,
        Etheta_rx_re=rx_re,
        Etheta_rx_im=zeros,
        Ephi_rx_re=zeros,
        Ephi_rx_im=zeros,
    )


def _write_scene_json(out_json: Path, manifold_asset_path: Optional[str]) -> None:
    manifold = {
        "enabled": True,
        "mag_db_bias": 0.0,
        "mag_db_per_abs_az_deg": 0.0,
        "mag_db_per_abs_el_deg": 0.0,
        "phase_deg_bias": 0.0,
        "phase_deg_per_az_deg": 0.0,
        "phase_deg_per_el_deg": 0.0,
        "phase_deg_per_reflection_order": 0.0,
    }
    if manifold_asset_path is not None:
        manifold["asset_path"] = str(manifold_asset_path)
        manifold["asset_gain_scale"] = 1.0

    payload = {
        "scene_id": "manifold_loader_scene_v1",
        "backend": {
            "type": "analytic_targets",
            "n_chirps": 1,
            "chirp_interval_s": 4.0e-5,
            "tx_pos_m": [[0.0, 0.0, 0.0]],
            "rx_pos_m": [[0.0, 0.00185, 0.0]],
            "targets": [
                {
                    "range_m": 20.0,
                    "radial_velocity_mps": 0.0,
                    "az_deg": 0.0,
                    "el_deg": 0.0,
                    "amp": 1.0,
                    "range_amp_exponent": 2.0,
                    "material_tag": "target_metal",
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
                    "target_metal": {
                        "reflectivity": 1.0,
                        "rcs_scale_linear": 1.0,
                        "reflection_decay": 1.0,
                        "wideband_slope_db_per_ghz": 0.0,
                    }
                },
                "wideband": {"enabled": False, "phase_weight": 1.0},
                "manifold": manifold,
                "diffuse": {"enabled": False, "paths_per_specular": 0},
                "clutter": {"enabled": False, "paths_per_chirp": 0},
            },
        },
        "radar": {
            "fc_hz": 77e9,
            "slope_hz_per_s": 20e12,
            "fs_hz": 20e6,
            "samples_per_chirp": 128,
        },
        "map_config": {
            "nfft_range": 128,
            "nfft_doppler": 8,
            "nfft_angle": 8,
            "range_bin_limit": 32,
        },
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_path_amp_complex(path_list_json: Path, path_id: str) -> complex:
    payload = json.loads(path_list_json.read_text(encoding="utf-8"))
    assert len(payload) == 1
    row = payload[0]
    assert len(row) == 1
    item = row[0]
    assert str(item.get("path_id")) == str(path_id)
    amp = dict(item.get("amp_complex") or {})
    return complex(float(amp.get("re", 0.0)), float(amp.get("im", 0.0)))


if __name__ == "__main__":
    run()

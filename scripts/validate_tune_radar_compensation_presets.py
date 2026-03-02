#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="validate_tune_radar_comp_") as td:
        root = Path(td)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        template_scene = _build_template_scene()
        target_patch = _target_patch()

        scene_template_json = root / "scene_template.json"
        scene_template_json.write_text(json.dumps(template_scene, indent=2), encoding="utf-8")

        reference_scene = json.loads(scene_template_json.read_text(encoding="utf-8"))
        reference_scene["backend"]["radar_compensation"] = _deep_merge(
            reference_scene["backend"]["radar_compensation"],
            target_patch,
        )
        reference_scene_json = root / "reference_scene.json"
        reference_scene_json.write_text(json.dumps(reference_scene, indent=2), encoding="utf-8")

        reference_out = root / "reference_outputs"
        reference_run = run_object_scene_to_radar_map_json(
            scene_json_path=str(reference_scene_json),
            output_dir=str(reference_out),
            run_hybrid_estimation=False,
        )
        reference_radar_map = Path(str(reference_run["radar_map_npz"])).resolve()

        candidates_json = root / "candidates.json"
        candidates_json.write_text(
            json.dumps(
                {
                    "candidates": [
                        {"name": "baseline", "patch": {}},
                        {"name": "target_like", "patch": target_patch},
                        {
                            "name": "worse_like",
                            "patch": {
                                "manifold": {
                                    "phase_deg_per_az_deg": 0.9,
                                    "phase_deg_bias": 10.0,
                                },
                                "diffuse": {"amp_ratio": 0.45, "paths_per_specular": 3},
                                "clutter": {"amp_abs": 5.0e-4, "paths_per_chirp": 6},
                            },
                        },
                    ]
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        tuning_root = root / "tuning_outputs"
        tuning_report_json = root / "tuning_report.json"
        lock_json = root / "comp_lock.json"
        proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/tune_radar_compensation_presets.py",
                "--profile-id",
                "single_target_ghost_comp_v1",
                "--scene-json-template",
                str(scene_template_json),
                "--reference-radar-map-npz",
                str(reference_radar_map),
                "--candidates-json",
                str(candidates_json),
                "--output-root",
                str(tuning_root),
                "--output-tuning-report-json",
                str(tuning_report_json),
                "--output-lock-json",
                str(lock_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Radar compensation preset tuning completed." in proc.stdout, proc.stdout
        report = json.loads(tuning_report_json.read_text(encoding="utf-8"))
        assert report["selected_candidate_name"] == "target_like"
        assert float(report["selected_score"]) <= 1.0e-12
        selected_cfg = dict(report["selected_compensation_config"])
        assert bool(selected_cfg.get("enabled", False)) is True
        assert int(selected_cfg.get("random_seed", -1)) == 20260320

        lock_payload = json.loads(lock_json.read_text(encoding="utf-8"))
        profiles = lock_payload.get("profiles", {})
        assert "single_target_ghost_comp_v1" in profiles
        lock_cfg = profiles["single_target_ghost_comp_v1"]["radar_compensation"]
        assert int(lock_cfg["random_seed"]) == 20260320

        # Golden-path consumption check: profile lock should override built-in defaults.
        golden_root = root / "golden"
        golden_summary = root / "golden_summary.json"
        golden = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_scene_backend_golden_path.py",
                "--backend",
                "analytic_targets",
                "--scene-equivalence-profile",
                "single_target_ghost_comp_v1",
                "--radar-compensation-lock-json",
                str(lock_json),
                "--n-chirps",
                "4",
                "--samples-per-chirp",
                "256",
                "--output-root",
                str(golden_root),
                "--output-summary-json",
                str(golden_summary),
                "--strict-nonexecuted",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scene backend golden-path run completed." in golden.stdout, golden.stdout
        golden_payload = json.loads(golden_summary.read_text(encoding="utf-8"))
        eqv = dict(golden_payload.get("equivalence_inputs", {}))
        assert eqv.get("radar_compensation_source") == "profile_lock_override"
        assert str(eqv.get("radar_compensation_lock_json", "")).endswith("comp_lock.json")

    print("validate_tune_radar_compensation_presets: pass")


def _build_template_scene() -> dict:
    return {
        "scene_id": "radar_comp_tune_template_v1",
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
                    "radial_velocity_mps": 0.5,
                    "az_deg": 9.0,
                    "el_deg": 0.0,
                    "amp": 1.0,
                    "range_amp_exponent": 2.0,
                    "material_tag": "ghost_panel",
                    "reflection_order": 2,
                    "path_id": "ghost_target",
                }
            ],
            "noise_sigma": 0.0,
            "radar_compensation": {
                "enabled": True,
                "random_seed": 20260320,
                "default_material_model": {
                    "reflectivity": 1.0,
                    "rcs_scale_linear": 1.0,
                    "reflection_decay": 1.0,
                    "wideband_slope_db_per_ghz": 0.0,
                },
                "material_models": {
                    "ghost_panel": {
                        "reflectivity": 0.82,
                        "rcs_scale_linear": 1.1,
                        "reflection_decay": 0.9,
                        "wideband_slope_db_per_ghz": -0.3,
                    }
                },
                "wideband": {"enabled": True, "phase_weight": 1.0},
                "manifold": {
                    "enabled": True,
                    "mag_db_bias": -0.1,
                    "mag_db_per_abs_az_deg": -0.003,
                    "mag_db_per_abs_el_deg": -0.001,
                    "phase_deg_bias": 2.0,
                    "phase_deg_per_az_deg": 0.2,
                    "phase_deg_per_el_deg": 0.08,
                    "phase_deg_per_reflection_order": 4.0,
                },
                "diffuse": {
                    "enabled": True,
                    "paths_per_specular": 1,
                    "amp_ratio": 0.15,
                    "delay_jitter_std": 0.01,
                    "doppler_sigma_hz": 2.0,
                    "direction_sigma_deg": 4.0,
                },
                "clutter": {
                    "enabled": True,
                    "paths_per_chirp": 2,
                    "range_min_m": 4.0,
                    "range_max_m": 30.0,
                    "az_min_deg": -30.0,
                    "az_max_deg": 30.0,
                    "el_mean_deg": 0.0,
                    "el_sigma_deg": 1.5,
                    "doppler_sigma_hz": 15.0,
                    "amp_abs": 1.2e-4,
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
            "samples_per_chirp": 256,
        },
        "map_config": {
            "nfft_range": 256,
            "nfft_doppler": 32,
            "nfft_angle": 16,
            "range_bin_limit": 96,
        },
    }


def _target_patch() -> dict:
    return {
        "material_models": {
            "ghost_panel": {
                "reflectivity": 0.9,
                "rcs_scale_linear": 1.35,
                "reflection_decay": 0.95,
                "wideband_slope_db_per_ghz": -0.55,
            }
        },
        "manifold": {
            "mag_db_bias": -0.2,
            "mag_db_per_abs_az_deg": -0.0045,
            "phase_deg_bias": 3.5,
            "phase_deg_per_az_deg": 0.28,
        },
        "diffuse": {"paths_per_specular": 2, "amp_ratio": 0.22, "direction_sigma_deg": 3.2},
        "clutter": {"paths_per_chirp": 1, "amp_abs": 9.0e-5},
    }


def _deep_merge(base: dict, patch: dict) -> dict:
    out = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


if __name__ == "__main__":
    run()

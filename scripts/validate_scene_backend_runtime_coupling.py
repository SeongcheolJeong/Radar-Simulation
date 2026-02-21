#!/usr/bin/env python3
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json

C0 = 299_792_458.0


def _write_runtime_provider_fixture(root: Path) -> str:
    module_path = root / "runtime_provider_fixture.py"
    module_path.write_text(
        """
import math

C0 = 299_792_458.0


def sionna_provider(context):
    n = int(context["n_chirps"])
    inp = dict(context.get("runtime_input") or {})
    rng = float(inp.get("range_m", 25.0))
    az_deg = float(inp.get("az_deg", 0.0))
    el_deg = float(inp.get("el_deg", 0.0))
    amp = float(inp.get("amp", 1.0 / (rng * rng)))
    az = math.radians(az_deg)
    el = math.radians(el_deg)
    u = [
        math.cos(el) * math.cos(az),
        math.cos(el) * math.sin(az),
        math.sin(el),
    ]
    delay = 2.0 * rng / C0
    out = []
    for k in range(n):
        out.append([
            {
                "delay_s": delay,
                "doppler_hz": 0.0,
                "unit_direction": u,
                "amp": amp,
                "path_id": f"runtime_sionna_{k}",
                "material_tag": "runtime_sionna",
                "reflection_order": 1,
            }
        ])
    return {"paths_by_chirp": out}


def po_sbr_provider(context):
    n = int(context["n_chirps"])
    inp = dict(context.get("runtime_input") or {})
    rng = float(inp.get("range_m", 23.0))
    amp = float(inp.get("amp", 1.0 / (rng * rng)))
    delay = 2.0 * rng / C0
    paths = []
    for k in range(n):
        paths.append(
            {
                "chirp_index": int(k),
                "delay_s": delay,
                "doppler_hz": 0.0,
                "unit_direction": [1.0, 0.0, 0.0],
                "amp": amp,
                "path_id": f"runtime_po_{k}",
                "material_tag": "runtime_po",
                "reflection_order": 1,
            }
        )
    return {"paths": paths}


def failing_provider(context):
    raise RuntimeError("intentional runtime provider failure")
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return "runtime_provider_fixture"


def _write_scene(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _base_radar() -> dict:
    return {
        "fc_hz": 77e9,
        "slope_hz_per_s": 20e12,
        "fs_hz": 20e6,
        "samples_per_chirp": 512,
    }


def _base_tx_rx() -> tuple:
    tx = [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]]
    rx = [
        [0.0, 0.00185, 0.0],
        [0.0, 0.0037, 0.0],
        [0.0, 0.00555, 0.0],
        [0.0, 0.0074, 0.0],
    ]
    return tx, rx


def _load_runtime_resolution(radar_map_npz: Path) -> dict:
    payload = np.load(str(radar_map_npz), allow_pickle=False)
    meta = json.loads(str(payload["metadata_json"]))
    info = meta.get("runtime_resolution")
    if not isinstance(info, dict):
        raise AssertionError("runtime_resolution metadata missing")
    return info


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_scene_runtime_coupling_") as td:
        root = Path(td)
        fixture_module = _write_runtime_provider_fixture(root)
        sys.path.insert(0, str(root))
        try:
            tx_pos, rx_pos = _base_tx_rx()

            # Case 1: Sionna runtime provider direct path
            s1 = _write_scene(
                root / "scene_sionna_runtime.json",
                {
                    "scene_id": "sionna_runtime_case",
                    "backend": {
                        "type": "sionna_rt",
                        "n_chirps": 3,
                        "tx_pos_m": tx_pos,
                        "rx_pos_m": rx_pos,
                        "runtime_provider": f"{fixture_module}:sionna_provider",
                        "runtime_required_modules": [],
                        "runtime_input": {"range_m": 25.0},
                        "noise_sigma": 0.0,
                    },
                    "radar": _base_radar(),
                    "map_config": {"nfft_range": 512, "range_bin_limit": 64},
                },
            )
            o1 = root / "out_sionna_runtime"
            run_object_scene_to_radar_map_json(str(s1), str(o1), run_hybrid_estimation=False)
            p1 = json.loads((o1 / "path_list.json").read_text(encoding="utf-8"))
            assert p1[0][0]["path_id"] == "runtime_sionna_0"
            r1 = _load_runtime_resolution(o1 / "radar_map.npz")
            assert r1["mode"] == "runtime_provider"

            # Case 2: PO-SBR runtime provider direct path
            s2 = _write_scene(
                root / "scene_po_runtime.json",
                {
                    "scene_id": "po_runtime_case",
                    "backend": {
                        "type": "po_sbr_rt",
                        "n_chirps": 3,
                        "tx_pos_m": tx_pos,
                        "rx_pos_m": rx_pos,
                        "runtime_provider": f"{fixture_module}:po_sbr_provider",
                        "runtime_required_modules": [],
                        "runtime_input": {"range_m": 23.0},
                        "noise_sigma": 0.0,
                    },
                    "radar": _base_radar(),
                    "map_config": {"nfft_range": 512, "range_bin_limit": 64},
                },
            )
            o2 = root / "out_po_runtime"
            run_object_scene_to_radar_map_json(str(s2), str(o2), run_hybrid_estimation=False)
            p2 = json.loads((o2 / "path_list.json").read_text(encoding="utf-8"))
            assert p2[0][0]["path_id"] == "runtime_po_0"
            r2 = _load_runtime_resolution(o2 / "radar_map.npz")
            assert r2["mode"] == "runtime_provider"

            # Case 3: runtime failure with static fallback
            static_paths = {
                "paths_by_chirp": [
                    [
                        {
                            "delay_s": 2.0 * 21.0 / C0,
                            "doppler_hz": 0.0,
                            "unit_direction": [1.0, 0.0, 0.0],
                            "amp": 1.0 / (21.0 * 21.0),
                            "path_id": "static_fallback_0",
                            "material_tag": "fallback",
                            "reflection_order": 1,
                        }
                    ],
                    [
                        {
                            "delay_s": 2.0 * 21.0 / C0,
                            "doppler_hz": 0.0,
                            "unit_direction": [1.0, 0.0, 0.0],
                            "amp": 1.0 / (21.0 * 21.0),
                            "path_id": "static_fallback_1",
                            "material_tag": "fallback",
                            "reflection_order": 1,
                        }
                    ],
                    [
                        {
                            "delay_s": 2.0 * 21.0 / C0,
                            "doppler_hz": 0.0,
                            "unit_direction": [1.0, 0.0, 0.0],
                            "amp": 1.0 / (21.0 * 21.0),
                            "path_id": "static_fallback_2",
                            "material_tag": "fallback",
                            "reflection_order": 1,
                        }
                    ],
                ]
            }
            s3 = _write_scene(
                root / "scene_sionna_fallback.json",
                {
                    "scene_id": "sionna_runtime_fallback_case",
                    "backend": {
                        "type": "sionna_rt",
                        "n_chirps": 3,
                        "tx_pos_m": tx_pos,
                        "rx_pos_m": rx_pos,
                        "runtime_provider": f"{fixture_module}:failing_provider",
                        "runtime_required_modules": [],
                        "runtime_failure_policy": "use_static",
                        "paths_payload": static_paths,
                        "noise_sigma": 0.0,
                    },
                    "radar": _base_radar(),
                    "map_config": {"nfft_range": 512, "range_bin_limit": 64},
                },
            )
            o3 = root / "out_sionna_fallback"
            run_object_scene_to_radar_map_json(str(s3), str(o3), run_hybrid_estimation=False)
            p3 = json.loads((o3 / "path_list.json").read_text(encoding="utf-8"))
            assert p3[0][0]["path_id"] == "static_fallback_0"
            r3 = _load_runtime_resolution(o3 / "radar_map.npz")
            assert r3["mode"] == "runtime_failed_fallback_static"
            assert "intentional runtime provider failure" in str(r3.get("runtime_error", ""))

            # Case 4: runtime missing-module failure with static fallback
            s4 = _write_scene(
                root / "scene_sionna_missing_module_fallback.json",
                {
                    "scene_id": "sionna_runtime_missing_module_case",
                    "backend": {
                        "type": "sionna_rt",
                        "n_chirps": 3,
                        "tx_pos_m": tx_pos,
                        "rx_pos_m": rx_pos,
                        "runtime_provider": f"{fixture_module}:sionna_provider",
                        "runtime_required_modules": ["definitely_missing_runtime_module_abc"],
                        "runtime_failure_policy": "use_static",
                        "paths_payload": static_paths,
                        "noise_sigma": 0.0,
                    },
                    "radar": _base_radar(),
                    "map_config": {"nfft_range": 512, "range_bin_limit": 64},
                },
            )
            o4 = root / "out_sionna_missing_module_fallback"
            run_object_scene_to_radar_map_json(str(s4), str(o4), run_hybrid_estimation=False)
            p4 = json.loads((o4 / "path_list.json").read_text(encoding="utf-8"))
            assert p4[0][0]["path_id"] == "static_fallback_0"
            r4 = _load_runtime_resolution(o4 / "radar_map.npz")
            assert r4["mode"] == "runtime_failed_fallback_static"
            assert "required runtime modules unavailable" in str(r4.get("runtime_error", ""))

            # Case 5: runtime failure without fallback must raise
            s5 = _write_scene(
                root / "scene_sionna_runtime_fail_strict.json",
                {
                    "scene_id": "sionna_runtime_fail_strict_case",
                    "backend": {
                        "type": "sionna_rt",
                        "n_chirps": 3,
                        "tx_pos_m": tx_pos,
                        "rx_pos_m": rx_pos,
                        "runtime_provider": f"{fixture_module}:failing_provider",
                        "runtime_required_modules": [],
                        "runtime_failure_policy": "error",
                        "noise_sigma": 0.0,
                    },
                    "radar": _base_radar(),
                    "map_config": {"nfft_range": 512, "range_bin_limit": 64},
                },
            )
            o5 = root / "out_sionna_runtime_fail_strict"
            try:
                run_object_scene_to_radar_map_json(str(s5), str(o5), run_hybrid_estimation=False)
                raise AssertionError("expected strict runtime provider failure")
            except ValueError as exc:
                assert "runtime provider failed" in str(exc)
        finally:
            try:
                sys.path.remove(str(root))
            except ValueError:
                pass

    print("validate_scene_backend_runtime_coupling: pass")


if __name__ == "__main__":
    run()

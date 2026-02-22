#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path
from typing import Any, Tuple

import numpy as np

from avxsim.constants import C0
from avxsim.runtime_providers import po_sbr_rt_provider as provider
from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


class _FakePOSolver:
    def build(self, filename: str) -> Tuple[Any, Any]:
        return [[0.0, 0.0, 0.0]], [[0, 0, 0]]

    def simulate(
        self,
        alpha_deg: float,
        phi_deg: float,
        theta_deg: float,
        freq_hz: float,
        rays_per_lambda: float,
        v: Any,
        f: Any,
        bounces: int,
    ) -> Tuple[complex, complex, float]:
        # deterministic mock: fixed equivalent range and chirp-invariant fields
        return complex(1.0, 0.25), complex(-0.25, 0.5), 15.0


def _load_runtime_resolution(radar_map_npz: Path) -> dict:
    payload = np.load(str(radar_map_npz), allow_pickle=False)
    metadata = json.loads(str(payload["metadata_json"]))
    info = metadata.get("runtime_resolution")
    if not isinstance(info, dict):
        raise AssertionError("runtime_resolution metadata missing")
    return info


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_po_sbr_runtime_provider_integration_") as td:
        root = Path(td)
        geom = root / "geometries" / "plate.obj"
        geom.parent.mkdir(parents=True, exist_ok=True)
        geom.write_text("# placeholder geometry\n", encoding="utf-8")

        scene_json = root / "scene_po_sbr_runtime_provider.json"
        scene_json.write_text(
            json.dumps(
                {
                    "scene_id": "po_sbr_runtime_provider_integration_case",
                    "backend": {
                        "type": "po_sbr_rt",
                        "n_chirps": 4,
                        "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                        "rx_pos_m": [
                            [0.0, 0.00185, 0.0],
                            [0.0, 0.0037, 0.0],
                            [0.0, 0.00555, 0.0],
                            [0.0, 0.0074, 0.0],
                        ],
                        "runtime_provider": "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr",
                        "runtime_required_modules": [],
                        "runtime_failure_policy": "error",
                        "runtime_input": {
                            "po_sbr_repo_root": str(root),
                            "geometry_path": "geometries/plate.obj",
                            "alpha_deg": 180.0,
                            "phi_deg": 90.0,
                            "theta_deg": 90.0,
                            "freq_hz": 77e9,
                            "rays_per_lambda": 3.0,
                            "bounces": 2,
                            "radial_velocity_mps": 0.0,
                            "material_tag": "stubbed_po_sbr",
                        },
                        "noise_sigma": 0.0,
                    },
                    "radar": {
                        "fc_hz": 77e9,
                        "slope_hz_per_s": 20e12,
                        "fs_hz": 20e6,
                        "samples_per_chirp": 512,
                    },
                    "map_config": {"nfft_range": 512, "range_bin_limit": 64},
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        fake_solver = _FakePOSolver()
        old_assert = provider._assert_po_sbr_runtime_prereqs
        old_loader = provider._load_po_solver_module
        try:
            provider._assert_po_sbr_runtime_prereqs = lambda: None
            provider._load_po_solver_module = lambda repo_root: fake_solver
            out_dir = root / "outputs"
            result = run_object_scene_to_radar_map_json(
                scene_json_path=str(scene_json),
                output_dir=str(out_dir),
                run_hybrid_estimation=False,
            )
        finally:
            provider._assert_po_sbr_runtime_prereqs = old_assert
            provider._load_po_solver_module = old_loader

        path_payload = json.loads(Path(result["path_list_json"]).read_text(encoding="utf-8"))
        assert isinstance(path_payload, list) and len(path_payload) == 4
        expected_delay = float(2.0 * 15.0 / C0)
        for chirp_idx, chirp_paths in enumerate(path_payload):
            assert isinstance(chirp_paths, list) and len(chirp_paths) == 1
            path = chirp_paths[0]
            assert path["path_id"] == f"po_sbr_runtime_c{chirp_idx:04d}"
            assert path["material_tag"] == "stubbed_po_sbr"
            assert abs(float(path["delay_s"]) - expected_delay) < 1.0e-12

        runtime_resolution = _load_runtime_resolution(Path(result["radar_map_npz"]))
        assert runtime_resolution["mode"] == "runtime_provider"
        assert str(runtime_resolution.get("runtime_provider", "")).endswith(
            "generate_po_sbr_like_paths_from_posbr"
        )
        runtime_info = runtime_resolution.get("runtime_info")
        assert isinstance(runtime_info, dict)
        assert runtime_info.get("provider_spec") == (
            "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr"
        )

    print("validate_scene_runtime_po_sbr_provider_integration_stubbed: pass")


if __name__ == "__main__":
    run()

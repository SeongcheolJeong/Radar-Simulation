#!/usr/bin/env python3
import math
import tempfile
from pathlib import Path
from typing import Any, Tuple

from avxsim.constants import C0
from avxsim.runtime_providers import po_sbr_rt_provider as provider


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
        phase = math.radians(float(phi_deg))
        e_theta = complex(math.cos(phase), math.sin(phase))
        e_phi = complex(0.5, -0.25)
        r0 = 12.0
        return e_theta, e_phi, r0


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_po_sbr_runtime_provider_") as td:
        root = Path(td)
        geom = root / "geometries" / "plate.obj"
        geom.parent.mkdir(parents=True, exist_ok=True)
        geom.write_text("# placeholder geometry\n", encoding="utf-8")

        fake_solver = _FakePOSolver()
        old_assert = provider._assert_po_sbr_runtime_prereqs
        old_igl_compat = provider._apply_igl_compat
        old_loader = provider._load_po_solver_module
        try:
            provider._assert_po_sbr_runtime_prereqs = lambda: None
            provider._apply_igl_compat = lambda: None
            provider._load_po_solver_module = lambda repo_root: fake_solver

            fc_hz = 77e9
            radial_velocity_mps = 3.0
            payload = provider.generate_po_sbr_like_paths_from_posbr(
                {
                    "n_chirps": 4,
                    "fc_hz": fc_hz,
                    "runtime_input": {
                        "po_sbr_repo_root": str(root),
                        "geometry_path": "geometries/plate.obj",
                        "alpha_deg": 180.0,
                        "phi_deg": 90.0,
                        "theta_deg": 90.0,
                        "phi_rate_deg_per_s": 100.0,
                        "chirp_interval_s": 1.0e-3,
                        "freq_hz": fc_hz,
                        "rays_per_lambda": 3.0,
                        "bounces": 2,
                        "radial_velocity_mps": radial_velocity_mps,
                        "material_tag": "stubbed_po_sbr",
                    },
                }
            )
            floor_payload = provider.generate_po_sbr_like_paths_from_posbr(
                {
                    "n_chirps": 1,
                    "fc_hz": fc_hz,
                    "runtime_input": {
                        "po_sbr_repo_root": str(root),
                        "geometry_path": "geometries/plate.obj",
                        "alpha_deg": 180.0,
                        "phi_deg": 0.0,
                        "theta_deg": 90.0,
                        "freq_hz": fc_hz,
                        "rays_per_lambda": 3.0,
                        "bounces": 1,
                        "radial_velocity_mps": 0.0,
                        "amp_scale": 0.0,
                        "amp_floor_abs": 0.01,
                    },
                }
            )
            target_payload = provider.generate_po_sbr_like_paths_from_posbr(
                {
                    "n_chirps": 1,
                    "fc_hz": fc_hz,
                    "runtime_input": {
                        "po_sbr_repo_root": str(root),
                        "geometry_path": "geometries/plate.obj",
                        "alpha_deg": 180.0,
                        "phi_deg": 0.0,
                        "theta_deg": 90.0,
                        "freq_hz": fc_hz,
                        "rays_per_lambda": 3.0,
                        "bounces": 1,
                        "radial_velocity_mps": 0.0,
                        "amp_scale": 0.0,
                        "amp_target_abs": 0.02,
                    },
                }
            )
            multi_component_payload = provider.generate_po_sbr_like_paths_from_posbr(
                {
                    "n_chirps": 2,
                    "fc_hz": fc_hz,
                    "runtime_input": {
                        "po_sbr_repo_root": str(root),
                        "geometry_path": "geometries/plate.obj",
                        "components": [
                            {
                                "alpha_deg": 180.0,
                                "phi_deg": 0.0,
                                "theta_deg": 90.0,
                                "freq_hz": fc_hz,
                                "rays_per_lambda": 3.0,
                                "bounces": 1,
                                "radial_velocity_mps": 1.5,
                                "min_range_m": 12.0,
                                "amp_target_abs": 0.03,
                                "material_tag": "comp0",
                                "path_id_prefix": "po_comp0",
                            },
                            {
                                "alpha_deg": 180.0,
                                "phi_deg": 45.0,
                                "theta_deg": 90.0,
                                "freq_hz": fc_hz,
                                "rays_per_lambda": 2.5,
                                "bounces": 1,
                                "radial_velocity_mps": -2.0,
                                "min_range_m": 12.0,
                                "amp_floor_abs": 0.02,
                                "material_tag": "comp1",
                                "path_id_prefix": "po_comp1",
                            },
                        ],
                    },
                }
            )
        finally:
            provider._assert_po_sbr_runtime_prereqs = old_assert
            provider._apply_igl_compat = old_igl_compat
            provider._load_po_solver_module = old_loader

        paths_by_chirp = payload.get("paths_by_chirp")
        assert isinstance(paths_by_chirp, list)
        assert len(paths_by_chirp) == 4
        expected_delay = float(2.0 * 12.0 / C0)
        expected_fd = float(2.0 * radial_velocity_mps / (C0 / fc_hz))
        for chirp_idx, chirp_paths in enumerate(paths_by_chirp):
            assert isinstance(chirp_paths, list) and len(chirp_paths) == 1
            path = chirp_paths[0]
            assert path["path_id"] == f"po_sbr_runtime_c{chirp_idx:04d}"
            assert path["material_tag"] == "stubbed_po_sbr"
            assert abs(float(path["delay_s"]) - expected_delay) < 1.0e-12
            assert abs(float(path["doppler_hz"]) - expected_fd) < 1.0e-9
            amp = path["amp_complex"]
            assert isinstance(amp, dict)
            assert all(k in amp for k in ("re", "im"))

        floor_paths = floor_payload.get("paths_by_chirp")
        assert isinstance(floor_paths, list) and len(floor_paths) == 1
        floor_amp = floor_paths[0][0]["amp_complex"]
        assert abs(float(floor_amp["re"]) - 0.01) < 1.0e-12
        assert abs(float(floor_amp["im"])) < 1.0e-12

        target_paths = target_payload.get("paths_by_chirp")
        assert isinstance(target_paths, list) and len(target_paths) == 1
        target_amp = target_paths[0][0]["amp_complex"]
        target_mag = math.sqrt(float(target_amp["re"]) ** 2 + float(target_amp["im"]) ** 2)
        assert abs(target_mag - 0.02) < 1.0e-12

        mc_paths = multi_component_payload.get("paths_by_chirp")
        assert isinstance(mc_paths, list) and len(mc_paths) == 2
        for chirp_idx, chirp_paths in enumerate(mc_paths):
            assert isinstance(chirp_paths, list) and len(chirp_paths) == 2
            path0 = chirp_paths[0]
            path1 = chirp_paths[1]
            assert path0["path_id"] == f"po_comp0_c{chirp_idx:04d}_p00"
            assert path1["path_id"] == f"po_comp1_c{chirp_idx:04d}_p01"
            assert path0["material_tag"] == "comp0"
            assert path1["material_tag"] == "comp1"
            amp0 = path0["amp_complex"]
            amp1 = path1["amp_complex"]
            mag0 = math.sqrt(float(amp0["re"]) ** 2 + float(amp0["im"]) ** 2)
            mag1 = math.sqrt(float(amp1["re"]) ** 2 + float(amp1["im"]) ** 2)
            assert abs(mag0 - 0.03) < 1.0e-12
            assert mag1 >= 0.02 - 1.0e-12

    print("validate_po_sbr_runtime_provider_stubbed: pass")


if __name__ == "__main__":
    run()

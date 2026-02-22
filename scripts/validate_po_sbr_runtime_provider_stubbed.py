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
        old_loader = provider._load_po_solver_module
        try:
            provider._assert_po_sbr_runtime_prereqs = lambda: None
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
        finally:
            provider._assert_po_sbr_runtime_prereqs = old_assert
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

    print("validate_po_sbr_runtime_provider_stubbed: pass")


if __name__ == "__main__":
    run()

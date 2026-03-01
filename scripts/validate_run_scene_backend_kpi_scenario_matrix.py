#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _write_runtime_fixture(module_path: Path) -> str:
    module_path.write_text(
        """
import math

C0 = 299_792_458.0


def _dir_from_phi_theta(phi_deg, theta_deg):
    phi = math.radians(float(phi_deg))
    theta = math.radians(float(theta_deg))
    return [
        math.sin(theta) * math.cos(phi),
        math.sin(theta) * math.sin(phi),
        math.cos(theta),
    ]


def sionna_provider(context):
    n = int(context.get("n_chirps", 1))
    backend = dict(context.get("backend") or {})
    runtime_input = dict(backend.get("runtime_input") or {})
    spheres = list(runtime_input.get("spheres") or [])
    sphere = dict(spheres[0])

    center = [float(x) for x in sphere.get("center_m", [25.5, 0.0, 0.0])]
    radius = float(sphere.get("radius_m", 0.5))
    c_norm = math.sqrt(sum(x * x for x in center))
    if c_norm <= 0.0:
        direction = [1.0, 0.0, 0.0]
    else:
        direction = [x / c_norm for x in center]
    one_way_range = max(c_norm - radius, 1.0e-6)

    velocity = [float(x) for x in sphere.get("velocity_mps", [0.0, 0.0, 0.0])]
    radial_v = sum(direction[i] * velocity[i] for i in range(3))

    fc_hz = float(context.get("fc_hz", 77e9))
    lam = C0 / fc_hz
    fd = 2.0 * radial_v / lam
    delay = 2.0 * one_way_range / C0
    amp = 1.0 / (one_way_range * one_way_range)

    out = []
    for k in range(n):
        out.append(
            [
                {
                    "delay_s": delay,
                    "doppler_hz": fd,
                    "unit_direction": direction,
                    "amp": amp,
                    "path_id": f"fixture_sionna_{k}",
                    "material_tag": "fixture",
                    "reflection_order": 1,
                }
            ]
        )
    return {"paths_by_chirp": out}


def po_provider(context):
    n = int(context.get("n_chirps", 1))
    backend = dict(context.get("backend") or {})
    runtime_input = dict(backend.get("runtime_input") or {})

    one_way_range = float(runtime_input.get("min_range_m", 25.0))
    direction = _dir_from_phi_theta(
        runtime_input.get("phi_deg", 0.0),
        runtime_input.get("theta_deg", 90.0),
    )
    radial_v = float(runtime_input.get("radial_velocity_mps", 0.0))

    fc_hz = float(context.get("fc_hz", 77e9))
    lam = C0 / fc_hz
    fd = 2.0 * radial_v / lam
    delay = 2.0 * one_way_range / C0
    amp = float(runtime_input.get("amp_floor_abs", 1.0 / (one_way_range * one_way_range)))

    out = []
    for k in range(n):
        out.append(
            {
                "chirp_index": int(k),
                "delay_s": delay,
                "doppler_hz": fd,
                "unit_direction": direction,
                "amp": amp,
                "path_id": f"fixture_po_{k}",
                "material_tag": "fixture",
                "reflection_order": 1,
            }
        )
    return {"paths": out}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return module_path.stem


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="validate_scene_backend_kpi_scenario_matrix_") as td:
        root = Path(td)
        fixture_module = _write_runtime_fixture(root / "scenario_matrix_runtime_fixture.py")

        out_root = root / "matrix_run"
        out_summary = root / "matrix_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(root), str(repo_root / "src")])

        run_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_scene_backend_kpi_scenario_matrix.py",
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_summary),
                "--strict-all-ready",
                "--sionna-runtime-provider",
                f"{fixture_module}:sionna_provider",
                "--sionna-runtime-required-modules",
                "",
                "--po-sbr-runtime-provider",
                f"{fixture_module}:po_provider",
                "--po-sbr-runtime-required-modules",
                "",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if run_proc.returncode != 0:
            raise AssertionError(
                "scenario matrix run failed\n"
                f"stdout:\n{run_proc.stdout}\n"
                f"stderr:\n{run_proc.stderr}\n"
            )
        assert "Scene backend KPI scenario matrix completed." in run_proc.stdout, run_proc.stdout

        validate_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/validate_scene_backend_kpi_scenario_matrix_report.py",
                "--summary-json",
                str(out_summary),
                "--require-ready",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "validate_scene_backend_kpi_scenario_matrix_report: pass" in validate_proc.stdout, validate_proc.stdout

        payload = json.loads(out_summary.read_text(encoding="utf-8"))
        assert payload.get("matrix_status") == "ready"
        summary = dict(payload.get("summary") or {})
        assert int(summary.get("profile_count", -1)) >= 3
        assert int(summary.get("gate_profile_count", -1)) >= 1
        assert int(summary.get("gate_blocked_profile_count", -1)) == 0
        assert int(summary.get("failed_profile_count", -1)) == 0

    print("validate_run_scene_backend_kpi_scenario_matrix: pass")


if __name__ == "__main__":
    run()

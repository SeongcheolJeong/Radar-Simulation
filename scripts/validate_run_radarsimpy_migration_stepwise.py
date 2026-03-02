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


def _parse_complex(value):
    if isinstance(value, dict):
        return complex(float(value.get("re", 0.0)), float(value.get("im", 0.0)))
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return complex(float(value[0]), float(value[1]))
    return complex(float(value), 0.0)


def _chirp_interval_s(context):
    backend = dict(context.get("backend") or {})
    runtime_input = dict(backend.get("runtime_input") or {})
    if "chirp_interval_s" in runtime_input:
        return float(runtime_input["chirp_interval_s"])
    radar = dict(context.get("radar") or {})
    samples = int(radar.get("samples_per_chirp", 1024))
    fs_hz = float(radar.get("fs_hz", 20e6))
    return float(samples) / float(fs_hz)


def _dir_from_az_el(az_deg, el_deg):
    az = math.radians(float(az_deg))
    el = math.radians(float(el_deg))
    return [
        math.cos(el) * math.cos(az),
        math.cos(el) * math.sin(az),
        math.sin(el),
    ]


def _dir_from_phi_theta(phi_deg, theta_deg):
    phi = math.radians(float(phi_deg))
    theta = math.radians(float(theta_deg))
    return [
        math.sin(theta) * math.cos(phi),
        math.sin(theta) * math.sin(phi),
        math.cos(theta),
    ]


def _paths_from_targets(targets, n_chirps, fc_hz, chirp_interval_s):
    lam = C0 / float(fc_hz)
    out = []
    for chirp_idx in range(int(n_chirps)):
        t = float(chirp_idx) * float(chirp_interval_s)
        chirp_paths = []
        for target_idx, target in enumerate(targets):
            range_m = max(1.0e-6, float(target["range_m"]) + float(target["radial_velocity_mps"]) * t)
            u = _dir_from_az_el(float(target["az_deg"]), float(target["el_deg"]))
            amp0 = _parse_complex(target.get("amp_scale", 1.0))
            range_exp = max(float(target.get("range_amp_exponent", 2.0)), 0.0)
            amp = amp0 / (range_m ** range_exp)
            chirp_paths.append(
                {
                    "delay_s": 2.0 * range_m / C0,
                    "doppler_hz": 2.0 * float(target["radial_velocity_mps"]) / lam,
                    "unit_direction": [float(u[0]), float(u[1]), float(u[2])],
                    "amp_complex": {"re": float(amp.real), "im": float(amp.imag)},
                    "path_id": str(target.get("path_id_prefix", f"fixture_t{target_idx}")) + f"_c{chirp_idx:04d}",
                    "material_tag": str(target.get("material_tag", "fixture")),
                    "reflection_order": int(target.get("reflection_order", 1)),
                }
            )
        out.append(chirp_paths)
    return out


def radarsimpy_provider(context):
    n_chirps = int(context.get("n_chirps", 1))
    fc_hz = float(context.get("fc_hz", 77e9))
    backend = dict(context.get("backend") or {})
    runtime_input = dict(backend.get("runtime_input") or {})

    targets = list(runtime_input.get("targets") or [])
    if len(targets) == 0:
        targets = [
            {
                "range_m": 25.0,
                "az_deg": 0.0,
                "el_deg": 0.0,
                "radial_velocity_mps": 0.0,
                "amp_scale": 1.0,
                "range_amp_exponent": 2.0,
                "material_tag": "fixture",
                "reflection_order": 1,
                "path_id_prefix": "fixture_radarsimpy",
            }
        ]

    return {
        "paths_by_chirp": _paths_from_targets(
            targets=targets,
            n_chirps=n_chirps,
            fc_hz=fc_hz,
            chirp_interval_s=_chirp_interval_s(context),
        )
    }


def sionna_provider(context):
    n_chirps = int(context.get("n_chirps", 1))
    fc_hz = float(context.get("fc_hz", 77e9))
    backend = dict(context.get("backend") or {})
    runtime_input = dict(backend.get("runtime_input") or {})

    targets = []
    for idx, sphere in enumerate(list(runtime_input.get("spheres") or [])):
        center = [float(x) for x in sphere.get("center_m", [25.0, 0.0, 0.0])]
        norm = math.sqrt((center[0] ** 2) + (center[1] ** 2) + (center[2] ** 2))
        radius = max(float(sphere.get("radius_m", 0.0)), 0.0)
        if norm <= 0.0:
            u = [1.0, 0.0, 0.0]
            range_m = 25.0
        else:
            u = [center[0] / norm, center[1] / norm, center[2] / norm]
            range_m = max(norm - radius, 1.0e-6)

        velocity = [float(x) for x in sphere.get("velocity_mps", [0.0, 0.0, 0.0])]
        radial_v = float((u[0] * velocity[0]) + (u[1] * velocity[1]) + (u[2] * velocity[2]))
        targets.append(
            {
                "range_m": float(range_m),
                "az_deg": math.degrees(math.atan2(u[1], u[0])),
                "el_deg": math.degrees(math.asin(max(-1.0, min(1.0, u[2])))),
                "radial_velocity_mps": radial_v,
                "amp_scale": sphere.get("amp", 1.0),
                "range_amp_exponent": float(sphere.get("range_amp_exponent", 2.0)),
                "material_tag": str(sphere.get("material_tag", "fixture")),
                "reflection_order": int(sphere.get("reflection_order", 1)),
                "path_id_prefix": str(sphere.get("path_id_prefix", f"fixture_sionna_{idx}")),
            }
        )

    if len(targets) == 0:
        targets = [
            {
                "range_m": 25.0,
                "az_deg": 0.0,
                "el_deg": 0.0,
                "radial_velocity_mps": 0.0,
                "amp_scale": 1.0,
                "range_amp_exponent": 2.0,
                "material_tag": "fixture",
                "reflection_order": 1,
                "path_id_prefix": "fixture_sionna",
            }
        ]

    return {
        "paths_by_chirp": _paths_from_targets(
            targets=targets,
            n_chirps=n_chirps,
            fc_hz=fc_hz,
            chirp_interval_s=_chirp_interval_s(context),
        )
    }


def po_provider(context):
    n_chirps = int(context.get("n_chirps", 1))
    fc_hz = float(context.get("fc_hz", 77e9))
    backend = dict(context.get("backend") or {})
    runtime_input = dict(backend.get("runtime_input") or {})
    components = list(runtime_input.get("components") or [])

    lam = C0 / float(fc_hz)
    chirp_interval_s = _chirp_interval_s(context)
    out = []
    for chirp_idx in range(int(n_chirps)):
        t = float(chirp_idx) * float(chirp_interval_s)
        chirp_paths = []
        for idx, comp in enumerate(components):
            phi_deg = float(comp.get("phi_deg", 0.0))
            theta_deg = float(comp.get("theta_deg", 90.0))
            u = _dir_from_phi_theta(phi_deg=phi_deg, theta_deg=theta_deg)
            az_deg = math.degrees(math.atan2(u[1], u[0]))
            el_deg = math.degrees(math.asin(max(-1.0, min(1.0, u[2]))))

            # Intentionally biased range for failure-path validation.
            base_range = float(comp.get("min_range_m", 25.0)) + 6.0
            rv = float(comp.get("radial_velocity_mps", 0.0))
            range_m = max(1.0e-6, base_range + rv * t)
            amp = float(comp.get("amp_target_abs", 1.0 / (base_range * base_range)))

            chirp_paths.append(
                {
                    "delay_s": 2.0 * range_m / C0,
                    "doppler_hz": 2.0 * rv / lam,
                    "unit_direction": _dir_from_az_el(az_deg=az_deg, el_deg=el_deg),
                    "amp": amp,
                    "path_id": str(comp.get("path_id_prefix", f"fixture_po_{idx}")) + f"_c{chirp_idx:04d}",
                    "material_tag": str(comp.get("material_tag", "fixture")),
                    "reflection_order": int(comp.get("reflection_order", 1)),
                }
            )
        out.append(chirp_paths)

    if len(out) == 0:
        out = [[] for _ in range(int(n_chirps))]
    return {"paths_by_chirp": out}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return module_path.stem


def _run_cmd(cmd, cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _pick_python_bin(repo_root: Path) -> str:
    venv_python = repo_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return str(Path(sys.executable))


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    python_bin = _pick_python_bin(repo_root=repo_root)
    with tempfile.TemporaryDirectory(prefix="validate_radarsimpy_migration_stepwise_") as td:
        root = Path(td)
        fixture_module = _write_runtime_fixture(root / "migration_runtime_fixture.py")

        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(root), str(repo_root / "src")])

        # Case 1: ready path (analytic + sionna both match radarsimpy reference)
        run1_root = root / "run1"
        run1_summary = run1_root / "summary.json"
        run1_cmd = [
            python_bin,
            "scripts/run_radarsimpy_migration_stepwise.py",
            "--output-root",
            str(run1_root / "outputs"),
            "--output-summary-json",
            str(run1_summary),
            "--candidate-backend",
            "analytic_targets,sionna_rt",
            "--radarsimpy-runtime-provider",
            f"{fixture_module}:radarsimpy_provider",
            "--radarsimpy-runtime-required-modules",
            "",
            "--sionna-runtime-provider",
            f"{fixture_module}:sionna_provider",
            "--sionna-runtime-required-modules",
            "",
            "--require-runtime-provider-mode",
        ]
        proc1 = _run_cmd(run1_cmd, cwd=repo_root, env=env)
        if proc1.returncode != 0:
            raise AssertionError(
                "run1 failed\n"
                f"stdout:\n{proc1.stdout}\n"
                f"stderr:\n{proc1.stderr}\n"
            )
        assert "RadarSimPy migration stepwise run completed." in proc1.stdout, proc1.stdout

        payload1 = json.loads(run1_summary.read_text(encoding="utf-8"))
        assert payload1.get("migration_status") == "ready"
        summary1 = dict(payload1.get("summary") or {})
        assert int(summary1.get("candidate_backend_count", -1)) == 2
        assert int(summary1.get("compared_count", -1)) == 2
        assert int(summary1.get("pass_count", -1)) == 2
        assert int(summary1.get("fail_count", -1)) == 0
        assert int(summary1.get("blocked_count", -1)) == 0
        assert bool(summary1.get("reference_gate_pass", False)) is True
        for row in payload1.get("steps", []):
            assert row.get("status") == "compared"
            assert bool(row.get("parity_pass", False)) is True

        # Case 2: blocked path with po_sbr mismatch, but allow-failures keeps return code 0
        run2_root = root / "run2"
        run2_summary = run2_root / "summary.json"
        run2_cmd = [
            python_bin,
            "scripts/run_radarsimpy_migration_stepwise.py",
            "--output-root",
            str(run2_root / "outputs"),
            "--output-summary-json",
            str(run2_summary),
            "--candidate-backend",
            "analytic_targets,sionna_rt,po_sbr_rt",
            "--radarsimpy-runtime-provider",
            f"{fixture_module}:radarsimpy_provider",
            "--radarsimpy-runtime-required-modules",
            "",
            "--sionna-runtime-provider",
            f"{fixture_module}:sionna_provider",
            "--sionna-runtime-required-modules",
            "",
            "--po-sbr-runtime-provider",
            f"{fixture_module}:po_provider",
            "--po-sbr-runtime-required-modules",
            "",
            "--allow-failures",
        ]
        proc2 = _run_cmd(run2_cmd, cwd=repo_root, env=env)
        if proc2.returncode != 0:
            raise AssertionError(
                "run2 failed unexpectedly\n"
                f"stdout:\n{proc2.stdout}\n"
                f"stderr:\n{proc2.stderr}\n"
            )

        payload2 = json.loads(run2_summary.read_text(encoding="utf-8"))
        assert payload2.get("migration_status") == "blocked"
        summary2 = dict(payload2.get("summary") or {})
        assert int(summary2.get("candidate_backend_count", -1)) == 3
        assert int(summary2.get("compared_count", -1)) == 3
        assert int(summary2.get("fail_count", -1)) >= 1

        step_by_backend = {str(item.get("backend")): item for item in payload2.get("steps", [])}
        assert bool(step_by_backend["analytic_targets"].get("parity_pass", False)) is True
        assert bool(step_by_backend["sionna_rt"].get("parity_pass", False)) is True
        assert bool(step_by_backend["po_sbr_rt"].get("parity_pass", True)) is False

    print("validate_run_radarsimpy_migration_stepwise: pass")


if __name__ == "__main__":
    run()

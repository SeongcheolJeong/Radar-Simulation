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


def sionna_provider(context):
    n = int(context.get("n_chirps", 1))
    backend = dict(context.get("backend") or {})
    runtime_input = dict(backend.get("runtime_input") or {})
    spheres = list(runtime_input.get("spheres") or [])
    sphere = dict(spheres[0] if len(spheres) > 0 else {})
    center = [float(x) for x in sphere.get("center_m", [25.5, 0.0, 0.0])]
    radius = float(sphere.get("radius_m", 0.5))
    c_norm = math.sqrt(sum(x * x for x in center))
    direction = [1.0, 0.0, 0.0] if c_norm <= 0.0 else [x / c_norm for x in center]
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
    runtime_input = dict(context.get("runtime_input") or {})
    geom = str(runtime_input.get("geometry_path", "fixture_geom"))
    geom_scale = 1.0
    if "dihedral" in geom:
        geom_scale = 1.1
    elif "trihedral" in geom:
        geom_scale = 1.25
    one_way_range = float(runtime_input.get("min_range_m", 25.0))
    phi = math.radians(float(runtime_input.get("phi_deg", 0.0)))
    theta = math.radians(float(runtime_input.get("theta_deg", 90.0)))
    direction = [
        math.sin(theta) * math.cos(phi),
        math.sin(theta) * math.sin(phi),
        math.cos(theta),
    ]
    radial_v = float(runtime_input.get("radial_velocity_mps", 0.0))
    fc_hz = float(context.get("fc_hz", 77e9))
    lam = C0 / fc_hz
    fd = 2.0 * radial_v / lam
    delay = 2.0 * one_way_range / C0
    amp = float(runtime_input.get("amp_floor_abs", 1.0 / (one_way_range * one_way_range)))
    amp = float(amp * geom_scale)

    components = runtime_input.get("components")
    if isinstance(components, list) and len(components) > 0:
        out = []
        for k in range(n):
            for idx, comp in enumerate(components):
                c_phi = math.radians(float(comp.get("phi_deg", runtime_input.get("phi_deg", 0.0))))
                c_theta = math.radians(float(comp.get("theta_deg", runtime_input.get("theta_deg", 90.0))))
                c_dir = [
                    math.sin(c_theta) * math.cos(c_phi),
                    math.sin(c_theta) * math.sin(c_phi),
                    math.cos(c_theta),
                ]
                c_rng = float(comp.get("min_range_m", one_way_range))
                c_delay = 2.0 * c_rng / C0
                c_rv = float(comp.get("radial_velocity_mps", radial_v))
                c_fd = 2.0 * c_rv / lam
                c_amp = float(comp.get("amp_floor_abs", amp))
                c_amp = float(c_amp * geom_scale)
                out.append(
                    {
                        "chirp_index": int(k),
                        "delay_s": c_delay,
                        "doppler_hz": c_fd,
                        "unit_direction": c_dir,
                        "amp": c_amp,
                        "path_id": f"fixture_po_{idx}_{k}",
                        "material_tag": str(comp.get("material_tag", "fixture")),
                        "reflection_order": int(comp.get("reflection_order", 1)),
                    }
                )
        return {"paths": out}

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
    with tempfile.TemporaryDirectory(prefix="validate_po_sbr_full_track_stability_") as td:
        root = Path(td)
        fixture_module = _write_runtime_fixture(root / "full_track_stability_fixture.py")

        out_root = root / "stability_run"
        out_summary = root / "stability_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(root), str(repo_root / "src")])

        run_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_po_sbr_physical_full_track_stability_campaign.py",
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_summary),
                "--runs",
                "2",
                "--strict-stable",
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
            check=True,
        )
        assert (
            "PO-SBR physical full-track stability campaign completed." in run_proc.stdout
        ), run_proc.stdout

        validate_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/validate_po_sbr_physical_full_track_stability_report.py",
                "--summary-json",
                str(out_summary),
                "--require-stable",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert (
            "validate_po_sbr_physical_full_track_stability_report: pass" in validate_proc.stdout
        ), validate_proc.stdout

        payload = json.loads(out_summary.read_text(encoding="utf-8"))
        assert payload.get("campaign_status") == "stable"
        summary = dict(payload.get("summary") or {})
        assert int(summary.get("requested_runs", -1)) == 2
        assert int(summary.get("run_error_count", -1)) == 0
        assert int(summary.get("full_track_blocked_count", -1)) == 0

    print("validate_run_po_sbr_physical_full_track_stability_campaign: pass")


if __name__ == "__main__":
    run()

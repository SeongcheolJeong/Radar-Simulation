#!/usr/bin/env python3
import argparse
import json
import math
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np

from avxsim.runtime_coupling import detect_runtime_modules
from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


BACKEND_ORDER = ("analytic_targets", "sionna_rt", "po_sbr_rt")
DEFAULT_TX_POS_M = [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]]
DEFAULT_RX_POS_M = [
    [0.0, 0.00185, 0.0],
    [0.0, 0.0037, 0.0],
    [0.0, 0.00555, 0.0],
    [0.0, 0.0074, 0.0],
]
DEFAULT_SIONNA_RUNTIME_PROVIDER = (
    "avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba"
)
DEFAULT_PO_SBR_RUNTIME_PROVIDER = (
    "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr"
)
EQUIVALENCE_PROFILES: Dict[str, Dict[str, Any]] = {
    "single_target_range25_v1": {
        "profile_family": "equivalence_strict",
        "components": [
            {
                "target_range_m": 25.0,
                "target_az_deg": 0.0,
                "target_el_deg": 0.0,
                "target_radial_velocity_mps": 0.0,
                "sionna_target_radius_m": 0.5,
                "po_sbr_alpha_deg": 180.0,
                "amp_abs": 1.0,
                "range_amp_exponent": 2.0,
                "material_tag": "metal",
                "reflection_order": 1,
                "po_sbr_bounces": 2,
                "po_sbr_rays_per_lambda": 3.0,
                "path_id_prefix": "golden_path_po_sbr_target0",
            }
        ],
    },
    "single_target_az20_range25_v1": {
        "profile_family": "equivalence_strict",
        "components": [
            {
                "target_range_m": 25.0,
                "target_az_deg": 20.0,
                "target_el_deg": 0.0,
                "target_radial_velocity_mps": 0.0,
                "sionna_target_radius_m": 0.5,
                "po_sbr_alpha_deg": 180.0,
                "amp_abs": 1.0,
                "range_amp_exponent": 2.0,
                "material_tag": "metal",
                "reflection_order": 1,
                "po_sbr_bounces": 2,
                "po_sbr_rays_per_lambda": 3.0,
                "path_id_prefix": "golden_path_po_sbr_target0",
            }
        ],
    },
    "single_target_vel3_range25_v1": {
        "profile_family": "equivalence_strict",
        "components": [
            {
                "target_range_m": 25.0,
                "target_az_deg": 0.0,
                "target_el_deg": 0.0,
                "target_radial_velocity_mps": 3.0,
                "sionna_target_radius_m": 0.5,
                "po_sbr_alpha_deg": 180.0,
                "amp_abs": 1.0,
                "range_amp_exponent": 2.0,
                "material_tag": "metal",
                "reflection_order": 1,
                "po_sbr_bounces": 2,
                "po_sbr_rays_per_lambda": 3.0,
                "path_id_prefix": "golden_path_po_sbr_target0",
            }
        ],
    },
    "dual_target_split_range25_v1": {
        "profile_family": "realism_informational",
        "components": [
            {
                "target_range_m": 24.0,
                "target_az_deg": -8.0,
                "target_el_deg": 0.0,
                "target_radial_velocity_mps": 0.0,
                "sionna_target_radius_m": 0.45,
                "po_sbr_alpha_deg": 180.0,
                "amp_abs": 1.0,
                "range_amp_exponent": 2.0,
                "material_tag": "metal_primary",
                "reflection_order": 1,
                "po_sbr_bounces": 2,
                "po_sbr_rays_per_lambda": 3.0,
                "path_id_prefix": "golden_path_po_sbr_target0",
            },
            {
                "target_range_m": 27.0,
                "target_az_deg": 12.0,
                "target_el_deg": 0.0,
                "target_radial_velocity_mps": 0.0,
                "sionna_target_radius_m": 0.45,
                "po_sbr_alpha_deg": 180.0,
                "amp_abs": 0.55,
                "range_amp_exponent": 2.0,
                "material_tag": "asphalt_secondary",
                "reflection_order": 1,
                "po_sbr_bounces": 2,
                "po_sbr_rays_per_lambda": 3.0,
                "path_id_prefix": "golden_path_po_sbr_target1",
            },
        ],
    },
    "single_target_material_loss_range25_v1": {
        "profile_family": "realism_informational",
        "components": [
            {
                "target_range_m": 25.0,
                "target_az_deg": 5.0,
                "target_el_deg": 0.0,
                "target_radial_velocity_mps": 0.0,
                "sionna_target_radius_m": 0.5,
                "po_sbr_alpha_deg": 180.0,
                "amp_abs": 0.62,
                "range_amp_exponent": 2.0,
                "material_tag": "coated_panel",
                "reflection_order": 2,
                "po_sbr_bounces": 3,
                "po_sbr_rays_per_lambda": 3.5,
                "path_id_prefix": "golden_path_po_sbr_target0",
            }
        ],
    },
    "mesh_dihedral_range25_v1": {
        "profile_family": "realism_informational",
        "po_sbr_geometry_path": "geometries/dihedral.obj",
        "components": [
            {
                "target_range_m": 25.0,
                "target_az_deg": 8.0,
                "target_el_deg": 0.0,
                "target_radial_velocity_mps": 0.0,
                "sionna_target_radius_m": 0.5,
                "po_sbr_alpha_deg": 180.0,
                "amp_abs": 0.9,
                "range_amp_exponent": 2.0,
                "material_tag": "mesh_dihedral_metal",
                "reflection_order": 2,
                "po_sbr_bounces": 3,
                "po_sbr_rays_per_lambda": 3.5,
                "path_id_prefix": "golden_path_po_sbr_dihedral",
            }
        ],
    },
    "mesh_trihedral_range25_v1": {
        "profile_family": "realism_informational",
        "po_sbr_geometry_path": "geometries/trihedral.obj",
        "components": [
            {
                "target_range_m": 25.0,
                "target_az_deg": -6.0,
                "target_el_deg": 0.0,
                "target_radial_velocity_mps": 0.0,
                "sionna_target_radius_m": 0.45,
                "po_sbr_alpha_deg": 180.0,
                "amp_abs": 1.2,
                "range_amp_exponent": 2.0,
                "material_tag": "mesh_trihedral_primary",
                "reflection_order": 2,
                "po_sbr_bounces": 3,
                "po_sbr_rays_per_lambda": 3.5,
                "path_id_prefix": "golden_path_po_sbr_trihedral_0",
            },
            {
                "target_range_m": 29.0,
                "target_az_deg": 11.0,
                "target_el_deg": 0.0,
                "target_radial_velocity_mps": 0.0,
                "sionna_target_radius_m": 0.45,
                "po_sbr_alpha_deg": 180.0,
                "amp_abs": 0.48,
                "range_amp_exponent": 2.0,
                "material_tag": "mesh_trihedral_secondary",
                "reflection_order": 2,
                "po_sbr_bounces": 3,
                "po_sbr_rays_per_lambda": 3.5,
                "path_id_prefix": "golden_path_po_sbr_trihedral_1",
            },
        ],
    },
}
SUPPORTED_EQV_PROFILE_IDS = tuple(EQUIVALENCE_PROFILES.keys())


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run backend golden-path executions (analytic/sionna_rt/po_sbr_rt) and "
            "write one strict progress report for local migration tracking."
        )
    )
    p.add_argument(
        "--backend",
        action="append",
        default=[],
        help=(
            "Backend to run (repeatable, comma-separated allowed): "
            "analytic_targets, sionna_rt, po_sbr_rt. Default: all."
        ),
    )
    p.add_argument("--output-root", required=True, help="Output root directory")
    p.add_argument("--output-summary-json", required=True, help="Output summary JSON path")
    p.add_argument("--scene-id-prefix", default="scene_runtime_golden_path_v1", help="Scene id prefix")
    p.add_argument("--n-chirps", type=int, default=8, help="Number of chirps per backend run")
    p.add_argument("--samples-per-chirp", type=int, default=1024, help="ADC samples per chirp")
    p.add_argument(
        "--scene-equivalence-profile",
        default="single_target_range25_v1",
        help=(
            "Scene profile id. Supported: " + ", ".join(SUPPORTED_EQV_PROFILE_IDS)
        ),
    )
    p.add_argument(
        "--target-range-m",
        type=float,
        default=None,
        help="Optional override for reference one-way target range",
    )
    p.add_argument(
        "--target-az-deg",
        type=float,
        default=None,
        help="Optional override for target azimuth angle (degrees)",
    )
    p.add_argument(
        "--target-el-deg",
        type=float,
        default=None,
        help="Optional override for target elevation angle (degrees)",
    )
    p.add_argument(
        "--target-radial-velocity-mps",
        type=float,
        default=None,
        help="Optional override for radial velocity (m/s)",
    )
    p.add_argument(
        "--sionna-target-radius-m",
        type=float,
        default=None,
        help="Optional override for sionna_rt sphere radius",
    )
    p.add_argument(
        "--strict-nonexecuted",
        action="store_true",
        help="Exit non-zero if any requested backend is blocked or failed",
    )

    p.add_argument(
        "--sionna-runtime-provider",
        default=DEFAULT_SIONNA_RUNTIME_PROVIDER,
        help="Runtime provider spec for sionna_rt backend",
    )
    p.add_argument(
        "--sionna-runtime-required-modules",
        default="mitsuba,drjit",
        help="Comma-separated required modules for sionna_rt runtime provider",
    )

    p.add_argument(
        "--po-sbr-runtime-provider",
        default=DEFAULT_PO_SBR_RUNTIME_PROVIDER,
        help="Runtime provider spec for po_sbr_rt backend",
    )
    p.add_argument(
        "--po-sbr-runtime-required-modules",
        default="rtxpy,igl",
        help="Comma-separated required modules for po_sbr_rt runtime provider",
    )
    p.add_argument(
        "--po-sbr-repo-root",
        default="external/PO-SBR-Python",
        help="PO-SBR repository root (used by default PO-SBR runtime provider)",
    )
    p.add_argument(
        "--po-sbr-geometry-path",
        default="geometries/plate.obj",
        help="PO-SBR geometry path (absolute or relative to --po-sbr-repo-root)",
    )
    p.add_argument(
        "--po-sbr-alpha-deg",
        type=float,
        default=None,
        help="Optional override for PO-SBR polarization alpha angle",
    )
    p.add_argument(
        "--po-sbr-phi-deg",
        type=float,
        default=None,
        help="Optional override for PO-SBR observation phi angle",
    )
    p.add_argument(
        "--po-sbr-theta-deg",
        type=float,
        default=None,
        help="Optional override for PO-SBR observation theta angle",
    )
    p.add_argument(
        "--po-sbr-min-range-m",
        type=float,
        default=None,
        help="Optional override for PO-SBR one-way minimum range clamp",
    )
    return p.parse_args()


def _parse_backends(items: Sequence[str]) -> List[str]:
    if len(items) == 0:
        return list(BACKEND_ORDER)

    out: List[str] = []
    allowed = set(BACKEND_ORDER)
    for raw in items:
        for token in str(raw).split(","):
            name = str(token).strip().lower()
            if name == "":
                continue
            if name not in allowed:
                raise ValueError(f"unsupported backend: {name}")
            if name not in out:
                out.append(name)
    if len(out) == 0:
        raise ValueError("at least one backend must be selected")
    return out


def _parse_csv_modules(raw: str) -> List[str]:
    out: List[str] = []
    for token in str(raw).split(","):
        name = str(token).strip()
        if name == "":
            continue
        out.append(name)
    return out


def _deg_to_unit_direction(az_deg: float, el_deg: float) -> List[float]:
    az = math.radians(float(az_deg))
    el = math.radians(float(el_deg))
    ux = float(math.cos(el) * math.cos(az))
    uy = float(math.cos(el) * math.sin(az))
    uz = float(math.sin(el))
    norm = math.sqrt(ux * ux + uy * uy + uz * uz)
    if norm <= 0.0:
        raise ValueError("invalid direction from az/el")
    return [ux / norm, uy / norm, uz / norm]


def _unit_direction_to_po_angles(unit_direction: Sequence[float]) -> Dict[str, float]:
    ux, uy, uz = (float(unit_direction[0]), float(unit_direction[1]), float(unit_direction[2]))
    phi_deg = float(math.degrees(math.atan2(uy, ux)))
    # PO-SBR provider direction convention: x=sin(theta)cos(phi), y=sin(theta)sin(phi), z=cos(theta)
    uz_clip = max(-1.0, min(1.0, uz))
    theta_deg = float(math.degrees(math.acos(uz_clip)))
    return {"phi_deg": phi_deg, "theta_deg": theta_deg}


def _resolve_scene_equivalence_inputs(args: argparse.Namespace) -> Dict[str, Any]:
    profile = str(args.scene_equivalence_profile).strip()
    if profile not in EQUIVALENCE_PROFILES:
        raise ValueError(f"unsupported --scene-equivalence-profile: {profile}")

    raw_profile = dict(EQUIVALENCE_PROFILES[profile])
    profile_family = str(raw_profile.get("profile_family", "equivalence_strict")).strip() or "equivalence_strict"
    po_sbr_geometry_path_override_raw = raw_profile.get("po_sbr_geometry_path")
    po_sbr_geometry_path_override = None
    if po_sbr_geometry_path_override_raw is not None:
        text = str(po_sbr_geometry_path_override_raw).strip()
        if text == "":
            raise ValueError("profile po_sbr_geometry_path must be non-empty when provided")
        po_sbr_geometry_path_override = text
    raw_components = raw_profile.get("components")
    if not isinstance(raw_components, Sequence) or isinstance(raw_components, (str, bytes)):
        raise ValueError(f"profile components must be non-empty list: {profile}")
    if len(raw_components) == 0:
        raise ValueError(f"profile components must be non-empty list: {profile}")

    override_flags = (
        args.target_range_m is not None
        or args.target_az_deg is not None
        or args.target_el_deg is not None
        or args.target_radial_velocity_mps is not None
        or args.sionna_target_radius_m is not None
        or args.po_sbr_alpha_deg is not None
        or args.po_sbr_phi_deg is not None
        or args.po_sbr_theta_deg is not None
        or args.po_sbr_min_range_m is not None
    )
    if override_flags and len(raw_components) > 1:
        raise ValueError(
            "single-target overrides are only supported when profile has one component"
        )

    resolved_components: List[Dict[str, Any]] = []
    for idx, raw_item in enumerate(raw_components):
        if not isinstance(raw_item, Mapping):
            raise ValueError(f"profile components[{idx}] must be object")
        item = dict(raw_item)

        target_range_m = float(item.get("target_range_m", 25.0))
        target_az_deg = float(item.get("target_az_deg", 0.0))
        target_el_deg = float(item.get("target_el_deg", 0.0))
        target_radial_velocity_mps = float(item.get("target_radial_velocity_mps", 0.0))
        sionna_target_radius_m = float(item.get("sionna_target_radius_m", 0.5))
        po_sbr_alpha_deg = float(item.get("po_sbr_alpha_deg", 180.0))
        amp_abs = float(item.get("amp_abs", 1.0))
        range_amp_exponent = float(item.get("range_amp_exponent", 2.0))
        material_tag = str(item.get("material_tag", f"profile_target_{idx}")).strip()
        reflection_order = int(item.get("reflection_order", 1))
        po_sbr_bounces = int(item.get("po_sbr_bounces", 2))
        po_sbr_rays_per_lambda = float(item.get("po_sbr_rays_per_lambda", 3.0))
        path_id_prefix = str(item.get("path_id_prefix", f"golden_path_po_sbr_target{idx}")).strip()

        if idx == 0:
            if args.target_range_m is not None:
                target_range_m = float(args.target_range_m)
            if args.target_az_deg is not None:
                target_az_deg = float(args.target_az_deg)
            if args.target_el_deg is not None:
                target_el_deg = float(args.target_el_deg)
            if args.target_radial_velocity_mps is not None:
                target_radial_velocity_mps = float(args.target_radial_velocity_mps)
            if args.sionna_target_radius_m is not None:
                sionna_target_radius_m = float(args.sionna_target_radius_m)
            if args.po_sbr_alpha_deg is not None:
                po_sbr_alpha_deg = float(args.po_sbr_alpha_deg)

        unit_dir = _deg_to_unit_direction(
            az_deg=float(target_az_deg),
            el_deg=float(target_el_deg),
        )
        po_angles = _unit_direction_to_po_angles(unit_direction=unit_dir)
        po_sbr_phi_deg = float(item.get("po_sbr_phi_deg", po_angles["phi_deg"]))
        po_sbr_theta_deg = float(item.get("po_sbr_theta_deg", po_angles["theta_deg"]))
        po_sbr_min_range_m = float(item.get("po_sbr_min_range_m", target_range_m))

        if idx == 0:
            if args.po_sbr_phi_deg is not None:
                po_sbr_phi_deg = float(args.po_sbr_phi_deg)
            if args.po_sbr_theta_deg is not None:
                po_sbr_theta_deg = float(args.po_sbr_theta_deg)
            if args.po_sbr_min_range_m is not None:
                po_sbr_min_range_m = float(args.po_sbr_min_range_m)

        if target_range_m <= 0.0:
            raise ValueError(f"profile components[{idx}].target_range_m must be > 0")
        if sionna_target_radius_m <= 0.0:
            raise ValueError(f"profile components[{idx}].sionna_target_radius_m must be > 0")
        if po_sbr_min_range_m <= 0.0:
            raise ValueError(f"profile components[{idx}].po_sbr_min_range_m must be > 0")
        if amp_abs < 0.0:
            raise ValueError(f"profile components[{idx}].amp_abs must be >= 0")
        if range_amp_exponent < 0.0:
            raise ValueError(f"profile components[{idx}].range_amp_exponent must be >= 0")
        if po_sbr_bounces < 0:
            raise ValueError(f"profile components[{idx}].po_sbr_bounces must be >= 0")
        if po_sbr_rays_per_lambda <= 0.0:
            raise ValueError(f"profile components[{idx}].po_sbr_rays_per_lambda must be > 0")
        if reflection_order < 0:
            raise ValueError(f"profile components[{idx}].reflection_order must be >= 0")
        if material_tag == "":
            raise ValueError(f"profile components[{idx}].material_tag must be non-empty")
        if path_id_prefix == "":
            raise ValueError(f"profile components[{idx}].path_id_prefix must be non-empty")

        amp_at_range = float(amp_abs / max(target_range_m ** max(range_amp_exponent, 0.0), 1.0e-12))
        po_sbr_amp_floor_abs = float(item.get("po_sbr_amp_floor_abs", amp_at_range))
        po_sbr_amp_target_abs = float(item.get("po_sbr_amp_target_abs", amp_at_range))
        if po_sbr_amp_floor_abs < 0.0:
            raise ValueError(f"profile components[{idx}].po_sbr_amp_floor_abs must be >= 0")
        if po_sbr_amp_target_abs < 0.0:
            raise ValueError(f"profile components[{idx}].po_sbr_amp_target_abs must be >= 0")

        resolved_components.append(
            {
                "target_range_m": target_range_m,
                "target_az_deg": target_az_deg,
                "target_el_deg": target_el_deg,
                "target_radial_velocity_mps": target_radial_velocity_mps,
                "sionna_target_radius_m": sionna_target_radius_m,
                "po_sbr_alpha_deg": po_sbr_alpha_deg,
                "po_sbr_phi_deg": po_sbr_phi_deg,
                "po_sbr_theta_deg": po_sbr_theta_deg,
                "po_sbr_min_range_m": po_sbr_min_range_m,
                "po_sbr_amp_floor_abs": po_sbr_amp_floor_abs,
                "po_sbr_amp_target_abs": po_sbr_amp_target_abs,
                "amp_abs": amp_abs,
                "range_amp_exponent": range_amp_exponent,
                "material_tag": material_tag,
                "reflection_order": reflection_order,
                "po_sbr_bounces": po_sbr_bounces,
                "po_sbr_rays_per_lambda": po_sbr_rays_per_lambda,
                "path_id_prefix": path_id_prefix,
            }
        )

    primary = resolved_components[0]
    return {
        "profile_family": profile_family,
        "po_sbr_geometry_path_override": po_sbr_geometry_path_override,
        "components": resolved_components,
        "target_count": int(len(resolved_components)),
        "target_range_m": float(primary["target_range_m"]),
        "target_az_deg": float(primary["target_az_deg"]),
        "target_el_deg": float(primary["target_el_deg"]),
        "target_radial_velocity_mps": float(primary["target_radial_velocity_mps"]),
        "sionna_target_radius_m": float(primary["sionna_target_radius_m"]),
        "po_sbr_alpha_deg": float(primary["po_sbr_alpha_deg"]),
        "po_sbr_phi_deg": float(primary["po_sbr_phi_deg"]),
        "po_sbr_theta_deg": float(primary["po_sbr_theta_deg"]),
        "po_sbr_min_range_m": float(primary["po_sbr_min_range_m"]),
        "po_sbr_amp_floor_abs": float(primary["po_sbr_amp_floor_abs"]),
        "po_sbr_amp_target_abs": float(primary["po_sbr_amp_target_abs"]),
    }


def _base_radar(samples_per_chirp: int) -> Dict[str, Any]:
    return {
        "fc_hz": 77e9,
        "slope_hz_per_s": 20e12,
        "fs_hz": 20e6,
        "samples_per_chirp": int(samples_per_chirp),
    }


def _base_map_config(samples_per_chirp: int) -> Dict[str, Any]:
    return {
        "nfft_range": int(samples_per_chirp),
        "nfft_doppler": 64,
        "nfft_angle": 32,
        "range_bin_limit": min(int(samples_per_chirp // 2), 256),
    }


def _detect_nvidia_runtime() -> Dict[str, Any]:
    exe = shutil.which("nvidia-smi")
    if exe is None:
        return {"available": False, "executable": None, "error": None}
    try:
        subprocess.run([exe, "--help"], capture_output=True, text=True, check=True)
        return {"available": True, "executable": exe, "error": None}
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "available": False,
            "executable": exe,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _resolve_repo_root(raw_path: str, cwd: Path) -> Path:
    p = Path(str(raw_path).strip()).expanduser()
    if not p.is_absolute():
        p = cwd / p
    return p.resolve()


def _resolve_geometry_path(repo_root: Path, raw_path: str) -> Path:
    p = Path(str(raw_path).strip()).expanduser()
    if not p.is_absolute():
        p = repo_root / p
    return p.resolve()


def _provider_uses_native_po_sbr_assets(provider_spec: str) -> bool:
    provider = str(provider_spec).strip()
    if provider == DEFAULT_PO_SBR_RUNTIME_PROVIDER:
        return True
    return provider.startswith("avxsim.runtime_providers.po_sbr_rt_provider:")


def _detect_missing_modules(required_modules: Sequence[str]) -> Dict[str, Any]:
    required = [str(x).strip() for x in required_modules if str(x).strip() != ""]
    report = detect_runtime_modules(required)
    missing = [name for name, item in report.items() if not bool(item.get("available", False))]
    return {
        "required_modules": list(required),
        "module_report": report,
        "missing_required_modules": sorted(missing),
    }


def _preflight_analytic(system_name: str) -> Dict[str, Any]:
    return {
        "status": "ready",
        "blockers": [],
        "diagnostics": {
            "platform": system_name,
            "runtime_provider": None,
            "required_modules": [],
            "missing_required_modules": [],
        },
    }


def _preflight_sionna(
    system_name: str,
    runtime_provider: str,
    required_modules: Sequence[str],
) -> Dict[str, Any]:
    module_diag = _detect_missing_modules(required_modules=required_modules)
    blockers: List[str] = []
    if str(runtime_provider).strip() == "":
        blockers.append("missing_runtime_provider")
    if len(module_diag["missing_required_modules"]) > 0:
        blockers.append("missing_required_modules")

    return {
        "status": "ready" if len(blockers) == 0 else "blocked",
        "blockers": blockers,
        "diagnostics": {
            "platform": system_name,
            "runtime_provider": str(runtime_provider),
            "required_modules": module_diag["required_modules"],
            "module_report": module_diag["module_report"],
            "missing_required_modules": module_diag["missing_required_modules"],
        },
    }


def _preflight_po_sbr(
    system_name: str,
    runtime_provider: str,
    required_modules: Sequence[str],
    repo_root: Path,
    geometry_path: Path,
) -> Dict[str, Any]:
    module_diag = _detect_missing_modules(required_modules=required_modules)
    nvidia_diag = _detect_nvidia_runtime()
    blockers: List[str] = []
    if str(runtime_provider).strip() == "":
        blockers.append("missing_runtime_provider")
    if len(module_diag["missing_required_modules"]) > 0:
        blockers.append("missing_required_modules")

    uses_native_assets = _provider_uses_native_po_sbr_assets(runtime_provider)
    if uses_native_assets:
        if system_name != "Linux":
            blockers.append(f"unsupported_platform:{system_name}")
        if not bool(nvidia_diag.get("available", False)):
            blockers.append("missing_nvidia_runtime")
        if not repo_root.exists():
            blockers.append("missing_repo")
        if not geometry_path.exists():
            blockers.append("missing_geometry")

    return {
        "status": "ready" if len(blockers) == 0 else "blocked",
        "blockers": blockers,
        "diagnostics": {
            "platform": system_name,
            "runtime_provider": str(runtime_provider),
            "required_modules": module_diag["required_modules"],
            "module_report": module_diag["module_report"],
            "missing_required_modules": module_diag["missing_required_modules"],
            "nvidia_runtime": nvidia_diag,
            "po_sbr_repo_root": str(repo_root),
            "po_sbr_repo_exists": bool(repo_root.exists()),
            "po_sbr_geometry_path": str(geometry_path),
            "po_sbr_geometry_exists": bool(geometry_path.exists()),
            "native_provider_asset_checks_enabled": bool(uses_native_assets),
        },
    }


def _build_analytic_scene(
    scene_id: str,
    n_chirps: int,
    samples_per_chirp: int,
    components: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    targets: List[Dict[str, Any]] = []
    for comp in components:
        targets.append(
            {
                "range_m": float(comp["target_range_m"]),
                "radial_velocity_mps": float(comp["target_radial_velocity_mps"]),
                "az_deg": float(comp["target_az_deg"]),
                "el_deg": float(comp["target_el_deg"]),
                "amp": float(comp["amp_abs"]),
                "range_amp_exponent": float(comp["range_amp_exponent"]),
                "material_tag": str(comp["material_tag"]),
            }
        )
    return {
        "scene_id": scene_id,
        "backend": {
            "type": "analytic_targets",
            "n_chirps": int(n_chirps),
            "chirp_interval_s": 4.0e-5,
            "tx_pos_m": DEFAULT_TX_POS_M,
            "rx_pos_m": DEFAULT_RX_POS_M,
            "targets": targets,
            "noise_sigma": 0.0,
        },
        "radar": _base_radar(samples_per_chirp=samples_per_chirp),
        "map_config": _base_map_config(samples_per_chirp=samples_per_chirp),
    }


def _build_sionna_scene(
    scene_id: str,
    n_chirps: int,
    samples_per_chirp: int,
    components: Sequence[Mapping[str, Any]],
    runtime_provider: str,
    runtime_required_modules: Sequence[str],
) -> Dict[str, Any]:
    spheres: List[Dict[str, Any]] = []
    for idx, comp in enumerate(components):
        radius = float(comp["sionna_target_radius_m"])
        if radius <= 0.0:
            raise ValueError(f"sionna target radius must be > 0 at component {idx}")
        direction = _deg_to_unit_direction(
            az_deg=float(comp["target_az_deg"]),
            el_deg=float(comp["target_el_deg"]),
        )
        center_range = float(comp["target_range_m"]) + radius
        center_m = [float(center_range * direction[i]) for i in range(3)]
        velocity_mps = [float(comp["target_radial_velocity_mps"] * direction[i]) for i in range(3)]
        spheres.append(
            {
                "center_m": center_m,
                "radius_m": radius,
                "velocity_mps": velocity_mps,
                "amp": float(comp["amp_abs"]),
                "range_amp_exponent": float(comp["range_amp_exponent"]),
                "path_id_prefix": f"golden_path_sionna_target_{idx}",
                "material_tag": str(comp["material_tag"]),
                "reflection_order": int(comp["reflection_order"]),
            }
        )
    return {
        "scene_id": scene_id,
        "backend": {
            "type": "sionna_rt",
            "n_chirps": int(n_chirps),
            "tx_pos_m": DEFAULT_TX_POS_M,
            "rx_pos_m": DEFAULT_RX_POS_M,
            "runtime_provider": str(runtime_provider),
            "runtime_required_modules": [str(x) for x in runtime_required_modules],
            "runtime_failure_policy": "error",
            "runtime_input": {
                "ego_origin_m": [0.0, 0.0, 0.0],
                "chirp_interval_s": 4.0e-5,
                "spheres": spheres,
            },
            "noise_sigma": 0.0,
        },
        "radar": _base_radar(samples_per_chirp=samples_per_chirp),
        "map_config": _base_map_config(samples_per_chirp=samples_per_chirp),
    }


def _build_po_sbr_scene(
    scene_id: str,
    n_chirps: int,
    samples_per_chirp: int,
    components: Sequence[Mapping[str, Any]],
    runtime_provider: str,
    runtime_required_modules: Sequence[str],
    repo_root: Path,
    geometry_path: Path,
) -> Dict[str, Any]:
    if len(components) == 0:
        raise ValueError("po_sbr scene requires at least one component")
    primary = dict(components[0])
    runtime_components: List[Dict[str, Any]] = []
    for comp in components:
        runtime_components.append(
            {
                "alpha_deg": float(comp["po_sbr_alpha_deg"]),
                "phi_deg": float(comp["po_sbr_phi_deg"]),
                "theta_deg": float(comp["po_sbr_theta_deg"]),
                "freq_hz": 77e9,
                "rays_per_lambda": float(comp["po_sbr_rays_per_lambda"]),
                "bounces": int(comp["po_sbr_bounces"]),
                "radial_velocity_mps": float(comp["target_radial_velocity_mps"]),
                "min_range_m": float(max(comp["po_sbr_min_range_m"], comp["target_range_m"])),
                "amp_floor_abs": float(comp["po_sbr_amp_floor_abs"]),
                "amp_target_abs": float(comp["po_sbr_amp_target_abs"]),
                "material_tag": str(comp["material_tag"]),
                "reflection_order": int(comp["reflection_order"]),
                "path_id_prefix": str(comp["path_id_prefix"]),
            }
        )
    return {
        "scene_id": scene_id,
        "backend": {
            "type": "po_sbr_rt",
            "n_chirps": int(n_chirps),
            "tx_pos_m": DEFAULT_TX_POS_M,
            "rx_pos_m": DEFAULT_RX_POS_M,
            "runtime_provider": str(runtime_provider),
            "runtime_required_modules": [str(x) for x in runtime_required_modules],
            "runtime_failure_policy": "error",
            "runtime_input": {
                "po_sbr_repo_root": str(repo_root),
                "geometry_path": str(geometry_path),
                "alpha_deg": float(primary["po_sbr_alpha_deg"]),
                "phi_deg": float(primary["po_sbr_phi_deg"]),
                "theta_deg": float(primary["po_sbr_theta_deg"]),
                "freq_hz": 77e9,
                "rays_per_lambda": float(primary["po_sbr_rays_per_lambda"]),
                "bounces": int(primary["po_sbr_bounces"]),
                "radial_velocity_mps": float(primary["target_radial_velocity_mps"]),
                "min_range_m": float(max(primary["po_sbr_min_range_m"], primary["target_range_m"])),
                "amp_floor_abs": float(primary["po_sbr_amp_floor_abs"]),
                "amp_target_abs": float(primary["po_sbr_amp_target_abs"]),
                "material_tag": str(primary["material_tag"]),
                "reflection_order": int(primary["reflection_order"]),
                "path_id_prefix": str(primary["path_id_prefix"]),
                "components": runtime_components,
            },
            "noise_sigma": 0.0,
        },
        "radar": _base_radar(samples_per_chirp=samples_per_chirp),
        "map_config": _base_map_config(samples_per_chirp=samples_per_chirp),
    }


def _load_optional_runtime_resolution(radar_map_npz: Path) -> Optional[Dict[str, Any]]:
    with np.load(str(radar_map_npz), allow_pickle=False) as payload:
        if "metadata_json" not in payload:
            return None
        raw = payload["metadata_json"]
        raw_value = raw.tolist() if hasattr(raw, "tolist") else raw
        metadata = json.loads(str(raw_value))
    runtime_resolution = metadata.get("runtime_resolution")
    if isinstance(runtime_resolution, Mapping):
        return dict(runtime_resolution)
    return None


def _count_paths(path_list_json: Path) -> int:
    payload = json.loads(path_list_json.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("path_list_json must contain list payload")
    return int(sum(len(chirp_paths) for chirp_paths in payload if isinstance(chirp_paths, list)))


def _base_result(status: str, diagnostics: Mapping[str, Any], blockers: Sequence[str]) -> Dict[str, Any]:
    return {
        "status": status,
        "blockers": [str(x) for x in blockers],
        "diagnostics": dict(diagnostics),
        "scene_json": None,
        "output_dir": None,
        "path_list_json": None,
        "adc_cube_npz": None,
        "radar_map_npz": None,
        "frame_count": 0,
        "path_count": 0,
        "runtime_resolution": None,
        "error": None,
    }


def _execute_backend(scene_payload: Mapping[str, Any], backend_root: Path, diagnostics: Mapping[str, Any]) -> Dict[str, Any]:
    backend_root.mkdir(parents=True, exist_ok=True)
    backend_type = str(scene_payload.get("backend", {}).get("type", "")).strip()
    scene_json = backend_root / f"scene_{backend_type}_golden_path.json"
    scene_json.write_text(json.dumps(scene_payload, indent=2), encoding="utf-8")

    pipeline_output_dir = backend_root / "pipeline_outputs"
    run_out = run_object_scene_to_radar_map_json(
        scene_json_path=str(scene_json),
        output_dir=str(pipeline_output_dir),
        run_hybrid_estimation=False,
    )

    path_list_json = Path(str(run_out["path_list_json"])).resolve()
    adc_cube_npz = Path(str(run_out["adc_cube_npz"])).resolve()
    radar_map_npz = Path(str(run_out["radar_map_npz"])).resolve()

    return {
        "status": "executed",
        "blockers": [],
        "diagnostics": dict(diagnostics),
        "scene_json": str(scene_json.resolve()),
        "output_dir": str(pipeline_output_dir.resolve()),
        "path_list_json": str(path_list_json),
        "adc_cube_npz": str(adc_cube_npz),
        "radar_map_npz": str(radar_map_npz),
        "frame_count": int(run_out.get("frame_count", 0)),
        "path_count": _count_paths(path_list_json=path_list_json),
        "runtime_resolution": _load_optional_runtime_resolution(radar_map_npz=radar_map_npz),
        "error": None,
    }


def _progress_summary(results: Mapping[str, Mapping[str, Any]], requested_backends: Sequence[str]) -> Dict[str, Any]:
    executed = [name for name in requested_backends if str(results.get(name, {}).get("status", "")) == "executed"]
    blocked = [name for name in requested_backends if str(results.get(name, {}).get("status", "")) == "blocked"]
    failed = [name for name in requested_backends if str(results.get(name, {}).get("status", "")) == "failed"]
    total = int(len(requested_backends))

    po_sbr_state = "not_requested"
    if "po_sbr_rt" in requested_backends:
        po_status = str(results.get("po_sbr_rt", {}).get("status", ""))
        if po_status == "executed":
            po_sbr_state = "closed_local_runtime"
        elif po_status == "blocked":
            po_sbr_state = "blocked"
        elif po_status == "failed":
            po_sbr_state = "failed"
        else:
            po_sbr_state = "unknown"

    return {
        "requested_count": total,
        "executed_count": int(len(executed)),
        "blocked_count": int(len(blocked)),
        "failed_count": int(len(failed)),
        "executed_backends": executed,
        "blocked_backends": blocked,
        "failed_backends": failed,
        "progress_ratio": (float(len(executed)) / float(total)) if total > 0 else 0.0,
        "po_sbr_migration_status": po_sbr_state,
    }


def main() -> None:
    args = parse_args()

    selected_backends = _parse_backends(args.backend)
    if int(args.n_chirps) <= 0:
        raise ValueError("--n-chirps must be > 0")
    if int(args.samples_per_chirp) <= 0:
        raise ValueError("--samples-per-chirp must be > 0")
    profile = str(args.scene_equivalence_profile).strip()
    eqv = _resolve_scene_equivalence_inputs(args=args)

    cwd = Path.cwd().resolve()
    out_root = Path(args.output_root).expanduser()
    if not out_root.is_absolute():
        out_root = (cwd / out_root).resolve()
    else:
        out_root = out_root.resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    out_summary_json = Path(args.output_summary_json).expanduser()
    if not out_summary_json.is_absolute():
        out_summary_json = (cwd / out_summary_json).resolve()
    else:
        out_summary_json = out_summary_json.resolve()
    out_summary_json.parent.mkdir(parents=True, exist_ok=True)

    sionna_required_modules = _parse_csv_modules(args.sionna_runtime_required_modules)
    po_sbr_required_modules = _parse_csv_modules(args.po_sbr_runtime_required_modules)

    po_sbr_repo_root = _resolve_repo_root(args.po_sbr_repo_root, cwd=cwd)
    po_sbr_geometry_path = _resolve_geometry_path(
        repo_root=po_sbr_repo_root,
        raw_path=args.po_sbr_geometry_path,
    )
    po_sbr_geometry_path_effective = po_sbr_geometry_path
    if eqv.get("po_sbr_geometry_path_override") is not None:
        po_sbr_geometry_path_effective = _resolve_geometry_path(
            repo_root=po_sbr_repo_root,
            raw_path=str(eqv["po_sbr_geometry_path_override"]),
        )

    system_name = platform.system()
    results: Dict[str, Dict[str, Any]] = {}

    for backend_name in selected_backends:
        backend_root = out_root / backend_name

        if backend_name == "analytic_targets":
            preflight = _preflight_analytic(system_name=system_name)
            scene_payload = _build_analytic_scene(
                scene_id=f"{args.scene_id_prefix}_{backend_name}",
                n_chirps=int(args.n_chirps),
                samples_per_chirp=int(args.samples_per_chirp),
                components=eqv["components"],
            )
        elif backend_name == "sionna_rt":
            preflight = _preflight_sionna(
                system_name=system_name,
                runtime_provider=str(args.sionna_runtime_provider),
                required_modules=sionna_required_modules,
            )
            scene_payload = _build_sionna_scene(
                scene_id=f"{args.scene_id_prefix}_{backend_name}",
                n_chirps=int(args.n_chirps),
                samples_per_chirp=int(args.samples_per_chirp),
                components=eqv["components"],
                runtime_provider=str(args.sionna_runtime_provider),
                runtime_required_modules=sionna_required_modules,
            )
        elif backend_name == "po_sbr_rt":
            preflight = _preflight_po_sbr(
                system_name=system_name,
                runtime_provider=str(args.po_sbr_runtime_provider),
                required_modules=po_sbr_required_modules,
                repo_root=po_sbr_repo_root,
                geometry_path=po_sbr_geometry_path_effective,
            )
            scene_payload = _build_po_sbr_scene(
                scene_id=f"{args.scene_id_prefix}_{backend_name}",
                n_chirps=int(args.n_chirps),
                samples_per_chirp=int(args.samples_per_chirp),
                components=eqv["components"],
                runtime_provider=str(args.po_sbr_runtime_provider),
                runtime_required_modules=po_sbr_required_modules,
                repo_root=po_sbr_repo_root,
                geometry_path=po_sbr_geometry_path_effective,
            )
        else:  # pragma: no cover - guarded by _parse_backends
            raise ValueError(f"unsupported backend: {backend_name}")

        blockers = list(preflight["blockers"])
        diagnostics = dict(preflight["diagnostics"])
        if len(blockers) > 0:
            results[backend_name] = _base_result(
                status="blocked",
                diagnostics=diagnostics,
                blockers=blockers,
            )
            continue

        try:
            results[backend_name] = _execute_backend(
                scene_payload=scene_payload,
                backend_root=backend_root,
                diagnostics=diagnostics,
            )
        except Exception as exc:
            failed = _base_result(
                status="failed",
                diagnostics=diagnostics,
                blockers=[],
            )
            failed["error"] = f"{type(exc).__name__}: {exc}"
            results[backend_name] = failed

    summary = _progress_summary(results=results, requested_backends=selected_backends)
    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "workspace_root": str(cwd),
        "python_executable": str(Path(sys.executable).resolve()),
        "python_version": str(sys.version).strip(),
        "platform_system": system_name,
        "scene_equivalence_profile": profile,
        "scene_profile_family": str(eqv["profile_family"]),
        "equivalence_inputs": {
            "profile_family": str(eqv["profile_family"]),
            "target_count": int(eqv["target_count"]),
            "target_range_m": float(eqv["target_range_m"]),
            "target_az_deg": float(eqv["target_az_deg"]),
            "target_el_deg": float(eqv["target_el_deg"]),
            "target_radial_velocity_mps": float(eqv["target_radial_velocity_mps"]),
            "sionna_target_radius_m": float(eqv["sionna_target_radius_m"]),
            "po_sbr_alpha_deg": float(eqv["po_sbr_alpha_deg"]),
            "po_sbr_phi_deg": float(eqv["po_sbr_phi_deg"]),
            "po_sbr_theta_deg": float(eqv["po_sbr_theta_deg"]),
            "po_sbr_min_range_m": float(eqv["po_sbr_min_range_m"]),
            "po_sbr_amp_floor_abs": float(eqv["po_sbr_amp_floor_abs"]),
            "po_sbr_amp_target_abs": float(eqv["po_sbr_amp_target_abs"]),
            "po_sbr_geometry_path": str(po_sbr_geometry_path_effective),
            "components": [
                {
                    "target_range_m": float(comp["target_range_m"]),
                    "target_az_deg": float(comp["target_az_deg"]),
                    "target_el_deg": float(comp["target_el_deg"]),
                    "target_radial_velocity_mps": float(comp["target_radial_velocity_mps"]),
                    "sionna_target_radius_m": float(comp["sionna_target_radius_m"]),
                    "po_sbr_alpha_deg": float(comp["po_sbr_alpha_deg"]),
                    "po_sbr_phi_deg": float(comp["po_sbr_phi_deg"]),
                    "po_sbr_theta_deg": float(comp["po_sbr_theta_deg"]),
                    "po_sbr_min_range_m": float(comp["po_sbr_min_range_m"]),
                    "po_sbr_amp_floor_abs": float(comp["po_sbr_amp_floor_abs"]),
                    "po_sbr_amp_target_abs": float(comp["po_sbr_amp_target_abs"]),
                    "amp_abs": float(comp["amp_abs"]),
                    "range_amp_exponent": float(comp["range_amp_exponent"]),
                    "material_tag": str(comp["material_tag"]),
                    "reflection_order": int(comp["reflection_order"]),
                    "po_sbr_bounces": int(comp["po_sbr_bounces"]),
                    "po_sbr_rays_per_lambda": float(comp["po_sbr_rays_per_lambda"]),
                    "path_id_prefix": str(comp["path_id_prefix"]),
                }
                for comp in eqv["components"]
            ],
        },
        "requested_backends": selected_backends,
        "output_root": str(out_root),
        "results": results,
        "summary": summary,
    }

    out_summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Scene backend golden-path run completed.")
    print(f"  requested_backends: {selected_backends}")
    print(f"  executed_backends: {summary['executed_backends']}")
    print(f"  blocked_backends: {summary['blocked_backends']}")
    print(f"  failed_backends: {summary['failed_backends']}")
    print(f"  po_sbr_migration_status: {summary['po_sbr_migration_status']}")
    print(f"  output_summary_json: {out_summary_json}")

    if bool(args.strict_nonexecuted) and (summary["blocked_count"] > 0 or summary["failed_count"] > 0):
        sys.exit(2)


if __name__ == "__main__":
    main()

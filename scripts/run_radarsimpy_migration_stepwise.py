#!/usr/bin/env python3
import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from avxsim.adapters import to_radarsimpy_view
from avxsim.adc_pack_builder import load_adc_from_npz, reorder_adc_to_sctr
from avxsim.constants import C0
from avxsim.parity import compare_hybrid_estimation_payloads
from avxsim.radarsimpy_periodic_lock import DEFAULT_RADARSIMPY_PERIODIC_THRESHOLDS
from avxsim.runtime_coupling import detect_runtime_modules
from avxsim.scene_pipeline import run_object_scene_to_radar_map_json

DEFAULT_TX_POS_M = [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]]
DEFAULT_RX_POS_M = [
    [0.0, 0.00185, 0.0],
    [0.0, 0.0037, 0.0],
    [0.0, 0.00555, 0.0],
    [0.0, 0.0074, 0.0],
]
DEFAULT_CANDIDATE_BACKENDS: Tuple[str, ...] = (
    "analytic_targets",
    "sionna_rt",
    "po_sbr_rt",
)
SUPPORTED_CANDIDATE_BACKENDS = set(DEFAULT_CANDIDATE_BACKENDS)

DEFAULT_RADARSIMPY_RUNTIME_PROVIDER = (
    "avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths"
)
DEFAULT_SIONNA_RUNTIME_PROVIDER = (
    "avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba"
)
DEFAULT_PO_SBR_RUNTIME_PROVIDER = (
    "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run stepwise migration checks from radarsimpy_rt reference to replacement "
            "backends with RD/RA + RadarSimPy-view ADC parity metrics."
        )
    )
    p.add_argument("--output-root", required=True, help="Output root directory")
    p.add_argument("--output-summary-json", required=True, help="Output stepwise summary JSON path")
    p.add_argument("--scene-id-prefix", default="radarsimpy_migration_stepwise_v1", help="Scene id prefix")
    p.add_argument(
        "--candidate-backend",
        action="append",
        default=[],
        help=(
            "Candidate backend to compare (repeatable, comma-separated): "
            "analytic_targets,sionna_rt,po_sbr_rt. Default: all"
        ),
    )

    p.add_argument("--n-chirps", type=int, default=8, help="Number of chirps")
    p.add_argument("--samples-per-chirp", type=int, default=1024, help="ADC samples per chirp")
    p.add_argument("--fc-hz", type=float, default=77e9, help="Radar carrier frequency")
    p.add_argument("--slope-hz-per-s", type=float, default=20e12, help="FMCW slope")
    p.add_argument("--fs-hz", type=float, default=20e6, help="Sampling rate")
    p.add_argument("--nfft-doppler", type=int, default=64, help="Doppler FFT size")
    p.add_argument("--nfft-angle", type=int, default=32, help="Angle FFT size")
    p.add_argument(
        "--range-bin-limit",
        type=int,
        default=256,
        help="Maximum range bins kept after range FFT",
    )

    p.add_argument("--components-json", default=None, help="Optional component-list JSON path")
    p.add_argument("--target-range-m", type=float, default=25.0, help="Default one-way target range")
    p.add_argument("--target-az-deg", type=float, default=0.0, help="Default azimuth")
    p.add_argument("--target-el-deg", type=float, default=0.0, help="Default elevation")
    p.add_argument("--target-radial-velocity-mps", type=float, default=0.0, help="Default radial velocity")
    p.add_argument("--amp-abs", type=float, default=1.0, help="Default amplitude scale")
    p.add_argument(
        "--range-amp-exponent",
        type=float,
        default=2.0,
        help="Default amplitude range exponent",
    )
    p.add_argument("--material-tag", default="migration_target", help="Default material tag")
    p.add_argument("--reflection-order", type=int, default=1, help="Default reflection order")
    p.add_argument("--sionna-target-radius-m", type=float, default=0.5, help="Default Sionna sphere radius")
    p.add_argument("--po-sbr-alpha-deg", type=float, default=180.0, help="Default PO-SBR alpha")
    p.add_argument("--po-sbr-bounces", type=int, default=2, help="Default PO-SBR bounce count")
    p.add_argument(
        "--po-sbr-rays-per-lambda",
        type=float,
        default=3.0,
        help="Default PO-SBR rays-per-wavelength",
    )

    p.add_argument(
        "--radarsimpy-runtime-provider",
        default=DEFAULT_RADARSIMPY_RUNTIME_PROVIDER,
        help="Runtime provider for radarsimpy_rt reference",
    )
    p.add_argument(
        "--radarsimpy-runtime-required-modules",
        default="radarsimpy",
        help="CSV required modules for radarsimpy runtime provider",
    )
    p.add_argument(
        "--radarsimpy-simulation-mode",
        default="radarsimpy_adc",
        choices=("auto", "analytic_paths", "radarsimpy_adc"),
        help="radarsimpy runtime simulation mode (default: radarsimpy_adc)",
    )
    p.add_argument(
        "--radarsimpy-fallback-to-analytic-on-error",
        action="store_true",
        help="allow radarsimpy provider to fallback to analytic paths on simulation failure",
    )
    p.add_argument(
        "--radarsimpy-runtime-device",
        default="cpu",
        choices=("cpu", "gpu"),
        help="radarsimpy simulation device",
    )
    p.add_argument(
        "--sionna-runtime-provider",
        default=DEFAULT_SIONNA_RUNTIME_PROVIDER,
        help="Runtime provider for sionna_rt candidate",
    )
    p.add_argument(
        "--sionna-runtime-required-modules",
        default="",
        help="CSV required modules for sionna runtime provider",
    )
    p.add_argument(
        "--po-sbr-runtime-provider",
        default=DEFAULT_PO_SBR_RUNTIME_PROVIDER,
        help="Runtime provider for po_sbr_rt candidate",
    )
    p.add_argument(
        "--po-sbr-runtime-required-modules",
        default="",
        help="CSV required modules for po_sbr runtime provider",
    )
    p.add_argument(
        "--po-sbr-repo-root",
        default="external/PO-SBR-Python",
        help="PO-SBR repository root for default runtime provider",
    )
    p.add_argument(
        "--po-sbr-geometry-path",
        default="geometries/plate.obj",
        help="PO-SBR geometry path for default runtime provider",
    )
    p.add_argument(
        "--runtime-failure-policy",
        default="error",
        choices=("error", "use_static"),
        help="Runtime failure policy for runtime-based backends",
    )
    p.add_argument(
        "--require-runtime-provider-mode",
        action="store_true",
        help="Fail a step when runtime_resolution.mode is not runtime_provider",
    )
    p.add_argument(
        "--require-radarsimpy-simulation-used",
        action="store_true",
        help="Fail reference step when provider_runtime_info.simulation_used is not true",
    )
    p.add_argument(
        "--trial-free-tier-geometry",
        action="store_true",
        help="Use 1 TX / 1 RX geometry for free-tier RadarSimPy limits",
    )

    p.add_argument("--rdra-thresholds-json", default=None, help="Override JSON for RD/RA parity thresholds")
    p.add_argument(
        "--adc-view-thresholds-json",
        default=None,
        help="Override JSON for RadarSimPy-view ADC parity thresholds",
    )
    p.add_argument(
        "--parity-gain-normalization",
        default="complex_l2",
        choices=("none", "complex_l2"),
        help=(
            "Optional global gain normalization before RD/RA + ADC parity. "
            "complex_l2 scales candidate by least-squares complex gain."
        ),
    )
    p.add_argument(
        "--allow-failures",
        action="store_true",
        help="Return 0 even when migration status is blocked",
    )
    return p.parse_args()


def _parse_candidate_backends(items: Sequence[str]) -> List[str]:
    if len(items) == 0:
        return list(DEFAULT_CANDIDATE_BACKENDS)
    out: List[str] = []
    for raw in items:
        for token in str(raw).split(","):
            name = str(token).strip().lower()
            if name == "":
                continue
            if name not in SUPPORTED_CANDIDATE_BACKENDS:
                raise ValueError(
                    "unsupported candidate backend: "
                    f"{name} (supported: analytic_targets,sionna_rt,po_sbr_rt)"
                )
            if name not in out:
                out.append(name)
    if len(out) == 0:
        raise ValueError("at least one candidate backend must be selected")
    return out


def _parse_module_csv(raw: Optional[str]) -> List[str]:
    if raw is None:
        return []
    out: List[str] = []
    for token in str(raw).split(","):
        name = str(token).strip()
        if name == "":
            continue
        if name not in out:
            out.append(name)
    return out


def _load_thresholds(path: Optional[str]) -> Optional[Dict[str, float]]:
    if path is None:
        return None
    p = Path(path).expanduser().resolve()
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"threshold file must be object: {p}")
    out: Dict[str, float] = {}
    for key, value in payload.items():
        out[str(key)] = float(value)
    return out


def _resolve_component_defaults(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "range_m": float(args.target_range_m),
        "az_deg": float(args.target_az_deg),
        "el_deg": float(args.target_el_deg),
        "radial_velocity_mps": float(args.target_radial_velocity_mps),
        "amp_abs": float(args.amp_abs),
        "range_amp_exponent": float(args.range_amp_exponent),
        "material_tag": str(args.material_tag),
        "reflection_order": int(args.reflection_order),
        "path_id_prefix": "migration_target",
        "sionna_target_radius_m": float(args.sionna_target_radius_m),
        "po_sbr_alpha_deg": float(args.po_sbr_alpha_deg),
        "po_sbr_bounces": int(args.po_sbr_bounces),
        "po_sbr_rays_per_lambda": float(args.po_sbr_rays_per_lambda),
    }


def _load_components(args: argparse.Namespace) -> List[Dict[str, Any]]:
    defaults = _resolve_component_defaults(args)
    if args.components_json is None:
        return [_normalize_component({}, defaults=defaults, idx=0)]

    comp_path = Path(args.components_json).expanduser().resolve()
    payload = json.loads(comp_path.read_text(encoding="utf-8"))
    raw_rows: List[Any]
    if isinstance(payload, Mapping):
        rows = payload.get("components")
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise ValueError("components-json object must contain list key: components")
        raw_rows = list(rows)
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        raw_rows = list(payload)
    else:
        raise ValueError("components-json must be list or object with components list")

    if len(raw_rows) == 0:
        raise ValueError("components list must be non-empty")

    out: List[Dict[str, Any]] = []
    for idx, row in enumerate(raw_rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"components[{idx}] must be object")
        out.append(_normalize_component(row, defaults=defaults, idx=idx))
    return out


def _normalize_component(item: Mapping[str, Any], defaults: Mapping[str, Any], idx: int) -> Dict[str, Any]:
    range_m = float(item.get("range_m", item.get("target_range_m", defaults["range_m"])))
    if range_m <= 0.0:
        raise ValueError(f"components[{idx}].range_m must be > 0")

    amp_abs = float(item.get("amp_abs", defaults["amp_abs"]))
    if amp_abs < 0.0:
        raise ValueError(f"components[{idx}].amp_abs must be >= 0")

    range_amp_exponent = float(item.get("range_amp_exponent", defaults["range_amp_exponent"]))
    if range_amp_exponent < 0.0:
        raise ValueError(f"components[{idx}].range_amp_exponent must be >= 0")

    reflection_order = int(item.get("reflection_order", defaults["reflection_order"]))
    if reflection_order < 0:
        raise ValueError(f"components[{idx}].reflection_order must be >= 0")

    sionna_target_radius_m = float(
        item.get("sionna_target_radius_m", defaults["sionna_target_radius_m"])
    )
    if sionna_target_radius_m <= 0.0:
        raise ValueError(f"components[{idx}].sionna_target_radius_m must be > 0")

    po_sbr_bounces = int(item.get("po_sbr_bounces", defaults["po_sbr_bounces"]))
    if po_sbr_bounces < 0:
        raise ValueError(f"components[{idx}].po_sbr_bounces must be >= 0")

    po_sbr_rays_per_lambda = float(
        item.get("po_sbr_rays_per_lambda", defaults["po_sbr_rays_per_lambda"])
    )
    if po_sbr_rays_per_lambda <= 0.0:
        raise ValueError(f"components[{idx}].po_sbr_rays_per_lambda must be > 0")

    path_id_prefix = str(item.get("path_id_prefix", f"migration_target_{idx}"))
    if path_id_prefix.strip() == "":
        raise ValueError(f"components[{idx}].path_id_prefix must be non-empty")

    return {
        "range_m": range_m,
        "az_deg": float(item.get("az_deg", item.get("target_az_deg", defaults["az_deg"]))),
        "el_deg": float(item.get("el_deg", item.get("target_el_deg", defaults["el_deg"]))),
        "radial_velocity_mps": float(
            item.get("radial_velocity_mps", item.get("target_radial_velocity_mps", defaults["radial_velocity_mps"]))
        ),
        "amp_abs": amp_abs,
        "range_amp_exponent": range_amp_exponent,
        "material_tag": str(item.get("material_tag", defaults["material_tag"])),
        "reflection_order": reflection_order,
        "path_id_prefix": path_id_prefix,
        "sionna_target_radius_m": sionna_target_radius_m,
        "po_sbr_alpha_deg": float(item.get("po_sbr_alpha_deg", defaults["po_sbr_alpha_deg"])),
        "po_sbr_bounces": po_sbr_bounces,
        "po_sbr_rays_per_lambda": po_sbr_rays_per_lambda,
    }


def _dir_from_az_el_deg(az_deg: float, el_deg: float) -> np.ndarray:
    az = math.radians(float(az_deg))
    el = math.radians(float(el_deg))
    return np.asarray(
        [
            math.cos(el) * math.cos(az),
            math.cos(el) * math.sin(az),
            math.sin(el),
        ],
        dtype=np.float64,
    )


def _build_static_paths_payload(
    components: Sequence[Mapping[str, Any]],
    n_chirps: int,
    fc_hz: float,
    chirp_interval_s: float,
) -> Dict[str, Any]:
    lam = C0 / float(fc_hz)
    out: List[List[Dict[str, Any]]] = []
    for chirp_idx in range(int(n_chirps)):
        t = float(chirp_idx) * float(chirp_interval_s)
        chirp_paths: List[Dict[str, Any]] = []
        for comp_idx, comp in enumerate(components):
            range_k = max(1.0e-6, float(comp["range_m"]) + float(comp["radial_velocity_mps"]) * t)
            amp = float(comp["amp_abs"]) / (range_k ** max(float(comp["range_amp_exponent"]), 0.0))
            u = _dir_from_az_el_deg(float(comp["az_deg"]), float(comp["el_deg"]))
            doppler_hz = float(2.0 * float(comp["radial_velocity_mps"]) / lam)
            if len(components) == 1:
                path_id = f"{comp['path_id_prefix']}_c{chirp_idx:04d}"
            else:
                path_id = f"{comp['path_id_prefix']}_c{chirp_idx:04d}_t{comp_idx:02d}"
            chirp_paths.append(
                {
                    "delay_s": float(2.0 * range_k / C0),
                    "doppler_hz": doppler_hz,
                    "unit_direction": [float(u[0]), float(u[1]), float(u[2])],
                    "amp": float(amp),
                    "path_id": path_id,
                    "material_tag": str(comp["material_tag"]),
                    "reflection_order": int(comp["reflection_order"]),
                }
            )
        out.append(chirp_paths)
    return {"paths_by_chirp": out}


def _build_radar_payload(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "fc_hz": float(args.fc_hz),
        "slope_hz_per_s": float(args.slope_hz_per_s),
        "fs_hz": float(args.fs_hz),
        "samples_per_chirp": int(args.samples_per_chirp),
    }


def _build_map_config(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "nfft_range": int(args.samples_per_chirp),
        "nfft_doppler": int(args.nfft_doppler),
        "nfft_angle": int(args.nfft_angle),
        "range_bin_limit": int(min(int(args.samples_per_chirp // 2), int(args.range_bin_limit))),
    }


def _resolve_geometry(args: argparse.Namespace) -> Tuple[List[List[float]], List[List[float]]]:
    if bool(args.trial_free_tier_geometry):
        return (
            [[0.0, 0.0, 0.0]],
            [[0.0, 0.00185, 0.0]],
        )
    return (list(DEFAULT_TX_POS_M), list(DEFAULT_RX_POS_M))


def _build_reference_scene(
    args: argparse.Namespace,
    scene_id: str,
    radar_payload: Mapping[str, Any],
    map_cfg: Mapping[str, Any],
    static_payload: Mapping[str, Any],
    components: Sequence[Mapping[str, Any]],
    modules: Sequence[str],
    chirp_interval_s: float,
    tx_pos_m: Sequence[Sequence[float]],
    rx_pos_m: Sequence[Sequence[float]],
) -> Dict[str, Any]:
    targets = []
    for comp in components:
        targets.append(
            {
                "range_m": float(comp["range_m"]),
                "az_deg": float(comp["az_deg"]),
                "el_deg": float(comp["el_deg"]),
                "radial_velocity_mps": float(comp["radial_velocity_mps"]),
                "amp_scale": float(comp["amp_abs"]),
                "range_amp_exponent": float(comp["range_amp_exponent"]),
                "material_tag": str(comp["material_tag"]),
                "reflection_order": int(comp["reflection_order"]),
                "path_id_prefix": str(comp["path_id_prefix"]),
            }
        )

    return {
        "scene_id": scene_id,
        "backend": {
            "type": "radarsimpy_rt",
            "n_chirps": int(args.n_chirps),
            "tx_pos_m": [list(row) for row in tx_pos_m],
            "rx_pos_m": [list(row) for row in rx_pos_m],
            "runtime_provider": str(args.radarsimpy_runtime_provider),
            "runtime_required_modules": list(modules),
            "runtime_failure_policy": str(args.runtime_failure_policy),
            "runtime_input": {
                "chirp_interval_s": float(chirp_interval_s),
                "min_range_m": 1.0e-6,
                "targets": targets,
                "simulation_mode": str(args.radarsimpy_simulation_mode),
                "fallback_to_analytic_on_error": bool(args.radarsimpy_fallback_to_analytic_on_error),
                "device": str(args.radarsimpy_runtime_device),
            },
            "paths_payload": dict(static_payload),
            "noise_sigma": 0.0,
        },
        "radar": dict(radar_payload),
        "map_config": dict(map_cfg),
    }


def _build_analytic_scene(
    args: argparse.Namespace,
    scene_id: str,
    radar_payload: Mapping[str, Any],
    map_cfg: Mapping[str, Any],
    components: Sequence[Mapping[str, Any]],
    chirp_interval_s: float,
    tx_pos_m: Sequence[Sequence[float]],
    rx_pos_m: Sequence[Sequence[float]],
) -> Dict[str, Any]:
    targets = []
    for comp in components:
        targets.append(
            {
                "range_m": float(comp["range_m"]),
                "az_deg": float(comp["az_deg"]),
                "el_deg": float(comp["el_deg"]),
                "radial_velocity_mps": float(comp["radial_velocity_mps"]),
                "amp": float(comp["amp_abs"]),
                "range_amp_exponent": float(comp["range_amp_exponent"]),
                "material_tag": str(comp["material_tag"]),
                "reflection_order": int(comp["reflection_order"]),
                "path_id": str(comp["path_id_prefix"]),
            }
        )

    return {
        "scene_id": scene_id,
        "backend": {
            "type": "analytic_targets",
            "n_chirps": int(args.n_chirps),
            "tx_pos_m": [list(row) for row in tx_pos_m],
            "rx_pos_m": [list(row) for row in rx_pos_m],
            "chirp_interval_s": float(chirp_interval_s),
            "targets": targets,
            "noise_sigma": 0.0,
        },
        "radar": dict(radar_payload),
        "map_config": dict(map_cfg),
    }


def _build_sionna_scene(
    args: argparse.Namespace,
    scene_id: str,
    radar_payload: Mapping[str, Any],
    map_cfg: Mapping[str, Any],
    static_payload: Mapping[str, Any],
    components: Sequence[Mapping[str, Any]],
    modules: Sequence[str],
    chirp_interval_s: float,
    tx_pos_m: Sequence[Sequence[float]],
    rx_pos_m: Sequence[Sequence[float]],
) -> Dict[str, Any]:
    spheres = []
    for comp in components:
        radius = float(comp["sionna_target_radius_m"])
        direction = _dir_from_az_el_deg(float(comp["az_deg"]), float(comp["el_deg"]))
        # Mitsuba sphere intersections measure distance to the surface; shift center
        # so the resulting one-way intersection range matches the target range.
        center = direction * (float(comp["range_m"]) + radius)
        velocity = direction * float(comp["radial_velocity_mps"])
        spheres.append(
            {
                "center_m": [float(center[0]), float(center[1]), float(center[2])],
                "radius_m": radius,
                "velocity_mps": [float(velocity[0]), float(velocity[1]), float(velocity[2])],
                "amp": {"re": float(comp["amp_abs"]), "im": 0.0},
                "range_amp_exponent": float(comp["range_amp_exponent"]),
                "path_id_prefix": str(comp["path_id_prefix"]),
                "material_tag": str(comp["material_tag"]),
                "reflection_order": int(comp["reflection_order"]),
            }
        )

    return {
        "scene_id": scene_id,
        "backend": {
            "type": "sionna_rt",
            "n_chirps": int(args.n_chirps),
            "tx_pos_m": [list(row) for row in tx_pos_m],
            "rx_pos_m": [list(row) for row in rx_pos_m],
            "runtime_provider": str(args.sionna_runtime_provider),
            "runtime_required_modules": list(modules),
            "runtime_failure_policy": str(args.runtime_failure_policy),
            "runtime_input": {
                "chirp_interval_s": float(chirp_interval_s),
                "min_range_m": 1.0e-6,
                "ego_origin_m": [0.0, 0.0, 0.0],
                "spheres": spheres,
            },
            "paths_payload": dict(static_payload),
            "noise_sigma": 0.0,
        },
        "radar": dict(radar_payload),
        "map_config": dict(map_cfg),
    }


def _build_po_sbr_scene(
    args: argparse.Namespace,
    scene_id: str,
    radar_payload: Mapping[str, Any],
    map_cfg: Mapping[str, Any],
    static_payload: Mapping[str, Any],
    components: Sequence[Mapping[str, Any]],
    modules: Sequence[str],
    chirp_interval_s: float,
    tx_pos_m: Sequence[Sequence[float]],
    rx_pos_m: Sequence[Sequence[float]],
) -> Dict[str, Any]:
    po_components: List[Dict[str, Any]] = []
    for comp in components:
        range_m = float(comp["range_m"])
        amp_target_abs = float(comp["amp_abs"]) / (range_m ** max(float(comp["range_amp_exponent"]), 0.0))
        po_components.append(
            {
                "alpha_deg": float(comp["po_sbr_alpha_deg"]),
                "phi_deg": float(comp["az_deg"]),
                "theta_deg": float(90.0 - float(comp["el_deg"])),
                "phi_rate_deg_per_s": 0.0,
                "freq_hz": float(radar_payload["fc_hz"]),
                "rays_per_lambda": float(comp["po_sbr_rays_per_lambda"]),
                "bounces": int(comp["po_sbr_bounces"]),
                "radial_velocity_mps": float(comp["radial_velocity_mps"]),
                "amp_scale": {"re": 1.0, "im": 0.0},
                "amp_floor_abs": 0.0,
                "amp_target_abs": float(amp_target_abs),
                "material_tag": str(comp["material_tag"]),
                "reflection_order": int(comp["reflection_order"]),
                "min_range_m": float(range_m),
                "path_id_prefix": str(comp["path_id_prefix"]),
            }
        )

    return {
        "scene_id": scene_id,
        "backend": {
            "type": "po_sbr_rt",
            "n_chirps": int(args.n_chirps),
            "tx_pos_m": [list(row) for row in tx_pos_m],
            "rx_pos_m": [list(row) for row in rx_pos_m],
            "runtime_provider": str(args.po_sbr_runtime_provider),
            "runtime_required_modules": list(modules),
            "runtime_failure_policy": str(args.runtime_failure_policy),
            "runtime_input": {
                "po_sbr_repo_root": str(args.po_sbr_repo_root),
                "geometry_path": str(args.po_sbr_geometry_path),
                "chirp_interval_s": float(chirp_interval_s),
                "components": po_components,
            },
            "paths_payload": dict(static_payload),
            "noise_sigma": 0.0,
        },
        "radar": dict(radar_payload),
        "map_config": dict(map_cfg),
    }


def _load_radar_map_payload(radar_map_npz: Path) -> Dict[str, Any]:
    with np.load(str(radar_map_npz), allow_pickle=False) as payload:
        out: Dict[str, Any] = {
            "fx_dop_win": np.asarray(payload["fx_dop_win"]),
            "fx_ang": np.asarray(payload["fx_ang"]),
        }
        if "metadata_json" in payload:
            try:
                out["metadata_json"] = json.loads(str(payload["metadata_json"].tolist()))
            except Exception:
                out["metadata_json"] = str(payload["metadata_json"])
    return out


def _extract_runtime_resolution(radar_map_payload: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    meta = radar_map_payload.get("metadata_json")
    if not isinstance(meta, Mapping):
        return None
    runtime_resolution = meta.get("runtime_resolution")
    if not isinstance(runtime_resolution, Mapping):
        return None
    return dict(runtime_resolution)


def _load_adc_sctr(adc_cube_npz: Path) -> np.ndarray:
    adc_raw, _ = load_adc_from_npz(str(adc_cube_npz), adc_key="adc")
    return np.asarray(reorder_adc_to_sctr(adc_raw, adc_order="sctr"))


def _count_paths(path_list_json: Path) -> int:
    payload = json.loads(path_list_json.read_text(encoding="utf-8"))
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
        return 0
    count = 0
    for row in payload:
        if isinstance(row, Sequence) and not isinstance(row, (str, bytes)):
            count += len(row)
    return int(count)


def _run_scene(
    scene_payload: Mapping[str, Any],
    scene_json_path: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    scene_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    scene_json_path.write_text(json.dumps(dict(scene_payload), indent=2), encoding="utf-8")

    report: Dict[str, Any] = {
        "status": "blocked",
        "scene_json": str(scene_json_path),
        "output_dir": str(output_dir),
        "path_list_json": None,
        "adc_cube_npz": None,
        "radar_map_npz": None,
        "frame_count": 0,
        "path_count": 0,
        "runtime_resolution": None,
        "error": None,
    }

    try:
        run_out = run_object_scene_to_radar_map_json(
            scene_json_path=str(scene_json_path),
            output_dir=str(output_dir),
            run_hybrid_estimation=False,
        )
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        return report

    radar_map_npz = Path(str(run_out["radar_map_npz"])).expanduser().resolve()
    adc_cube_npz = Path(str(run_out["adc_cube_npz"])).expanduser().resolve()
    path_list_json = Path(str(run_out["path_list_json"])).expanduser().resolve()

    radar_map_payload = _load_radar_map_payload(radar_map_npz)
    runtime_resolution = _extract_runtime_resolution(radar_map_payload)
    adc_sctr = _load_adc_sctr(adc_cube_npz)

    report.update(
        {
            "status": "executed",
            "path_list_json": str(path_list_json),
            "adc_cube_npz": str(adc_cube_npz),
            "radar_map_npz": str(radar_map_npz),
            "frame_count": int(run_out.get("frame_count", 0)),
            "path_count": _count_paths(path_list_json),
            "runtime_resolution": runtime_resolution,
            "_radar_map_payload": radar_map_payload,
            "_adc_sctr": adc_sctr,
        }
    )
    return report


def _compute_adc_view_metrics(reference: np.ndarray, candidate: np.ndarray) -> Dict[str, float]:
    ref = np.asarray(reference, dtype=np.complex128)
    cand = np.asarray(candidate, dtype=np.complex128)

    eps = float(np.finfo(np.float64).tiny)
    diff = cand - ref
    ref_pow = np.abs(ref) ** 2
    cand_pow = np.abs(cand) ** 2

    view_nmse = float(np.mean(np.abs(diff) ** 2) / (np.mean(np.abs(ref) ** 2) + eps))
    power_nmse = float(np.mean((cand_pow - ref_pow) ** 2) / (np.mean(ref_pow**2) + eps))
    mean_abs_error = float(np.mean(np.abs(diff)))
    max_abs_error = float(np.max(np.abs(diff)))

    ref_flat = ref.reshape(-1)
    cand_flat = cand.reshape(-1)
    denom = float(np.linalg.norm(ref_flat) * np.linalg.norm(cand_flat) + eps)
    corr = np.vdot(ref_flat, cand_flat) / denom
    complex_corr_abs = float(np.abs(corr))

    return {
        "view_nmse": view_nmse,
        "power_nmse": power_nmse,
        "mean_abs_error": mean_abs_error,
        "max_abs_error": max_abs_error,
        "complex_corr_abs": complex_corr_abs,
    }


def _estimate_complex_l2_gain(reference: np.ndarray, candidate: np.ndarray) -> complex:
    ref = np.asarray(reference, dtype=np.complex128).reshape(-1)
    cand = np.asarray(candidate, dtype=np.complex128).reshape(-1)
    denom = np.vdot(cand, cand)
    if abs(denom) <= 1.0e-30:
        return complex(1.0, 0.0)
    gain = np.vdot(cand, ref) / denom
    return complex(gain)


def _apply_gain_to_radar_map_payload(
    radar_map_payload: Mapping[str, Any],
    gain: complex,
) -> Dict[str, Any]:
    power_scale = float(abs(complex(gain)) ** 2)
    out: Dict[str, Any] = {}
    for key, value in radar_map_payload.items():
        if key in ("fx_dop_win", "fx_ang"):
            out[str(key)] = np.asarray(value) * power_scale
        else:
            out[str(key)] = value
    return out


def _apply_metric_thresholds(metrics: Mapping[str, float], thresholds: Mapping[str, float]) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []
    for key, limit in thresholds.items():
        if key.endswith("_max"):
            metric_key = key[: -len("_max")]
            value = float(metrics.get(metric_key, 0.0))
            if value > float(limit):
                failures.append(
                    {
                        "metric": metric_key,
                        "value": value,
                        "limit": float(limit),
                        "mode": "max",
                    }
                )
        elif key.endswith("_min"):
            metric_key = key[: -len("_min")]
            value = float(metrics.get(metric_key, 0.0))
            if value < float(limit):
                failures.append(
                    {
                        "metric": metric_key,
                        "value": value,
                        "limit": float(limit),
                        "mode": "min",
                    }
                )
    return failures


def _compute_adc_view_parity(
    reference_adc_sctr: np.ndarray,
    candidate_adc_sctr: np.ndarray,
    thresholds_override: Optional[Mapping[str, float]],
) -> Dict[str, Any]:
    ref_view = np.asarray(to_radarsimpy_view(reference_adc_sctr), dtype=np.complex128)
    cand_view = np.asarray(to_radarsimpy_view(candidate_adc_sctr), dtype=np.complex128)
    if ref_view.shape != cand_view.shape:
        raise ValueError(f"adc view shape mismatch: {cand_view.shape} != {ref_view.shape}")

    thresholds = dict(DEFAULT_RADARSIMPY_PERIODIC_THRESHOLDS)
    if thresholds_override is not None:
        for key, value in thresholds_override.items():
            thresholds[str(key)] = float(value)

    metrics = _compute_adc_view_metrics(reference=ref_view, candidate=cand_view)
    failures = _apply_metric_thresholds(metrics=metrics, thresholds=thresholds)
    return {
        "pass": bool(len(failures) == 0),
        "metrics": metrics,
        "thresholds": thresholds,
        "failures": failures,
        "view_shape": [int(x) for x in ref_view.shape],
    }


def _strip_private_fields(payload: Mapping[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in payload.items():
        if str(key).startswith("_"):
            continue
        out[str(key)] = value
    return out


def _runtime_mode(report: Mapping[str, Any]) -> Optional[str]:
    runtime_resolution = report.get("runtime_resolution")
    if not isinstance(runtime_resolution, Mapping):
        return None
    mode = runtime_resolution.get("mode")
    if mode is None:
        return None
    return str(mode)


def main() -> None:
    args = parse_args()
    if int(args.n_chirps) <= 0:
        raise ValueError("--n-chirps must be > 0")
    if int(args.samples_per_chirp) <= 0:
        raise ValueError("--samples-per-chirp must be > 0")
    if float(args.fc_hz) <= 0.0:
        raise ValueError("--fc-hz must be > 0")
    if float(args.fs_hz) <= 0.0:
        raise ValueError("--fs-hz must be > 0")

    cwd = Path.cwd().resolve()
    output_root = Path(args.output_root).expanduser()
    output_root = (cwd / output_root).resolve() if not output_root.is_absolute() else output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    output_summary_json = Path(args.output_summary_json).expanduser()
    output_summary_json = (
        (cwd / output_summary_json).resolve()
        if not output_summary_json.is_absolute()
        else output_summary_json.resolve()
    )
    output_summary_json.parent.mkdir(parents=True, exist_ok=True)

    candidate_backends = _parse_candidate_backends(args.candidate_backend)
    components = _load_components(args)
    radar_payload = _build_radar_payload(args)
    map_cfg = _build_map_config(args)
    tx_pos_m, rx_pos_m = _resolve_geometry(args)
    chirp_interval_s = float(args.samples_per_chirp) / float(args.fs_hz)

    static_payload = _build_static_paths_payload(
        components=components,
        n_chirps=int(args.n_chirps),
        fc_hz=float(args.fc_hz),
        chirp_interval_s=float(chirp_interval_s),
    )

    radarsimpy_modules = _parse_module_csv(args.radarsimpy_runtime_required_modules)
    sionna_modules = _parse_module_csv(args.sionna_runtime_required_modules)
    po_sbr_modules = _parse_module_csv(args.po_sbr_runtime_required_modules)
    module_names: List[str] = []
    for name in [*radarsimpy_modules, *sionna_modules, *po_sbr_modules]:
        if name not in module_names:
            module_names.append(name)
    module_report = detect_runtime_modules(module_names)

    rdra_threshold_overrides = _load_thresholds(args.rdra_thresholds_json)
    adc_threshold_overrides = _load_thresholds(args.adc_view_thresholds_json)

    reference_scene = _build_reference_scene(
        args=args,
        scene_id=f"{args.scene_id_prefix}_reference_radarsimpy_rt",
        radar_payload=radar_payload,
        map_cfg=map_cfg,
        static_payload=static_payload,
        components=components,
        modules=radarsimpy_modules,
        chirp_interval_s=float(chirp_interval_s),
        tx_pos_m=tx_pos_m,
        rx_pos_m=rx_pos_m,
    )
    reference_report = _run_scene(
        scene_payload=reference_scene,
        scene_json_path=output_root / "step_0_reference" / "scene.json",
        output_dir=output_root / "step_0_reference" / "pipeline_outputs",
    )

    reference_gate_pass = bool(reference_report.get("status") == "executed")
    reference_blockers: List[str] = []
    if not reference_gate_pass:
        reference_blockers.append("reference_execution_failed")
    if args.require_runtime_provider_mode and reference_gate_pass:
        mode = _runtime_mode(reference_report)
        if mode != "runtime_provider":
            reference_gate_pass = False
            reference_blockers.append("reference_runtime_mode_not_runtime_provider")
    if args.require_radarsimpy_simulation_used and reference_gate_pass:
        runtime_resolution = reference_report.get("runtime_resolution")
        provider_info = {}
        if isinstance(runtime_resolution, Mapping):
            maybe = runtime_resolution.get("provider_runtime_info")
            if isinstance(maybe, Mapping):
                provider_info = dict(maybe)
        if bool(provider_info.get("simulation_used", False)) is not True:
            reference_gate_pass = False
            reference_blockers.append("reference_provider_simulation_not_used")

    reference_public = _strip_private_fields(reference_report)
    reference_public["step_id"] = "step_0_reference_capture"
    reference_public["backend"] = "radarsimpy_rt"
    reference_public["gate_pass"] = bool(reference_gate_pass)
    reference_public["gate_blockers"] = list(reference_blockers)

    candidate_steps: List[Dict[str, Any]] = []
    for idx, backend in enumerate(candidate_backends, start=1):
        step_id = f"step_{idx}_{backend}"
        step_root = output_root / step_id

        if backend == "analytic_targets":
            scene = _build_analytic_scene(
                args=args,
                scene_id=f"{args.scene_id_prefix}_{backend}",
                radar_payload=radar_payload,
                map_cfg=map_cfg,
                components=components,
                chirp_interval_s=float(chirp_interval_s),
                tx_pos_m=tx_pos_m,
                rx_pos_m=rx_pos_m,
            )
        elif backend == "sionna_rt":
            scene = _build_sionna_scene(
                args=args,
                scene_id=f"{args.scene_id_prefix}_{backend}",
                radar_payload=radar_payload,
                map_cfg=map_cfg,
                static_payload=static_payload,
                components=components,
                modules=sionna_modules,
                chirp_interval_s=float(chirp_interval_s),
                tx_pos_m=tx_pos_m,
                rx_pos_m=rx_pos_m,
            )
        elif backend == "po_sbr_rt":
            scene = _build_po_sbr_scene(
                args=args,
                scene_id=f"{args.scene_id_prefix}_{backend}",
                radar_payload=radar_payload,
                map_cfg=map_cfg,
                static_payload=static_payload,
                components=components,
                modules=po_sbr_modules,
                chirp_interval_s=float(chirp_interval_s),
                tx_pos_m=tx_pos_m,
                rx_pos_m=rx_pos_m,
            )
        else:
            raise ValueError(f"unsupported backend: {backend}")

        run_report = _run_scene(
            scene_payload=scene,
            scene_json_path=step_root / "scene.json",
            output_dir=step_root / "pipeline_outputs",
        )

        row = _strip_private_fields(run_report)
        row["step_id"] = step_id
        row["backend"] = backend
        row["status"] = str(run_report.get("status", "blocked"))
        row["rdra_parity"] = None
        row["adc_view_parity"] = None
        row["parity_pass"] = False
        row["parity_normalization"] = None
        row["gate_blockers"] = []

        if not reference_gate_pass:
            row["status"] = "skipped"
            row["gate_blockers"] = ["reference_not_ready"] + list(reference_blockers)
            candidate_steps.append(row)
            continue

        if row["status"] != "executed":
            row["gate_blockers"] = ["candidate_execution_failed"]
            candidate_steps.append(row)
            continue

        if args.require_runtime_provider_mode and backend in ("sionna_rt", "po_sbr_rt"):
            mode = _runtime_mode(run_report)
            if mode != "runtime_provider":
                row["gate_blockers"].append("candidate_runtime_mode_not_runtime_provider")

        try:
            ref_adc_sctr = np.asarray(reference_report["_adc_sctr"])
            cand_adc_sctr = np.asarray(run_report["_adc_sctr"])
            ref_view = np.asarray(to_radarsimpy_view(ref_adc_sctr), dtype=np.complex128)
            cand_view = np.asarray(to_radarsimpy_view(cand_adc_sctr), dtype=np.complex128)
            if ref_view.shape != cand_view.shape:
                raise ValueError(
                    f"adc view shape mismatch during normalization: {cand_view.shape} != {ref_view.shape}"
                )

            gain_mode = str(args.parity_gain_normalization).strip().lower()
            gain = complex(1.0, 0.0)
            if gain_mode == "complex_l2":
                gain = _estimate_complex_l2_gain(reference=ref_view, candidate=cand_view)
            elif gain_mode != "none":
                raise ValueError(f"unsupported --parity-gain-normalization: {gain_mode}")

            cand_adc_eval = cand_adc_sctr * gain
            cand_radar_map_eval = _apply_gain_to_radar_map_payload(
                radar_map_payload=run_report["_radar_map_payload"],
                gain=gain,
            )
            row["parity_normalization"] = {
                "mode": gain_mode,
                "gain_complex": {"re": float(gain.real), "im": float(gain.imag)},
                "gain_abs": float(abs(gain)),
                "gain_db": float(20.0 * np.log10(max(abs(gain), 1.0e-30))),
            }

            rdra_parity = compare_hybrid_estimation_payloads(
                reference=reference_report["_radar_map_payload"],
                candidate=cand_radar_map_eval,
                thresholds=rdra_threshold_overrides,
            )
            adc_view_parity = _compute_adc_view_parity(
                reference_adc_sctr=ref_adc_sctr,
                candidate_adc_sctr=cand_adc_eval,
                thresholds_override=adc_threshold_overrides,
            )
            row["rdra_parity"] = rdra_parity
            row["adc_view_parity"] = adc_view_parity
            row["parity_pass"] = bool(rdra_parity.get("pass", False) and adc_view_parity.get("pass", False))
        except Exception as exc:
            row["gate_blockers"].append(f"parity_compute_failed:{type(exc).__name__}:{exc}")
            row["parity_pass"] = False

        if len(row["gate_blockers"]) > 0:
            row["parity_pass"] = False
        row["status"] = "compared"
        candidate_steps.append(row)

    compared_steps = [row for row in candidate_steps if str(row.get("status", "")) == "compared"]
    compared_count = int(len(compared_steps))
    pass_count = int(sum(1 for row in compared_steps if bool(row.get("parity_pass", False))))
    fail_count = int(sum(1 for row in compared_steps if not bool(row.get("parity_pass", False))))
    blocked_count = int(len(candidate_steps) - compared_count)

    blockers: List[str] = []
    if not reference_gate_pass:
        blockers.extend(reference_blockers)
    for row in candidate_steps:
        backend = str(row.get("backend", ""))
        status = str(row.get("status", ""))
        if status != "compared":
            blockers.append(f"{backend}:not_compared")
            continue
        if not bool(row.get("parity_pass", False)):
            blockers.append(f"{backend}:parity_failed")

    migration_status = "ready" if len(blockers) == 0 else "blocked"

    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_root": str(output_root),
        "migration_status": migration_status,
        "reference_backend": "radarsimpy_rt",
        "requested_candidate_backends": candidate_backends,
        "components": components,
        "runtime_module_report": module_report,
        "threshold_overrides": {
            "rdra": rdra_threshold_overrides,
            "adc_view": adc_threshold_overrides,
        },
        "require_runtime_provider_mode": bool(args.require_runtime_provider_mode),
        "require_radarsimpy_simulation_used": bool(args.require_radarsimpy_simulation_used),
        "trial_free_tier_geometry": bool(args.trial_free_tier_geometry),
        "geometry": {
            "tx_pos_m": [list(row) for row in tx_pos_m],
            "rx_pos_m": [list(row) for row in rx_pos_m],
        },
        "reference": reference_public,
        "steps": candidate_steps,
        "summary": {
            "candidate_backend_count": int(len(candidate_backends)),
            "compared_count": compared_count,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "blocked_count": blocked_count,
            "reference_gate_pass": bool(reference_gate_pass),
            "blockers": blockers,
        },
    }

    output_summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("RadarSimPy migration stepwise run completed.")
    print(f"  migration_status: {migration_status}")
    print(f"  reference_status: {reference_public.get('status')}")
    print(f"  candidate_backend_count: {len(candidate_backends)}")
    print(f"  compared_count: {compared_count}")
    print(f"  pass_count: {pass_count}")
    print(f"  fail_count: {fail_count}")
    print(f"  blocked_count: {blocked_count}")
    print(f"  output_summary_json: {output_summary_json}")

    if (migration_status != "ready") and (not bool(args.allow_failures)):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

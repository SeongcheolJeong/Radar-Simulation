from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np

from .antenna_manifold_asset import ComplexManifoldAsset, load_complex_manifold_asset
from .constants import C0
from .types import Path, RadarConfig


def apply_radar_compensation(
    paths_by_chirp: Sequence[Sequence[Path]],
    radar: RadarConfig,
    chirp_interval_s: float,
    config: Optional[Mapping[str, Any]],
) -> Tuple[list, Dict[str, Any]]:
    cfg = _normalize_compensation_config(config)
    if not bool(cfg["enabled"]):
        return [list(row) for row in paths_by_chirp], {
            "enabled": False,
            "input_path_count": int(sum(len(row) for row in paths_by_chirp)),
            "output_path_count": int(sum(len(row) for row in paths_by_chirp)),
            "added_diffuse_path_count": 0,
            "added_clutter_path_count": 0,
            "seed": cfg["seed"],
            "manifold_asset_enabled": False,
            "manifold_asset_path": None,
            "manifold_asset_frequency_hz": None,
        }

    manifold_asset = _resolve_manifold_asset(cfg["manifold"])
    manifold_asset_path = None if manifold_asset is None else str(manifold_asset.source_path)
    manifold_freq_hz = None
    if bool(cfg["manifold"]["enabled"]):
        manifold_freq_hz = float(
            radar.fc_hz
            if cfg["manifold"]["asset_frequency_hz"] is None
            else cfg["manifold"]["asset_frequency_hz"]
        )

    rng = np.random.default_rng(cfg["seed"])
    n_chirps = int(len(paths_by_chirp))
    bandwidth_hz = abs(float(radar.slope_hz_per_s)) * (
        float(radar.samples_per_chirp) / max(float(radar.fs_hz), 1.0e-12)
    )
    out: list = []
    input_path_count = int(sum(len(row) for row in paths_by_chirp))
    diffuse_added = 0
    clutter_added = 0

    for chirp_idx, row in enumerate(paths_by_chirp):
        chirp_out = []
        for path_idx, path in enumerate(row):
            compensated = _compensate_path(
                path=path,
                cfg=cfg,
                bandwidth_hz=float(bandwidth_hz),
                manifold_asset=manifold_asset,
                manifold_frequency_hz=float(
                    radar.fc_hz if manifold_freq_hz is None else float(manifold_freq_hz)
                ),
            )
            chirp_out.append(compensated)

            diffuse_paths = _spawn_diffuse_paths(
                chirp_idx=chirp_idx,
                path_idx=path_idx,
                source_path=compensated,
                cfg=cfg,
                rng=rng,
            )
            diffuse_added += int(len(diffuse_paths))
            chirp_out.extend(diffuse_paths)

        clutter_paths = _spawn_clutter_paths(
            chirp_idx=chirp_idx,
            cfg=cfg,
            rng=rng,
        )
        clutter_added += int(len(clutter_paths))
        chirp_out.extend(clutter_paths)
        out.append(chirp_out)

    output_path_count = int(sum(len(row) for row in out))
    return out, {
        "enabled": True,
        "seed": cfg["seed"],
        "chirp_interval_s": float(chirp_interval_s),
        "input_path_count": int(input_path_count),
        "output_path_count": int(output_path_count),
        "added_diffuse_path_count": int(diffuse_added),
        "added_clutter_path_count": int(clutter_added),
        "wideband_enabled": bool(cfg["wideband"]["enabled"]),
        "manifold_enabled": bool(cfg["manifold"]["enabled"]),
        "manifold_asset_enabled": bool(manifold_asset is not None),
        "manifold_asset_path": manifold_asset_path,
        "manifold_asset_frequency_hz": manifold_freq_hz,
        "manifold_asset_gain_scale": float(cfg["manifold"]["asset_gain_scale"]),
        "diffuse_enabled": bool(cfg["diffuse"]["enabled"]),
        "clutter_enabled": bool(cfg["clutter"]["enabled"]),
        "clutter_paths_per_chirp": int(cfg["clutter"]["paths_per_chirp"]),
        "diffuse_paths_per_specular": int(cfg["diffuse"]["paths_per_specular"]),
    }


def _compensate_path(
    path: Path,
    cfg: Mapping[str, Any],
    bandwidth_hz: float,
    manifold_asset: Optional[ComplexManifoldAsset],
    manifold_frequency_hz: float,
) -> Path:
    model = _material_model(cfg=cfg, material_tag=path.material_tag)
    az_deg, el_deg = _direction_to_az_el(path.unit_direction)
    reflection_order = int(path.reflection_order if path.reflection_order is not None else 1)

    rcs_scale_linear = max(float(model["rcs_scale_linear"]), 0.0)
    reflectivity = max(float(model["reflectivity"]), 0.0)
    reflection_decay = max(float(model["reflection_decay"]), 0.0)
    order_gain = reflection_decay ** max(reflection_order - 1, 0)
    gain = complex(
        np.sqrt(max(rcs_scale_linear, 0.0)) * np.sqrt(max(reflectivity, 0.0)) * order_gain
    )

    if bool(cfg["wideband"]["enabled"]):
        slope_db_per_ghz = float(model["wideband_slope_db_per_ghz"])
        delta_ghz = 0.5 * float(bandwidth_hz) / 1.0e9
        mag = 10.0 ** ((slope_db_per_ghz * delta_ghz) / 20.0)
        phase_weight = float(cfg["wideband"]["phase_weight"])
        phase = np.exp(1j * 2.0 * np.pi * phase_weight * 0.5 * float(bandwidth_hz) * float(path.delay_s))
        gain *= complex(mag) * complex(phase)

    if bool(cfg["manifold"]["enabled"]):
        manifold = cfg["manifold"]
        if manifold_asset is not None:
            tx_pol = manifold["asset_tx_pol_weights"]
            rx_pol = manifold["asset_rx_pol_weights"]
            gain_asset = manifold_asset.monostatic_gain_from_azel(
                frequency_hz=float(manifold_frequency_hz),
                az_deg=float(az_deg),
                el_deg=float(el_deg),
                tx_pol_weights=tx_pol,
                rx_pol_weights=rx_pol,
            )
            gain *= complex(gain_asset) * complex(float(manifold["asset_gain_scale"]))
        mag_db = (
            float(manifold["mag_db_bias"])
            + float(manifold["mag_db_per_abs_az_deg"]) * abs(float(az_deg))
            + float(manifold["mag_db_per_abs_el_deg"]) * abs(float(el_deg))
        )
        phase_deg = (
            float(manifold["phase_deg_bias"])
            + float(manifold["phase_deg_per_az_deg"]) * float(az_deg)
            + float(manifold["phase_deg_per_el_deg"]) * float(el_deg)
            + float(manifold["phase_deg_per_reflection_order"]) * float(max(reflection_order - 1, 0))
        )
        gain *= complex(10.0 ** (mag_db / 20.0)) * np.exp(1j * np.deg2rad(phase_deg))

    path_id = path.path_id if path.path_id is not None else "comp_path"
    material_tag = path.material_tag if path.material_tag is not None else "default_material"
    return Path(
        delay_s=float(path.delay_s),
        doppler_hz=float(path.doppler_hz),
        unit_direction=tuple(float(x) for x in path.unit_direction),
        amp=complex(path.amp) * complex(gain),
        pol_matrix=path.pol_matrix,
        path_id=str(path_id),
        material_tag=str(material_tag),
        reflection_order=int(reflection_order),
    )


def _spawn_diffuse_paths(
    chirp_idx: int,
    path_idx: int,
    source_path: Path,
    cfg: Mapping[str, Any],
    rng: np.random.Generator,
) -> list:
    diffuse = cfg["diffuse"]
    if (not bool(diffuse["enabled"])) or int(diffuse["paths_per_specular"]) <= 0:
        return []

    out = []
    count = int(diffuse["paths_per_specular"])
    amp_ratio = max(float(diffuse["amp_ratio"]), 0.0)
    delay_jitter_std = max(float(diffuse["delay_jitter_std"]), 0.0)
    doppler_sigma_hz = max(float(diffuse["doppler_sigma_hz"]), 0.0)
    direction_sigma_deg = max(float(diffuse["direction_sigma_deg"]), 0.0)

    base_path_id = (
        str(source_path.path_id)
        if source_path.path_id is not None
        else f"comp_path_c{chirp_idx:04d}_p{path_idx:04d}"
    )
    base_order = int(source_path.reflection_order if source_path.reflection_order is not None else 1)
    base_material = (
        str(source_path.material_tag) if source_path.material_tag is not None else "default_material"
    )

    for j in range(count):
        delay_scale = 1.0 + float(rng.normal(0.0, delay_jitter_std))
        delay_s = max(float(source_path.delay_s) * delay_scale, 1.0e-12)
        doppler_hz = float(source_path.doppler_hz) + float(rng.normal(0.0, doppler_sigma_hz))
        unit_direction = _perturb_direction(
            unit_direction=source_path.unit_direction,
            sigma_deg=direction_sigma_deg,
            rng=rng,
        )
        random_phase = np.exp(1j * rng.uniform(-np.pi, np.pi))
        amp = (
            complex(source_path.amp)
            * (amp_ratio / max(float(np.sqrt(count)), 1.0))
            * complex(random_phase)
        )
        out.append(
            Path(
                delay_s=float(delay_s),
                doppler_hz=float(doppler_hz),
                unit_direction=unit_direction,
                amp=complex(amp),
                pol_matrix=source_path.pol_matrix,
                path_id=f"{base_path_id}_df{j:02d}",
                material_tag=base_material,
                reflection_order=int(base_order),
            )
        )
    return out


def _spawn_clutter_paths(
    chirp_idx: int,
    cfg: Mapping[str, Any],
    rng: np.random.Generator,
) -> list:
    clutter = cfg["clutter"]
    if (not bool(clutter["enabled"])) or int(clutter["paths_per_chirp"]) <= 0:
        return []

    count = int(clutter["paths_per_chirp"])
    range_min_m = max(float(clutter["range_min_m"]), 1.0e-6)
    range_max_m = max(float(clutter["range_max_m"]), range_min_m + 1.0e-6)
    az_min_deg = float(clutter["az_min_deg"])
    az_max_deg = float(clutter["az_max_deg"])
    el_mean_deg = float(clutter["el_mean_deg"])
    el_sigma_deg = max(float(clutter["el_sigma_deg"]), 0.0)
    doppler_sigma_hz = max(float(clutter["doppler_sigma_hz"]), 0.0)
    amp_abs = max(float(clutter["amp_abs"]), 0.0)
    amp_db_sigma = max(float(clutter["amp_db_sigma"]), 0.0)
    material_tag = str(clutter["material_tag"])
    reflection_order = int(clutter["reflection_order"])

    out = []
    for j in range(count):
        range_m = float(rng.uniform(range_min_m, range_max_m))
        delay_s = max(2.0 * range_m / C0, 1.0e-12)
        az_deg = float(rng.uniform(az_min_deg, az_max_deg))
        el_deg = float(rng.normal(el_mean_deg, el_sigma_deg))
        unit_direction = _az_el_to_direction(az_deg=az_deg, el_deg=el_deg)

        doppler_hz = float(rng.normal(0.0, doppler_sigma_hz))

        amp_scale_db = float(rng.normal(0.0, amp_db_sigma))
        amp_mag = float(amp_abs * (10.0 ** (amp_scale_db / 20.0)))
        phase = np.exp(1j * rng.uniform(-np.pi, np.pi))

        out.append(
            Path(
                delay_s=float(delay_s),
                doppler_hz=float(doppler_hz),
                unit_direction=unit_direction,
                amp=complex(amp_mag) * complex(phase),
                pol_matrix=None,
                path_id=f"clutter_c{chirp_idx:04d}_k{j:03d}",
                material_tag=material_tag,
                reflection_order=int(reflection_order),
            )
        )
    return out


def _material_model(cfg: Mapping[str, Any], material_tag: Optional[str]) -> Mapping[str, Any]:
    models = cfg["material_models"]
    tag = "default_material" if material_tag is None else str(material_tag)
    if tag in models:
        return models[tag]
    return cfg["default_material_model"]


def _normalize_compensation_config(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    raw: MutableMapping[str, Any]
    if config is None:
        raw = {}
    elif isinstance(config, Mapping):
        raw = dict(config)
    else:
        raise ValueError("radar compensation config must be object")

    enabled = bool(raw.get("enabled", False))
    seed_value = raw.get("random_seed")
    seed = None if seed_value is None else int(seed_value)

    default_model = _normalize_material_model(raw.get("default_material_model", {}))
    material_models_raw = raw.get("material_models", {})
    material_models: Dict[str, Dict[str, float]] = {}
    if isinstance(material_models_raw, Mapping):
        for key, value in material_models_raw.items():
            material_models[str(key)] = _normalize_material_model(value)
    else:
        raise ValueError("radar_compensation.material_models must be object map")

    manifold_raw = raw.get("manifold", {})
    if not isinstance(manifold_raw, Mapping):
        raise ValueError("radar_compensation.manifold must be object")
    asset_path = _opt_str(
        manifold_raw.get("asset_path", manifold_raw.get("asset_npz", manifold_raw.get("asset_h5")))
    )
    asset_frequency_hz = _opt_float(manifold_raw.get("asset_frequency_hz"))
    manifold = {
        "enabled": bool(manifold_raw.get("enabled", False)),
        "mag_db_bias": float(manifold_raw.get("mag_db_bias", 0.0)),
        "mag_db_per_abs_az_deg": float(manifold_raw.get("mag_db_per_abs_az_deg", 0.0)),
        "mag_db_per_abs_el_deg": float(manifold_raw.get("mag_db_per_abs_el_deg", 0.0)),
        "phase_deg_bias": float(manifold_raw.get("phase_deg_bias", 0.0)),
        "phase_deg_per_az_deg": float(manifold_raw.get("phase_deg_per_az_deg", 0.0)),
        "phase_deg_per_el_deg": float(manifold_raw.get("phase_deg_per_el_deg", 0.0)),
        "phase_deg_per_reflection_order": float(
            manifold_raw.get("phase_deg_per_reflection_order", 0.0)
        ),
        "asset_path": asset_path,
        "asset_frequency_hz": asset_frequency_hz,
        "asset_gain_scale": float(manifold_raw.get("asset_gain_scale", 1.0)),
        "asset_tx_pol_weights": _normalize_pol_weights(
            manifold_raw.get("asset_tx_pol_weights"),
            key_name="radar_compensation.manifold.asset_tx_pol_weights",
        ),
        "asset_rx_pol_weights": _normalize_pol_weights(
            manifold_raw.get("asset_rx_pol_weights"),
            key_name="radar_compensation.manifold.asset_rx_pol_weights",
        ),
    }
    if float(manifold["asset_gain_scale"]) < 0.0:
        raise ValueError("radar_compensation.manifold.asset_gain_scale must be >= 0")
    if asset_frequency_hz is not None and float(asset_frequency_hz) <= 0.0:
        raise ValueError("radar_compensation.manifold.asset_frequency_hz must be > 0")

    wideband_raw = raw.get("wideband", {})
    if not isinstance(wideband_raw, Mapping):
        raise ValueError("radar_compensation.wideband must be object")
    wideband = {
        "enabled": bool(wideband_raw.get("enabled", True)),
        "phase_weight": float(wideband_raw.get("phase_weight", 1.0)),
    }

    diffuse_raw = raw.get("diffuse", {})
    if not isinstance(diffuse_raw, Mapping):
        raise ValueError("radar_compensation.diffuse must be object")
    diffuse = {
        "enabled": bool(diffuse_raw.get("enabled", False)),
        "paths_per_specular": int(diffuse_raw.get("paths_per_specular", 0)),
        "amp_ratio": float(diffuse_raw.get("amp_ratio", 0.15)),
        "delay_jitter_std": float(diffuse_raw.get("delay_jitter_std", 0.01)),
        "doppler_sigma_hz": float(diffuse_raw.get("doppler_sigma_hz", 2.0)),
        "direction_sigma_deg": float(diffuse_raw.get("direction_sigma_deg", 5.0)),
    }
    if int(diffuse["paths_per_specular"]) < 0:
        raise ValueError("radar_compensation.diffuse.paths_per_specular must be >= 0")

    clutter_raw = raw.get("clutter", {})
    if not isinstance(clutter_raw, Mapping):
        raise ValueError("radar_compensation.clutter must be object")
    clutter = {
        "enabled": bool(clutter_raw.get("enabled", False)),
        "paths_per_chirp": int(clutter_raw.get("paths_per_chirp", 0)),
        "range_min_m": float(clutter_raw.get("range_min_m", 3.0)),
        "range_max_m": float(clutter_raw.get("range_max_m", 80.0)),
        "az_min_deg": float(clutter_raw.get("az_min_deg", -60.0)),
        "az_max_deg": float(clutter_raw.get("az_max_deg", 60.0)),
        "el_mean_deg": float(clutter_raw.get("el_mean_deg", 0.0)),
        "el_sigma_deg": float(clutter_raw.get("el_sigma_deg", 2.0)),
        "doppler_sigma_hz": float(clutter_raw.get("doppler_sigma_hz", 30.0)),
        "amp_abs": float(clutter_raw.get("amp_abs", 2.0e-4)),
        "amp_db_sigma": float(clutter_raw.get("amp_db_sigma", 3.0)),
        "material_tag": str(clutter_raw.get("material_tag", "clutter")),
        "reflection_order": int(clutter_raw.get("reflection_order", 1)),
    }
    if int(clutter["paths_per_chirp"]) < 0:
        raise ValueError("radar_compensation.clutter.paths_per_chirp must be >= 0")
    if int(clutter["reflection_order"]) < 0:
        raise ValueError("radar_compensation.clutter.reflection_order must be >= 0")
    if float(clutter["range_max_m"]) < float(clutter["range_min_m"]):
        raise ValueError("radar_compensation.clutter.range_max_m must be >= range_min_m")
    if float(clutter["az_max_deg"]) < float(clutter["az_min_deg"]):
        raise ValueError("radar_compensation.clutter.az_max_deg must be >= az_min_deg")

    return {
        "enabled": bool(enabled),
        "seed": seed,
        "default_material_model": default_model,
        "material_models": material_models,
        "manifold": manifold,
        "wideband": wideband,
        "diffuse": diffuse,
        "clutter": clutter,
    }


def _resolve_manifold_asset(manifold: Mapping[str, Any]) -> Optional[ComplexManifoldAsset]:
    if not bool(manifold.get("enabled", False)):
        return None
    asset_path = _opt_str(manifold.get("asset_path"))
    if asset_path is None:
        return None
    return load_complex_manifold_asset(asset_path)


def _normalize_material_model(value: Any) -> Dict[str, float]:
    if value is None:
        src = {}
    elif isinstance(value, Mapping):
        src = dict(value)
    else:
        raise ValueError("material model must be object")
    return {
        "reflectivity": float(src.get("reflectivity", 1.0)),
        "rcs_scale_linear": float(src.get("rcs_scale_linear", 1.0)),
        "reflection_decay": float(src.get("reflection_decay", 1.0)),
        "wideband_slope_db_per_ghz": float(src.get("wideband_slope_db_per_ghz", 0.0)),
    }


def _normalize_pol_weights(value: Any, key_name: str) -> Tuple[complex, complex]:
    if value is None:
        return (1.0 + 0.0j, 0.0 + 0.0j)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{key_name} must be length-2 sequence when provided")
    arr = np.asarray(list(value), dtype=np.complex128).reshape(-1)
    if arr.size != 2:
        raise ValueError(f"{key_name} must be length 2")
    return complex(arr[0]), complex(arr[1])


def _opt_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return None if text == "" else text


def _opt_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    out = float(value)
    if not np.isfinite(out):
        raise ValueError("float value must be finite")
    return float(out)


def _direction_to_az_el(unit_direction: Sequence[float]) -> Tuple[float, float]:
    ux = float(unit_direction[0])
    uy = float(unit_direction[1])
    uz = float(unit_direction[2])
    norm = float(np.sqrt(ux * ux + uy * uy + uz * uz))
    if norm <= 0.0:
        raise ValueError("unit_direction must be non-zero")
    ux /= norm
    uy /= norm
    uz /= norm
    az = float(np.degrees(np.arctan2(uy, ux)))
    el = float(np.degrees(np.arcsin(np.clip(uz, -1.0, 1.0))))
    return az, el


def _az_el_to_direction(az_deg: float, el_deg: float) -> Tuple[float, float, float]:
    az = np.deg2rad(float(az_deg))
    el = np.deg2rad(float(el_deg))
    ux = float(np.cos(el) * np.cos(az))
    uy = float(np.cos(el) * np.sin(az))
    uz = float(np.sin(el))
    norm = float(np.sqrt(ux * ux + uy * uy + uz * uz))
    if norm <= 0.0:
        return (1.0, 0.0, 0.0)
    return (ux / norm, uy / norm, uz / norm)


def _perturb_direction(
    unit_direction: Sequence[float],
    sigma_deg: float,
    rng: np.random.Generator,
) -> Tuple[float, float, float]:
    az_deg, el_deg = _direction_to_az_el(unit_direction)
    az = float(az_deg + rng.normal(0.0, sigma_deg))
    el = float(el_deg + rng.normal(0.0, sigma_deg))
    return _az_el_to_direction(az_deg=az, el_deg=el)

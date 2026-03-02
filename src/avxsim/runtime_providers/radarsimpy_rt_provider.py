from __future__ import annotations

import math
from types import ModuleType
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np

from ..constants import C0
from .. import radarsimpy_api as rs_api


def generate_radarsimpy_like_paths(context: Mapping[str, Any]) -> Dict[str, Any]:
    n_chirps = int(context.get("n_chirps", 1))
    if n_chirps <= 0:
        raise ValueError("context.n_chirps must be positive")

    fc_hz = float(context.get("fc_hz", 77e9))
    if fc_hz <= 0.0:
        raise ValueError("context.fc_hz must be > 0")

    module = _import_radarsimpy_module()
    runtime_input = _as_obj(context, "runtime_input", required=False)
    chirp_interval_s = _resolve_chirp_interval_s(context=context, runtime_input=runtime_input)
    min_range_m = max(float(runtime_input.get("min_range_m", 1.0e-6)), 1.0e-6)
    lam = C0 / fc_hz
    targets = _resolve_targets(runtime_input=runtime_input)

    paths_by_chirp = _generate_analytic_paths_by_chirp(
        targets=targets,
        n_chirps=n_chirps,
        chirp_interval_s=chirp_interval_s,
        min_range_m=min_range_m,
        lam=lam,
    )

    simulation_mode = str(runtime_input.get("simulation_mode", "auto")).strip().lower()
    if simulation_mode not in ("auto", "analytic_paths", "radarsimpy_adc"):
        raise ValueError("runtime_input.simulation_mode must be auto, analytic_paths, or radarsimpy_adc")

    runtime_info: Dict[str, Any] = {
        "module_name": str(getattr(module, "__name__", "radarsimpy")),
        "module_version": str(getattr(module, "__version__", "unknown")),
        "generator": "analytic_targets_with_optional_radarsimpy_adc",
        "simulation_mode": simulation_mode,
    }
    if simulation_mode == "analytic_paths":
        runtime_info["simulation_used"] = False
        runtime_info["simulation_reason"] = "explicit_analytic_mode"
        return {
            "paths_by_chirp": paths_by_chirp,
            "provider_runtime_info": runtime_info,
        }

    has_sim_api = _has_radarsimpy_sim_api(module)
    if not has_sim_api:
        if simulation_mode == "radarsimpy_adc":
            raise RuntimeError("radarsimpy module does not expose Radar/Transmitter/Receiver/sim_radar")
        runtime_info["simulation_used"] = False
        runtime_info["simulation_reason"] = "sim_api_not_available"
        return {
            "paths_by_chirp": paths_by_chirp,
            "provider_runtime_info": runtime_info,
        }

    fallback_on_error = bool(runtime_input.get("fallback_to_analytic_on_error", False))
    try:
        adc_sctr, sim_info = _simulate_adc_with_radarsimpy(
            context=context,
            runtime_input=runtime_input,
            targets=targets,
            n_chirps=n_chirps,
            chirp_interval_s=chirp_interval_s,
            min_range_m=min_range_m,
        )
        runtime_info.update(sim_info)
        runtime_info["simulation_used"] = True
        return {
            "paths_by_chirp": paths_by_chirp,
            "adc_sctr": adc_sctr,
            "provider_runtime_info": runtime_info,
        }
    except Exception as exc:
        if (simulation_mode == "radarsimpy_adc") or (not fallback_on_error):
            raise
        runtime_info["simulation_used"] = False
        runtime_info["simulation_reason"] = "simulation_failed_fallback_analytic"
        runtime_info["simulation_error"] = f"{type(exc).__name__}: {exc}"
        return {
            "paths_by_chirp": paths_by_chirp,
            "provider_runtime_info": runtime_info,
        }


def _generate_analytic_paths_by_chirp(
    targets: Sequence[Mapping[str, Any]],
    n_chirps: int,
    chirp_interval_s: float,
    min_range_m: float,
    lam: float,
) -> List[List[Dict[str, Any]]]:
    out: List[List[Dict[str, Any]]] = []
    n_targets = len(targets)
    for chirp_idx in range(int(n_chirps)):
        t = float(chirp_idx) * float(chirp_interval_s)
        chirp_paths: List[Dict[str, Any]] = []
        for target_idx, target in enumerate(targets):
            range_k = max(min_range_m, float(target["range_m"]) + float(target["radial_velocity_mps"]) * t)
            az_rad = math.radians(float(target["az_deg"]))
            el_rad = math.radians(float(target["el_deg"]))
            ux = math.cos(el_rad) * math.cos(az_rad)
            uy = math.cos(el_rad) * math.sin(az_rad)
            uz = math.sin(el_rad)

            amp_scale = complex(target["amp_scale"])
            amp = amp_scale / (range_k ** max(float(target["range_amp_exponent"]), 0.0))
            tau = float(2.0 * range_k / C0)
            doppler_hz = float(2.0 * float(target["radial_velocity_mps"]) / lam)
            prefix = str(target["path_id_prefix"])
            path_id = (
                f"{prefix}_c{int(chirp_idx):04d}"
                if n_targets == 1
                else f"{prefix}_c{int(chirp_idx):04d}_t{int(target_idx):02d}"
            )
            chirp_paths.append(
                {
                    "delay_s": tau,
                    "doppler_hz": doppler_hz,
                    "unit_direction": [float(ux), float(uy), float(uz)],
                    "amp_complex": {"re": float(amp.real), "im": float(amp.imag)},
                    "path_id": path_id,
                    "material_tag": str(target["material_tag"]),
                    "reflection_order": int(target["reflection_order"]),
                }
            )
        out.append(chirp_paths)
    return out


def _simulate_adc_with_radarsimpy(
    context: Mapping[str, Any],
    runtime_input: Mapping[str, Any],
    targets: Sequence[Mapping[str, Any]],
    n_chirps: int,
    chirp_interval_s: float,
    min_range_m: float,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    backend = _as_obj(context, "backend", required=False)
    radar = _as_obj(context, "radar", required=False)
    tx_pos = _resolve_positions_3d(backend.get("tx_pos_m"), "backend.tx_pos_m")
    rx_pos = _resolve_positions_3d(backend.get("rx_pos_m"), "backend.rx_pos_m")
    n_tx = int(tx_pos.shape[0])
    n_rx = int(rx_pos.shape[0])

    fc_hz = float(context.get("fc_hz", radar.get("fc_hz", 77e9)))
    fs_hz = float(radar.get("fs_hz", 20e6))
    if fs_hz <= 0.0:
        raise ValueError("context.radar.fs_hz must be > 0")
    samples_per_chirp = int(radar.get("samples_per_chirp", int(round(chirp_interval_s * fs_hz))))
    if samples_per_chirp <= 0:
        raise ValueError("context.radar.samples_per_chirp must be positive")
    slope_hz_per_s = float(radar.get("slope_hz_per_s", 0.0))
    f_start_hz = float(runtime_input.get("f_start_hz", fc_hz))
    f_stop_hz = float(runtime_input.get("f_stop_hz", f_start_hz + slope_hz_per_s * chirp_interval_s))

    tx_schedule = _resolve_runtime_tx_schedule(
        runtime_input=runtime_input,
        backend=backend,
        n_chirps=int(n_chirps),
        n_tx=int(n_tx),
    )
    tx_channels = _build_tx_channels_for_sim(
        tx_pos=tx_pos,
        tx_schedule=tx_schedule,
        apply_tdm_schedule=bool(runtime_input.get("apply_tdm_schedule", True)),
    )
    rx_channels = [{"location": [float(x), float(y), float(z)]} for x, y, z in rx_pos.tolist()]

    tx = rs_api.Transmitter(
        f=[float(f_start_hz), float(f_stop_hz)],
        t=[0.0, float(chirp_interval_s)],
        tx_power=float(runtime_input.get("tx_power_dbm", 0.0)),
        pulses=int(n_chirps),
        prp=float(runtime_input.get("prp_s", chirp_interval_s)),
        channels=tx_channels,
    )
    rx = rs_api.Receiver(
        fs=float(fs_hz),
        noise_figure=float(runtime_input.get("noise_figure_db", 0.0)),
        rf_gain=float(runtime_input.get("rf_gain_db", 0.0)),
        load_resistor=float(runtime_input.get("load_resistor_ohm", 500.0)),
        baseband_gain=float(runtime_input.get("baseband_gain_db", 0.0)),
        bb_type=str(runtime_input.get("bb_type", "complex")),
        channels=rx_channels,
    )
    radar_obj = rs_api.Radar(
        transmitter=tx,
        receiver=rx,
        seed=_opt_int(runtime_input.get("seed")),
    )

    point_targets = _build_sim_point_targets(
        targets=targets,
        min_range_m=float(min_range_m),
    )
    sim_out = rs_api.sim_radar(
        radar_obj,
        point_targets,
        frame_time=runtime_input.get("frame_time"),
        density=float(runtime_input.get("density", 1.0)),
        level=_opt_str(runtime_input.get("level")),
        interf=None,
        ray_filter=_resolve_optional_ray_filter(runtime_input.get("ray_filter")),
        back_propagating=bool(runtime_input.get("back_propagating", False)),
        device=str(runtime_input.get("device", "cpu")),
        log_path=_opt_str(runtime_input.get("log_path")),
        debug=bool(runtime_input.get("debug", False)),
    )

    baseband = np.asarray(sim_out.get("baseband"))
    adc_sctr = _convert_sim_baseband_to_adc_sctr(
        baseband=baseband,
        n_tx=int(n_tx),
        n_rx=int(n_rx),
        n_chirps=int(n_chirps),
        samples_per_chirp=int(samples_per_chirp),
        tx_schedule=tx_schedule,
        channel_order=str(runtime_input.get("channel_order", "tx_major")),
    )

    info = {
        "simulation_backend": "radarsimpy.sim_radar",
        "simulation_device": str(runtime_input.get("device", "cpu")),
        "sim_baseband_shape": [int(x) for x in baseband.shape],
        "adc_sctr_shape": [int(x) for x in adc_sctr.shape],
        "target_count": int(len(point_targets)),
        "n_tx": int(n_tx),
        "n_rx": int(n_rx),
    }
    return adc_sctr, info


def _build_tx_channels_for_sim(
    tx_pos: np.ndarray,
    tx_schedule: Sequence[int],
    apply_tdm_schedule: bool,
) -> List[Dict[str, Any]]:
    n_tx = int(tx_pos.shape[0])
    n_chirps = int(len(tx_schedule))
    out: List[Dict[str, Any]] = []
    for tx_idx in range(n_tx):
        row: Dict[str, Any] = {
            "location": [float(x) for x in tx_pos[tx_idx].tolist()],
        }
        if apply_tdm_schedule and n_tx > 1:
            pulse_amp = np.zeros(n_chirps, dtype=np.float64)
            pulse_amp[np.asarray(tx_schedule, dtype=np.int64) == int(tx_idx)] = 1.0
            row["pulse_amp"] = pulse_amp
        out.append(row)
    return out


def _build_sim_point_targets(
    targets: Sequence[Mapping[str, Any]],
    min_range_m: float,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for target in targets:
        az = math.radians(float(target["az_deg"]))
        el = math.radians(float(target["el_deg"]))
        u = np.asarray(
            [
                math.cos(el) * math.cos(az),
                math.cos(el) * math.sin(az),
                math.sin(el),
            ],
            dtype=np.float64,
        )
        rng = max(float(min_range_m), float(target["range_m"]))
        location = u * rng
        radial_v = float(target["radial_velocity_mps"])
        speed = u * radial_v
        amp_scale = complex(target["amp_scale"])
        rcs_dbsm = _estimate_rcs_dbsm(target=target, amp_scale=amp_scale)
        phase_value = target.get("phase_deg")
        if phase_value is None:
            phase_deg = float(math.degrees(math.atan2(amp_scale.imag, amp_scale.real)))
        else:
            phase_deg = float(phase_value)

        out.append(
            {
                "location": location,
                "speed": speed,
                "rcs": float(rcs_dbsm),
                "phase": float(phase_deg),
            }
        )
    return out


def _estimate_rcs_dbsm(target: Mapping[str, Any], amp_scale: complex) -> float:
    explicit = target.get("rcs_dbsm")
    if explicit is not None:
        return float(explicit)
    mag = abs(complex(amp_scale))
    return float(10.0 * math.log10(max(mag * mag, 1.0e-12)))


def _resolve_runtime_tx_schedule(
    runtime_input: Mapping[str, Any],
    backend: Mapping[str, Any],
    n_chirps: int,
    n_tx: int,
) -> List[int]:
    raw = runtime_input.get("tx_schedule")
    if raw is None:
        raw = backend.get("resolved_tx_schedule", backend.get("tx_schedule"))
    if raw is None:
        return [int(i % n_tx) for i in range(int(n_chirps))]
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("tx_schedule must be list[int]")
    out = [int(x) for x in raw]
    if len(out) != int(n_chirps):
        raise ValueError("tx_schedule length must equal n_chirps")
    for i, tx in enumerate(out):
        if tx < 0 or tx >= int(n_tx):
            raise ValueError(f"tx_schedule[{i}] out of range: {tx}")
    return out


def _convert_sim_baseband_to_adc_sctr(
    baseband: np.ndarray,
    n_tx: int,
    n_rx: int,
    n_chirps: int,
    samples_per_chirp: int,
    tx_schedule: Sequence[int],
    channel_order: str,
) -> np.ndarray:
    arr = np.asarray(baseband, dtype=np.complex128)
    if arr.ndim != 3:
        raise ValueError("radarsimpy sim_radar baseband must be 3D [channel,pulse,sample]")
    n_chan, n_pulse, n_sample = [int(x) for x in arr.shape]
    if n_pulse != int(n_chirps):
        raise ValueError(f"unexpected pulse count from sim_radar: {n_pulse} != {n_chirps}")
    if n_sample != int(samples_per_chirp):
        raise ValueError(f"unexpected sample count from sim_radar: {n_sample} != {samples_per_chirp}")

    order = str(channel_order).strip().lower()
    adc = np.zeros((n_sample, n_pulse, int(n_tx), int(n_rx)), dtype=np.complex128)

    if n_chan == int(n_tx) * int(n_rx):
        if order == "tx_major":
            view = arr.reshape(int(n_tx), int(n_rx), n_pulse, n_sample)
            adc = np.transpose(view, (3, 2, 0, 1))
        elif order == "rx_major":
            view = arr.reshape(int(n_rx), int(n_tx), n_pulse, n_sample)
            adc = np.transpose(view, (3, 2, 1, 0))
        else:
            raise ValueError("runtime_input.channel_order must be tx_major or rx_major")
    elif n_chan == int(n_rx):
        schedule = [int(x) for x in tx_schedule]
        for chirp_idx, tx_idx in enumerate(schedule):
            adc[:, chirp_idx, tx_idx, :] = np.transpose(arr[:, chirp_idx, :], (1, 0))
    elif (int(n_tx) == 1) and (int(n_rx) == 1) and (n_chan == 1):
        adc[:, :, 0, 0] = np.transpose(arr[0, :, :], (1, 0))
    else:
        raise ValueError(
            "unable to map sim_radar baseband channels to adc_sctr: "
            f"channels={n_chan}, n_tx={n_tx}, n_rx={n_rx}"
        )

    if not np.all(np.isfinite(np.real(adc))) or not np.all(np.isfinite(np.imag(adc))):
        raise ValueError("adc_sctr contains non-finite values")
    return adc


def _resolve_positions_3d(value: Any, key_name: str) -> np.ndarray:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{key_name} must be list of [x,y,z]")
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 3 or arr.shape[0] <= 0:
        raise ValueError(f"{key_name} must have shape (n,3)")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{key_name} must be finite")
    return arr


def _has_radarsimpy_sim_api(module: ModuleType) -> bool:
    needed = ("Radar", "Transmitter", "Receiver", "sim_radar")
    return all(hasattr(module, name) for name in needed)


def _resolve_optional_ray_filter(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("runtime_input.ray_filter must be list[int,int]")
    if len(value) != 2:
        raise ValueError("runtime_input.ray_filter must have length 2")
    return [int(value[0]), int(value[1])]


def _resolve_targets(runtime_input: Mapping[str, Any]) -> List[Dict[str, Any]]:
    raw = runtime_input.get("targets")
    if raw is None:
        raw = [
            {
                "range_m": float(runtime_input.get("target_range_m", 25.0)),
                "az_deg": float(runtime_input.get("target_az_deg", 0.0)),
                "el_deg": float(runtime_input.get("target_el_deg", 0.0)),
                "radial_velocity_mps": float(runtime_input.get("target_radial_velocity_mps", 0.0)),
                "amp_scale": runtime_input.get("amp_scale", 1.0),
                "range_amp_exponent": float(runtime_input.get("range_amp_exponent", 2.0)),
                "material_tag": str(runtime_input.get("material_tag", "radarsimpy_runtime")),
                "reflection_order": int(runtime_input.get("reflection_order", 1)),
                "path_id_prefix": str(runtime_input.get("path_id_prefix", "radarsimpy_runtime")),
            }
        ]

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) == 0:
        raise ValueError("runtime_input.targets must be non-empty list when provided")

    out: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise ValueError(f"runtime_input.targets[{idx}] must be object")
        row = dict(item)
        path_id_prefix = str(row.get("path_id_prefix", f"radarsimpy_runtime_t{idx}")).strip()
        if path_id_prefix == "":
            raise ValueError(f"runtime_input.targets[{idx}].path_id_prefix must be non-empty")
        reflection_order = int(row.get("reflection_order", 1))
        if reflection_order < 0:
            raise ValueError(f"runtime_input.targets[{idx}].reflection_order must be >= 0")
        range_m = float(row.get("range_m", 25.0))
        if range_m <= 0.0:
            raise ValueError(f"runtime_input.targets[{idx}].range_m must be > 0")

        out.append(
            {
                "range_m": range_m,
                "az_deg": float(row.get("az_deg", 0.0)),
                "el_deg": float(row.get("el_deg", 0.0)),
                "radial_velocity_mps": float(row.get("radial_velocity_mps", 0.0)),
                "amp_scale": _parse_complex(
                    row.get("amp_scale", row.get("amp", 1.0)),
                    f"runtime_input.targets[{idx}].amp_scale",
                ),
                "range_amp_exponent": float(row.get("range_amp_exponent", 2.0)),
                "rcs_dbsm": _opt_float(row.get("rcs_dbsm")),
                "phase_deg": _opt_float(row.get("phase_deg")),
                "material_tag": str(row.get("material_tag", "radarsimpy_runtime")),
                "reflection_order": reflection_order,
                "path_id_prefix": path_id_prefix,
            }
        )
    return out


def _resolve_chirp_interval_s(context: Mapping[str, Any], runtime_input: Mapping[str, Any]) -> float:
    if "chirp_interval_s" in runtime_input:
        chirp_interval_s = float(runtime_input["chirp_interval_s"])
    else:
        radar = _as_obj(context, "radar", required=False)
        samples_per_chirp = int(radar.get("samples_per_chirp", 1024))
        fs_hz = float(radar.get("fs_hz", 20e6))
        if fs_hz <= 0.0:
            raise ValueError("context.radar.fs_hz must be > 0")
        chirp_interval_s = float(samples_per_chirp) / fs_hz
    if chirp_interval_s <= 0.0:
        raise ValueError("runtime_input.chirp_interval_s must be > 0")
    return chirp_interval_s


def _import_radarsimpy_module() -> ModuleType:
    return rs_api.load_radarsimpy_module()


def _opt_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _opt_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    return text


def _parse_complex(value: Any, key_name: str) -> complex:
    if isinstance(value, complex):
        return complex(value)
    if isinstance(value, Mapping):
        return complex(float(value.get("re", 0.0)), float(value.get("im", 0.0)))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) != 2:
            raise ValueError(f"{key_name} list form must be [re, im]")
        return complex(float(value[0]), float(value[1]))
    return complex(float(value), 0.0)


def _as_obj(payload: Mapping[str, Any], key: str, required: bool = True) -> Dict[str, Any]:
    value = payload.get(key)
    if value is None and not required:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be object")
    return dict(value)

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from .constants import C0


def _as_len3(value: Any, *, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64).reshape(-1)
    if arr.size != 3:
        raise ValueError(f"{name} must have length 3")
    return arr


def _as_target_list(targets: Any) -> list[Mapping[str, Any]]:
    if isinstance(targets, (str, bytes)):
        raise ValueError("targets must be a list of mapping objects")
    out = list(targets)
    for idx, row in enumerate(out):
        if not isinstance(row, Mapping):
            raise ValueError(f"targets[{idx}] must be mapping")
    return out


def _extract_radar_params(radar: Any) -> dict[str, Any]:
    if hasattr(radar, "radar_prop"):
        transmitter = radar.radar_prop["transmitter"]
        receiver = radar.radar_prop["receiver"]
    else:
        transmitter = getattr(radar, "transmitter", None)
        receiver = getattr(radar, "receiver", None)
        if (transmitter is None) or (receiver is None):
            raise TypeError("radar must expose either radar_prop or transmitter/receiver")

    tx_wave = getattr(transmitter, "waveform_prop", None)
    tx_chan = getattr(transmitter, "txchannel_prop", None)
    rx_bb = getattr(receiver, "bb_prop", None)
    rx_chan = getattr(receiver, "rxchannel_prop", None)
    if (tx_wave is None) or (tx_chan is None) or (rx_bb is None) or (rx_chan is None):
        raise TypeError("radar object does not expose required RadarSimPy model properties")

    fs = float(rx_bb["fs"])
    if fs <= 0.0:
        raise ValueError("receiver.bb_prop['fs'] must be > 0")

    pulses = int(tx_wave["pulses"])
    if pulses <= 0:
        raise ValueError("transmitter.waveform_prop['pulses'] must be > 0")

    pulse_length = float(tx_wave["pulse_length"])
    if pulse_length <= 0.0:
        raise ValueError("transmitter.waveform_prop['pulse_length'] must be > 0")

    samples_per_pulse = None
    sample_prop = getattr(radar, "sample_prop", None)
    if isinstance(sample_prop, Mapping):
        raw = sample_prop.get("samples_per_pulse")
        if raw is not None:
            samples_per_pulse = int(raw)
    if samples_per_pulse is None:
        samples_per_pulse = int(pulse_length * fs)
    if samples_per_pulse <= 0:
        raise ValueError("samples_per_pulse must be > 0")

    f_arr = np.asarray(tx_wave["f"], dtype=np.float64).reshape(-1)
    if f_arr.size <= 0:
        raise ValueError("transmitter.waveform_prop['f'] must not be empty")
    fc_hz = float(np.mean(f_arr))
    bandwidth_hz = float(np.max(f_arr) - np.min(f_arr))
    slope_hz_per_s = bandwidth_hz / pulse_length if pulse_length > 0.0 else 0.0

    prp = np.asarray(tx_wave.get("prp", np.full(pulses, pulse_length)), dtype=np.float64).reshape(-1)
    if prp.size == 1:
        prp = np.full(pulses, float(prp[0]), dtype=np.float64)
    if prp.size != pulses:
        raise ValueError("transmitter.waveform_prop['prp'] length must match pulses")
    pulse_start_time = np.asarray(tx_wave.get("pulse_start_time"), dtype=np.float64).reshape(-1)
    if pulse_start_time.size != pulses:
        pulse_start_time = np.cumsum(prp) - float(prp[0])

    tx_pos = np.asarray(tx_chan["locations"], dtype=np.float64)
    rx_pos = np.asarray(rx_chan["locations"], dtype=np.float64)
    if tx_pos.ndim != 2 or tx_pos.shape[1] != 3 or tx_pos.shape[0] <= 0:
        raise ValueError("transmitter.txchannel_prop['locations'] must have shape (n_tx, 3)")
    if rx_pos.ndim != 2 or rx_pos.shape[1] != 3 or rx_pos.shape[0] <= 0:
        raise ValueError("receiver.rxchannel_prop['locations'] must have shape (n_rx, 3)")

    tx_delay = np.asarray(tx_chan.get("delay", np.zeros(tx_pos.shape[0])), dtype=np.float64).reshape(-1)
    if tx_delay.size != tx_pos.shape[0]:
        tx_delay = np.zeros(tx_pos.shape[0], dtype=np.float64)

    pulse_mod = np.asarray(
        tx_chan.get("pulse_mod", np.ones((tx_pos.shape[0], pulses), dtype=np.complex128)),
        dtype=np.complex128,
    )
    if pulse_mod.shape != (tx_pos.shape[0], pulses):
        pulse_mod = np.ones((tx_pos.shape[0], pulses), dtype=np.complex128)

    tx_power_dbm = float(getattr(transmitter, "rf_prop", {}).get("tx_power", 0.0))
    tx_power_scale = float(10.0 ** (tx_power_dbm / 20.0))

    return {
        "transmitter": transmitter,
        "receiver": receiver,
        "fs_hz": fs,
        "pulses": pulses,
        "samples_per_pulse": samples_per_pulse,
        "pulse_length_s": pulse_length,
        "fc_hz": fc_hz,
        "slope_hz_per_s": slope_hz_per_s,
        "pulse_start_time_s": pulse_start_time,
        "tx_pos_m": tx_pos,
        "rx_pos_m": rx_pos,
        "tx_delay_s": tx_delay,
        "pulse_mod": pulse_mod,
        "tx_power_scale": tx_power_scale,
    }


def _target_sigma_linear(target: Mapping[str, Any]) -> float:
    if "rcs_dbsm" in target:
        return float(10.0 ** (float(target["rcs_dbsm"]) / 10.0))
    if "rcs" in target:
        # RadarSimPy sim_radar point target uses rcs in dBsm.
        return float(10.0 ** (float(target["rcs"]) / 10.0))
    return 1.0


def _target_phase_rad(target: Mapping[str, Any]) -> float:
    return float(np.radians(float(target.get("phase", 0.0))))


def _target_state(target: Mapping[str, Any], t_s: float) -> tuple[np.ndarray, np.ndarray]:
    loc = _as_len3(target.get("location", (0.0, 0.0, 0.0)), name="target.location")
    speed = _as_len3(target.get("speed", (0.0, 0.0, 0.0)), name="target.speed")
    return loc + speed * float(t_s), speed


def _build_base_timestamp(params: Mapping[str, Any]) -> np.ndarray:
    tx_pos = np.asarray(params["tx_pos_m"], dtype=np.float64)
    rx_pos = np.asarray(params["rx_pos_m"], dtype=np.float64)
    n_tx = int(tx_pos.shape[0])
    n_rx = int(rx_pos.shape[0])
    channels = int(n_tx * n_rx)
    pulses = int(params["pulses"])
    samples = int(params["samples_per_pulse"])
    fs = float(params["fs_hz"])
    pulse_start = np.asarray(params["pulse_start_time_s"], dtype=np.float64)
    tx_delay = np.asarray(params["tx_delay_s"], dtype=np.float64)

    sample_t = np.arange(samples, dtype=np.float64) / fs
    tx_idx = np.arange(channels, dtype=np.int64) // n_rx
    channel_delay = tx_delay[tx_idx]
    return (
        channel_delay[:, np.newaxis, np.newaxis]
        + pulse_start[np.newaxis, :, np.newaxis]
        + sample_t[np.newaxis, np.newaxis, :]
    )


def core_sim_radar(  # pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments
    radar: Any,
    targets: Sequence[Mapping[str, Any]],
    density: float = 1,
    level: str | None = None,
    interf: Any = None,
    ray_filter: Sequence[int] | None = None,
    back_propagating: bool = False,
    device: str = "gpu",
    log_path: str | None = None,
    dry_run: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    del level, interf, ray_filter, back_propagating, device, log_path, kwargs
    params = _extract_radar_params(radar)
    target_rows = _as_target_list(targets)

    n_tx = int(params["tx_pos_m"].shape[0])
    n_rx = int(params["rx_pos_m"].shape[0])
    pulses = int(params["pulses"])
    samples = int(params["samples_per_pulse"])
    fs = float(params["fs_hz"])
    fc = float(params["fc_hz"])
    lam = C0 / max(fc, 1.0)
    slope = float(params["slope_hz_per_s"])
    pulse_start = np.asarray(params["pulse_start_time_s"], dtype=np.float64)
    tx_delay = np.asarray(params["tx_delay_s"], dtype=np.float64)
    pulse_mod = np.asarray(params["pulse_mod"], dtype=np.complex128)
    sample_t = np.arange(samples, dtype=np.float64) / fs

    n_chan = int(n_tx * n_rx)
    baseband = np.zeros((n_chan, pulses, samples), dtype=np.complex128)
    noise = np.zeros_like(baseband)
    timestamp = _build_base_timestamp(params)

    if bool(dry_run) or (len(target_rows) <= 0):
        return {
            "baseband": baseband,
            "noise": noise,
            "timestamp": timestamp,
            "interference": None,
        }

    density_scale = float(max(float(density), 1.0e-12))
    tx_scale = float(params["tx_power_scale"]) * np.sqrt(density_scale)
    tx_pos = np.asarray(params["tx_pos_m"], dtype=np.float64)
    rx_pos = np.asarray(params["rx_pos_m"], dtype=np.float64)

    for tx_idx in range(n_tx):
        for rx_idx in range(n_rx):
            chan_idx = int(tx_idx * n_rx + rx_idx)
            tx_loc = tx_pos[tx_idx]
            rx_loc = rx_pos[rx_idx]
            for pulse_idx in range(pulses):
                mod = complex(pulse_mod[tx_idx, pulse_idx])
                if abs(mod) <= 0.0:
                    continue
                pulse_time = float(pulse_start[pulse_idx] + tx_delay[tx_idx])
                y = np.zeros(samples, dtype=np.complex128)
                for target in target_rows:
                    pos, vel = _target_state(target, pulse_time)
                    dtx_vec = pos - tx_loc
                    drx_vec = pos - rx_loc
                    dtx = float(np.linalg.norm(dtx_vec))
                    drx = float(np.linalg.norm(drx_vec))
                    if (dtx <= 0.0) or (drx <= 0.0):
                        continue
                    path_m = max(dtx + drx, 1.0e-6)
                    tau = path_m / C0

                    vtx = float(np.dot(vel, dtx_vec / dtx))
                    vrx = float(np.dot(vel, drx_vec / drx))
                    # Match RadarSimPy baseband Doppler sign convention.
                    doppler_hz = (vtx + vrx) / max(lam, 1.0e-12)
                    beat_hz = (slope * tau) + doppler_hz

                    sigma = max(_target_sigma_linear(target), 0.0)
                    amp = (np.sqrt(sigma) / (path_m * path_m)) * tx_scale
                    phase0 = _target_phase_rad(target) - (2.0 * np.pi * fc * tau) + (2.0 * np.pi * doppler_hz * pulse_time)

                    y += amp * np.exp(1j * ((2.0 * np.pi * beat_hz * sample_t) + phase0))
                baseband[chan_idx, pulse_idx, :] = mod * y

    return {
        "baseband": baseband,
        "noise": noise,
        "timestamp": timestamp,
        "interference": None,
    }


def _angles_to_vectors(phi_deg: np.ndarray, theta_deg: np.ndarray) -> np.ndarray:
    phi = np.radians(phi_deg)
    theta = np.radians(theta_deg)
    return np.stack(
        [
            np.sin(theta) * np.cos(phi),
            np.sin(theta) * np.sin(phi),
            np.cos(theta),
        ],
        axis=-1,
    )


def core_sim_rcs(
    targets: Sequence[Mapping[str, Any]],
    f: float,
    inc_phi: float | Sequence[float] | np.ndarray,
    inc_theta: float | Sequence[float] | np.ndarray,
    inc_pol: Sequence[complex] = (0, 0, 1),
    obs_phi: float | Sequence[float] | np.ndarray | None = None,
    obs_theta: float | Sequence[float] | np.ndarray | None = None,
    obs_pol: Sequence[complex] | None = None,
    density: float = 1.0,
    **kwargs: Any,
) -> float | np.ndarray:
    del f, kwargs
    rows = _as_target_list(targets)

    if obs_pol is None:
        obs_pol = inc_pol
    if obs_phi is None:
        obs_phi = inc_phi
    if obs_theta is None:
        obs_theta = inc_theta

    inc_phi_arr = np.asarray(inc_phi, dtype=np.float64).reshape(-1)
    inc_theta_arr = np.asarray(inc_theta, dtype=np.float64).reshape(-1)
    obs_phi_arr = np.asarray(obs_phi, dtype=np.float64).reshape(-1)
    obs_theta_arr = np.asarray(obs_theta, dtype=np.float64).reshape(-1)

    if inc_phi_arr.shape != inc_theta_arr.shape:
        raise ValueError("The lengths of `inc_phi` and `inc_theta` must be the same")
    if obs_phi_arr.shape != obs_theta_arr.shape:
        raise ValueError("The lengths of `obs_phi` and `obs_theta` must be the same")
    if inc_phi_arr.shape != obs_phi_arr.shape:
        raise ValueError("The lengths of `inc_phi` and `obs_phi` must be the same")

    inc_pol_arr = np.asarray(inc_pol, dtype=np.complex128).reshape(-1)
    obs_pol_arr = np.asarray(obs_pol, dtype=np.complex128).reshape(-1)
    if (inc_pol_arr.size != 3) or (obs_pol_arr.size != 3):
        raise ValueError("inc_pol and obs_pol must have length 3")
    pol_gain = float(abs(np.vdot(inc_pol_arr, obs_pol_arr))) / (
        max(float(np.linalg.norm(inc_pol_arr)), 1.0e-12) * max(float(np.linalg.norm(obs_pol_arr)), 1.0e-12)
    )

    sigma_total = 0.0
    for row in rows:
        sigma_total += max(_target_sigma_linear(row), 0.0)
    sigma_total = max(sigma_total, 0.0)
    density_scale = float(max(float(density), 1.0e-12))

    inc_vec = _angles_to_vectors(inc_phi_arr, inc_theta_arr)
    obs_vec = _angles_to_vectors(obs_phi_arr, obs_theta_arr)
    ang_match = np.clip(np.sum(inc_vec * obs_vec, axis=-1), -1.0, 1.0)
    ang_gain = 0.5 * (1.0 + ang_match)

    rcs = sigma_total * density_scale * pol_gain * ang_gain
    if rcs.size == 1:
        return float(rcs.reshape(-1)[0])
    return np.asarray(rcs, dtype=np.float64)


__all__ = ["core_sim_radar", "core_sim_rcs"]

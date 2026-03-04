from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

_DEFAULT_POLARIZATION = np.asarray([0.0, 0.0, 1.0], dtype=np.float64)
_DEFAULT_AZIMUTH_RANGE = np.asarray([-90.0, 90.0], dtype=np.float64)
_DEFAULT_ELEVATION_RANGE = np.asarray([-90.0, 90.0], dtype=np.float64)
_DEFAULT_PATTERN_DB = np.asarray([0.0, 0.0], dtype=np.float64)

_BOLTZMANN_CONSTANT = 1.38064852e-23  # J/K
_MILLIWATTS_TO_WATTS = 1.0e-3


def _as_1d_array(value: Any, *, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    elif arr.ndim != 1:
        raise ValueError(f"{name} must be a scalar or 1-D array")
    return arr


def _as_len3(value: Any, *, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64).reshape(-1)
    if arr.size != 3:
        raise ValueError(f"{name} must have length 3")
    return arr


def _as_channel_list(channels: Sequence[Mapping[str, Any]] | None) -> list[Mapping[str, Any]]:
    if channels is None:
        return [{"location": (0.0, 0.0, 0.0)}]
    if isinstance(channels, (str, bytes)):
        raise ValueError("channels must be a list of mapping objects")
    out = list(channels)
    if len(out) <= 0:
        raise ValueError("channels must not be empty")
    for idx, item in enumerate(out):
        if not isinstance(item, Mapping):
            raise ValueError(f"channels[{idx}] must be mapping")
    return out


def _normalized_patterns(
    *,
    channel: Mapping[str, Any],
    channel_idx: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    az_angle = np.asarray(channel.get("azimuth_angle", _DEFAULT_AZIMUTH_RANGE), dtype=np.float64).reshape(-1)
    az_pattern = np.asarray(channel.get("azimuth_pattern", _DEFAULT_PATTERN_DB), dtype=np.float64).reshape(-1)
    if az_angle.shape[0] != az_pattern.shape[0]:
        raise ValueError(
            f"Length mismatch for channel {channel_idx}: azimuth_angle ({az_angle.shape[0]}) "
            f"and azimuth_pattern ({az_pattern.shape[0]}) must have same length"
        )
    antenna_gain = float(np.max(az_pattern))
    az_pattern = az_pattern - antenna_gain

    el_angle = np.asarray(channel.get("elevation_angle", _DEFAULT_ELEVATION_RANGE), dtype=np.float64).reshape(-1)
    el_pattern = np.asarray(channel.get("elevation_pattern", _DEFAULT_PATTERN_DB), dtype=np.float64).reshape(-1)
    if el_angle.shape[0] != el_pattern.shape[0]:
        raise ValueError(
            f"Length mismatch for channel {channel_idx}: elevation_angle ({el_angle.shape[0]}) "
            f"and elevation_pattern ({el_pattern.shape[0]}) must have same length"
        )
    el_pattern = el_pattern - float(np.max(el_pattern))
    return az_angle, az_pattern, el_angle, el_pattern, antenna_gain


def _build_waveform_modulation(
    *,
    mod_t_raw: Any,
    amp_raw: Any,
    phs_raw: Any,
) -> dict[str, Any]:
    if (amp_raw is None) and (phs_raw is not None):
        amp_raw = np.ones_like(np.asarray(phs_raw, dtype=np.float64), dtype=np.float64)
    if (phs_raw is None) and (amp_raw is not None):
        phs_raw = np.zeros_like(np.asarray(amp_raw, dtype=np.float64), dtype=np.float64)

    if (mod_t_raw is None) or (amp_raw is None) or (phs_raw is None):
        return {"enabled": False, "var": None, "t": None}

    mod_t = _as_1d_array(mod_t_raw, name="mod_t")
    amp = _as_1d_array(amp_raw, name="amp")
    phs = _as_1d_array(phs_raw, name="phs")
    if mod_t.shape[0] <= 0:
        return {"enabled": False, "var": None, "t": None}
    if (mod_t.shape[0] != amp.shape[0]) or (amp.shape[0] != phs.shape[0]):
        raise ValueError("Lengths of mod_t/amp/phs must match for waveform modulation")
    mod_var = amp * np.exp(1j * np.radians(phs))
    return {
        "enabled": True,
        "var": np.asarray(mod_var, dtype=np.complex128),
        "t": np.asarray(mod_t, dtype=np.float64),
    }


def _expand_pulse_sequence(value: Any, *, pulses: int, name: str, default: float) -> np.ndarray:
    if value is None:
        return np.full(int(pulses), float(default), dtype=np.float64)
    arr = np.asarray(value, dtype=np.float64).reshape(-1)
    if arr.size == 1:
        return np.full(int(pulses), float(arr.item()), dtype=np.float64)
    if arr.size != int(pulses):
        raise ValueError(f"{name} length ({arr.size}) must match pulses ({int(pulses)})")
    return np.asarray(arr, dtype=np.float64)


class CoreTransmitter:
    """Native fallback for RadarSimPy Transmitter root API."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        f: float | Sequence[float] | np.ndarray,
        t: float | Sequence[float] | np.ndarray,
        tx_power: float = 0,
        pulses: int = 1,
        prp: float | Sequence[float] | np.ndarray | None = None,
        f_offset: float | Sequence[float] | np.ndarray | None = None,
        pn_f: np.ndarray | None = None,
        pn_power: np.ndarray | None = None,
        channels: Sequence[Mapping[str, Any]] | None = None,
    ):
        if int(pulses) < 1:
            raise ValueError("Number of pulses must be at least 1")
        if not isinstance(tx_power, (int, float)):
            raise ValueError("tx_power must be a number")
        pulses_i = int(pulses)

        f_arr = _as_1d_array(f, name="f")
        if f_arr.size == 1:
            f_arr = np.asarray([float(f_arr[0]), float(f_arr[0])], dtype=np.float64)

        if isinstance(t, (list, tuple, np.ndarray)):
            t_arr = _as_1d_array(t, name="t")
            t_arr = np.asarray(t_arr - float(t_arr[0]), dtype=np.float64)
        else:
            t_scalar = float(t)
            t_arr = np.asarray([0.0, t_scalar], dtype=np.float64)

        if f_arr.shape[0] != t_arr.shape[0]:
            raise ValueError(
                f"Lengths of `f` ({f_arr.shape[0]}) and `t` ({t_arr.shape[0]}) should be the same"
            )
        pulse_length = float(t_arr[-1])
        if pulse_length <= 0.0:
            raise ValueError("pulse_length must be > 0")

        f_offset_arr = _expand_pulse_sequence(
            f_offset,
            pulses=pulses_i,
            name="f_offset",
            default=0.0,
        )
        if prp is None:
            prp_arr = np.full(pulses_i, pulse_length, dtype=np.float64)
        else:
            prp_arr = _expand_pulse_sequence(prp, pulses=pulses_i, name="prp", default=pulse_length)
        if float(np.min(prp_arr)) < pulse_length:
            raise ValueError(
                f"All PRP values ({float(np.min(prp_arr)):.2e} s) must be >= pulse_length ({pulse_length:.2e} s)"
            )

        if (pn_f is None) != (pn_power is None):
            raise ValueError("pn_f and pn_power must be both set or both None")
        pn_f_arr = None if pn_f is None else _as_1d_array(pn_f, name="pn_f")
        pn_power_arr = None if pn_power is None else _as_1d_array(pn_power, name="pn_power")
        if (pn_f_arr is not None) and (pn_power_arr is not None) and (pn_f_arr.shape[0] != pn_power_arr.shape[0]):
            raise ValueError("pn_f and pn_power must have the same length")

        self.rf_prop: dict[str, Any] = {
            "tx_power": float(tx_power),
            "pn_f": pn_f_arr,
            "pn_power": pn_power_arr,
        }
        self.waveform_prop: dict[str, Any] = {
            "f": np.asarray(f_arr, dtype=np.float64),
            "t": np.asarray(t_arr, dtype=np.float64),
            "bandwidth": float(np.max(f_arr) - np.min(f_arr)),
            "pulse_length": pulse_length,
            "pulses": pulses_i,
            "f_offset": np.asarray(f_offset_arr, dtype=np.float64),
            "prp": np.asarray(prp_arr, dtype=np.float64),
            "pulse_start_time": np.cumsum(prp_arr) - float(prp_arr[0]),
        }
        self.txchannel_prop = self._process_tx_channels(_as_channel_list(channels))

    def _process_tx_channels(self, channels: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        pulses = int(self.waveform_prop["pulses"])
        size = len(channels)
        tx_prop: dict[str, Any] = {
            "size": int(size),
            "delay": np.zeros(size, dtype=np.float64),
            "grid": np.zeros(size, dtype=np.float64),
            "locations": np.zeros((size, 3), dtype=np.float64),
            "polarization": np.zeros((size, 3), dtype=np.float64),
            "waveform_mod": [],
            "pulse_mod": np.ones((size, pulses), dtype=np.complex128),
            "az_patterns": [],
            "az_angles": [],
            "el_patterns": [],
            "el_angles": [],
            "antenna_gains": np.zeros(size, dtype=np.float64),
        }
        for tx_idx, ch in enumerate(channels):
            tx_prop["delay"][tx_idx] = float(ch.get("delay", 0.0))
            tx_prop["grid"][tx_idx] = float(ch.get("grid", 1.0))
            tx_prop["locations"][tx_idx, :] = _as_len3(ch.get("location", (0.0, 0.0, 0.0)), name=f"channels[{tx_idx}].location")
            tx_prop["polarization"][tx_idx, :] = _as_len3(
                ch.get("polarization", _DEFAULT_POLARIZATION), name=f"channels[{tx_idx}].polarization"
            )

            tx_prop["waveform_mod"].append(
                _build_waveform_modulation(
                    mod_t_raw=ch.get("mod_t"),
                    amp_raw=ch.get("amp"),
                    phs_raw=ch.get("phs"),
                )
            )

            pulse_amp = _expand_pulse_sequence(
                ch.get("pulse_amp"),
                pulses=pulses,
                name=f"channels[{tx_idx}].pulse_amp",
                default=1.0,
            )
            pulse_phs = _expand_pulse_sequence(
                ch.get("pulse_phs"),
                pulses=pulses,
                name=f"channels[{tx_idx}].pulse_phs",
                default=0.0,
            )
            tx_prop["pulse_mod"][tx_idx, :] = pulse_amp * np.exp(1j * np.radians(pulse_phs))

            az_angle, az_pattern, el_angle, el_pattern, ant_gain = _normalized_patterns(
                channel=ch,
                channel_idx=tx_idx,
            )
            tx_prop["antenna_gains"][tx_idx] = ant_gain
            tx_prop["az_angles"].append(az_angle)
            tx_prop["az_patterns"].append(az_pattern)
            tx_prop["el_angles"].append(el_angle)
            tx_prop["el_patterns"].append(el_pattern)
        return tx_prop


class CoreReceiver:
    """Native fallback for RadarSimPy Receiver root API."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        fs: float,
        noise_figure: float = 10,
        rf_gain: float = 0,
        load_resistor: float = 500,
        baseband_gain: float = 0,
        bb_type: str = "complex",
        channels: Sequence[Mapping[str, Any]] | None = None,
    ):
        fs_f = float(fs)
        if fs_f <= 0.0:
            raise ValueError("Sampling rate (fs) must be positive")
        if bb_type not in {"complex", "real"}:
            raise ValueError(f"Invalid baseband type '{bb_type}'. Must be one of: complex, real")
        if float(load_resistor) <= 0.0:
            raise ValueError("load_resistor must be positive")

        self.rf_prop: dict[str, Any] = {
            "rf_gain": float(rf_gain),
            "noise_figure": float(noise_figure),
        }
        self.bb_prop: dict[str, Any] = {
            "fs": fs_f,
            "load_resistor": float(load_resistor),
            "baseband_gain": float(baseband_gain),
            "bb_type": str(bb_type),
            "noise_bandwidth": fs_f if bb_type == "complex" else fs_f / 2.0,
        }
        self.rxchannel_prop = self._process_rx_channels(_as_channel_list(channels))

    def _process_rx_channels(self, channels: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        size = len(channels)
        rx_prop: dict[str, Any] = {
            "size": int(size),
            "locations": np.zeros((size, 3), dtype=np.float64),
            "polarization": np.zeros((size, 3), dtype=np.float64),
            "az_patterns": [],
            "az_angles": [],
            "el_patterns": [],
            "el_angles": [],
            "antenna_gains": np.zeros(size, dtype=np.float64),
        }
        for rx_idx, ch in enumerate(channels):
            rx_prop["locations"][rx_idx, :] = _as_len3(ch.get("location", (0.0, 0.0, 0.0)), name=f"channels[{rx_idx}].location")
            rx_prop["polarization"][rx_idx, :] = _as_len3(
                ch.get("polarization", _DEFAULT_POLARIZATION), name=f"channels[{rx_idx}].polarization"
            )
            az_angle, az_pattern, el_angle, el_pattern, ant_gain = _normalized_patterns(
                channel=ch,
                channel_idx=rx_idx,
            )
            rx_prop["antenna_gains"][rx_idx] = ant_gain
            rx_prop["az_angles"].append(az_angle)
            rx_prop["az_patterns"].append(az_pattern)
            rx_prop["el_angles"].append(el_angle)
            rx_prop["el_patterns"].append(el_pattern)
        return rx_prop


class CoreRadar:
    """Native fallback for RadarSimPy Radar root API."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        transmitter: CoreTransmitter,
        receiver: CoreReceiver,
        frame_time: float | int | Sequence[float] | np.ndarray = 0,
        location: Sequence[float] = (0, 0, 0),
        speed: Sequence[float] = (0, 0, 0),
        rotation: Sequence[float] = (0, 0, 0),
        rotation_rate: Sequence[float] = (0, 0, 0),
        seed: int | None = None,
        **kwargs: Any,
    ):
        _ = kwargs
        _ = seed

        if not hasattr(transmitter, "txchannel_prop") or not hasattr(transmitter, "waveform_prop"):
            raise TypeError("transmitter must expose txchannel_prop and waveform_prop")
        if not hasattr(receiver, "rxchannel_prop") or not hasattr(receiver, "bb_prop"):
            raise TypeError("receiver must expose rxchannel_prop and bb_prop")

        pulse_length = float(transmitter.waveform_prop["pulse_length"])
        fs = float(receiver.bb_prop["fs"])
        samples_per_pulse = int(pulse_length * fs)
        if samples_per_pulse <= 0:
            raise ValueError(
                f"samples_per_pulse must be greater than 0, got {samples_per_pulse}. "
                f"pulse_length={pulse_length}, fs={fs}"
            )

        tx_size = int(transmitter.txchannel_prop["size"])
        rx_size = int(receiver.rxchannel_prop["size"])
        tx_locations = np.asarray(transmitter.txchannel_prop["locations"], dtype=np.float64)
        rx_locations = np.asarray(receiver.rxchannel_prop["locations"], dtype=np.float64)
        if tx_locations.shape != (tx_size, 3):
            raise ValueError("transmitter.txchannel_prop['locations'] must have shape (tx_size, 3)")
        if rx_locations.shape != (rx_size, 3):
            raise ValueError("receiver.rxchannel_prop['locations'] must have shape (rx_size, 3)")

        self.sample_prop: dict[str, Any] = {"samples_per_pulse": int(samples_per_pulse)}
        self.array_prop: dict[str, Any] = {
            "size": int(tx_size * rx_size),
            "virtual_array": np.repeat(tx_locations, rx_size, axis=0)
            + np.tile(rx_locations, (tx_size, 1)),
        }
        self.radar_prop: dict[str, Any] = {
            "transmitter": transmitter,
            "receiver": receiver,
        }
        self.time_prop: dict[str, Any] = {}

        self.time_prop["origin_timestamp"] = self._generate_origin_timestamp()
        self.time_prop["origin_timestamp_shape"] = np.shape(self.time_prop["origin_timestamp"])
        self.time_prop["frame_start_time"] = np.asarray(frame_time, dtype=np.float64)
        self.time_prop["timestamp"] = self._generate_timestamp()
        self.time_prop["timestamp_shape"] = np.shape(self.time_prop["timestamp"])

        self.sample_prop["noise"] = self._calculate_noise_amp()
        self.sample_prop["phase_noise"] = None

        # Keep scalar motion model in native fallback (shape-compatible with upstream static mode).
        self.radar_prop["location"] = _as_len3(location, name="location")
        self.radar_prop["speed"] = _as_len3(speed, name="speed")
        self.radar_prop["rotation"] = np.radians(_as_len3(rotation, name="rotation"))
        self.radar_prop["rotation_rate"] = np.radians(_as_len3(rotation_rate, name="rotation_rate"))

    def _generate_origin_timestamp(self) -> np.ndarray:
        channel_size = int(self.array_prop["size"])
        rx_channel_size = int(self.radar_prop["receiver"].rxchannel_prop["size"])
        samples_per_pulse = int(self.sample_prop["samples_per_pulse"])
        prp = np.asarray(self.radar_prop["transmitter"].waveform_prop["prp"], dtype=np.float64)
        tx_delays = np.asarray(self.radar_prop["transmitter"].txchannel_prop["delay"], dtype=np.float64)
        fs = float(self.radar_prop["receiver"].bb_prop["fs"])

        sample_times = np.arange(samples_per_pulse, dtype=np.float64) / fs
        pulse_start_times = np.cumsum(prp) - float(prp[0])
        tx_indices = np.arange(channel_size, dtype=np.int64) // int(rx_channel_size)
        channel_delays = tx_delays[tx_indices]
        return (
            channel_delays[:, np.newaxis, np.newaxis]
            + pulse_start_times[np.newaxis, :, np.newaxis]
            + sample_times[np.newaxis, np.newaxis, :]
        )

    def _generate_timestamp(self) -> np.ndarray:
        frame_start_time = np.asarray(self.time_prop["frame_start_time"], dtype=np.float64)
        origin_timestamp = np.asarray(self.time_prop["origin_timestamp"], dtype=np.float64)
        if frame_start_time.size > 1:
            num_frames = int(frame_start_time.size)
            channels, pulses, samples = origin_timestamp.shape
            offsets = np.broadcast_to(
                frame_start_time.reshape(num_frames, 1, 1),
                (num_frames, pulses, samples),
            )
            offsets = np.repeat(offsets[:, np.newaxis, :, :], channels, axis=1)
            offsets = offsets.reshape(num_frames * channels, pulses, samples)
            return np.tile(origin_timestamp, (num_frames, 1, 1)) + offsets
        return origin_timestamp + float(frame_start_time.reshape(-1)[0])

    def _calculate_noise_amp(self, noise_temp: float = 290.0) -> float:
        input_noise_dbm = 10.0 * np.log10(_BOLTZMANN_CONSTANT * float(noise_temp) * 1000.0)
        rx = self.radar_prop["receiver"]
        receiver_noise_dbm = (
            input_noise_dbm
            + float(rx.rf_prop["rf_gain"])
            + float(rx.rf_prop["noise_figure"])
            + 10.0 * np.log10(float(rx.bb_prop["noise_bandwidth"]))
            + float(rx.bb_prop["baseband_gain"])
        )
        receiver_noise_watts = _MILLIWATTS_TO_WATTS * (10.0 ** (receiver_noise_dbm / 10.0))
        return float(np.sqrt(receiver_noise_watts * float(rx.bb_prop["load_resistor"])))

    @property
    def timestamp(self) -> np.ndarray:
        return np.asarray(self.time_prop["timestamp"])

    @property
    def transmitter(self) -> CoreTransmitter:
        return self.radar_prop["transmitter"]

    @property
    def receiver(self) -> CoreReceiver:
        return self.radar_prop["receiver"]


__all__ = ["CoreTransmitter", "CoreReceiver", "CoreRadar"]

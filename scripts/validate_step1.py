#!/Library/Developer/CommandLineTools/usr/bin/python3
import math
from dataclasses import dataclass
from typing import List

import numpy as np

from avxsim.constants import C0
from avxsim.scenarios import make_constant_velocity_paths, make_static_paths, make_two_path_multipath
from avxsim.synth import synth_fmcw_tdm
from avxsim.types import RadarConfig


@dataclass(frozen=True)
class Setup:
    fc_hz: float = 77e9
    slope_hz_per_s: float = 20e12
    fs_hz: float = 20e6
    samples_per_chirp: int = 8192
    n_chirps: int = 8
    n_tx: int = 2
    n_rx: int = 4


def build_positions(fc_hz: float, n_tx: int, n_rx: int):
    lam = C0 / fc_hz
    d = 0.5 * lam
    tx_pos = np.zeros((n_tx, 3), dtype=np.float64)
    rx_pos = np.zeros((n_rx, 3), dtype=np.float64)
    tx_pos[:, 0] = np.arange(n_tx) * d
    rx_pos[:, 0] = np.arange(n_rx) * d
    return tx_pos, rx_pos


def dominant_freq_hz(signal: np.ndarray, fs_hz: float) -> float:
    n = signal.shape[0]
    spectrum = np.fft.fft(signal)
    freqs = np.fft.fftfreq(n, d=1.0 / fs_hz)
    mask = freqs >= 0.0
    mag = np.abs(spectrum[mask])
    f = freqs[mask]
    return float(f[int(np.argmax(mag))])


def topk_freqs_hz(signal: np.ndarray, fs_hz: float, k: int) -> List[float]:
    n = signal.shape[0]
    spectrum = np.fft.fft(signal)
    freqs = np.fft.fftfreq(n, d=1.0 / fs_hz)
    mask = freqs >= 0.0
    mag = np.abs(spectrum[mask])
    f = freqs[mask]
    idx = np.argsort(mag)[-k:][::-1]
    return [float(f[i]) for i in idx]


def close_freq(actual: float, expected: float, tol_hz: float) -> bool:
    return abs(actual - expected) <= tol_hz


def run():
    s = Setup()
    tx_schedule = [i % s.n_tx for i in range(s.n_chirps)]
    radar = RadarConfig(
        fc_hz=s.fc_hz,
        slope_hz_per_s=s.slope_hz_per_s,
        fs_hz=s.fs_hz,
        samples_per_chirp=s.samples_per_chirp,
        tx_schedule=tx_schedule,
    )
    tx_pos, rx_pos = build_positions(s.fc_hz, s.n_tx, s.n_rx)
    tol = 1.5 * s.fs_hz / s.samples_per_chirp
    direction = (0.0, 1.0, 0.0)

    print("[CP-0] ADC shape and TDM gating")
    static_paths = make_static_paths(
        n_chirps=s.n_chirps,
        range_m=45.0,
        amp=1.0 + 0.0j,
        unit_direction=direction,
    )
    adc = synth_fmcw_tdm(static_paths, tx_pos, rx_pos, radar)
    assert adc.shape == (s.samples_per_chirp, s.n_chirps, s.n_tx, s.n_rx), adc.shape
    for chirp_idx, tx_idx in enumerate(tx_schedule):
        for tx in range(s.n_tx):
            energy = float(np.max(np.abs(adc[:, chirp_idx, tx, :])))
            if tx == tx_idx:
                assert energy > 0.0
            else:
                assert energy < 1e-9
    print("  PASS")

    print("[CP-1] Static point target")
    r_static = 45.0
    tau_static = 2.0 * r_static / C0
    expected_static = s.slope_hz_per_s * tau_static
    sig = adc[:, 0, tx_schedule[0], 0]
    f_actual = dominant_freq_hz(sig, s.fs_hz)
    assert close_freq(f_actual, expected_static, tol), (f_actual, expected_static, tol)
    print(f"  PASS (actual={f_actual:.1f}Hz expected={expected_static:.1f}Hz tol={tol:.1f}Hz)")

    print("[CP-2] Constant velocity point target")
    v = 40.0
    moving_paths = make_constant_velocity_paths(
        n_chirps=s.n_chirps,
        range_m=45.0,
        radial_velocity_mps=v,
        fc_hz=s.fc_hz,
        amp=1.0 + 0.0j,
        unit_direction=direction,
    )
    adc_move = synth_fmcw_tdm(moving_paths, tx_pos, rx_pos, radar)
    lam = C0 / s.fc_hz
    fd = 2.0 * v / lam
    expected_move = expected_static + fd
    f_move = dominant_freq_hz(adc_move[:, 0, tx_schedule[0], 0], s.fs_hz)
    assert close_freq(f_move, expected_move, tol), (f_move, expected_move, tol)
    print(f"  PASS (actual={f_move:.1f}Hz expected={expected_move:.1f}Hz tol={tol:.1f}Hz)")

    print("[CP-3] Two-path multipath")
    r1 = 45.0
    r2 = 51.0
    two_paths = make_two_path_multipath(
        n_chirps=s.n_chirps,
        ranges_m=[r1, r2],
        amps=[1.0 + 0.0j, 0.6 + 0.1j],
        unit_direction=direction,
    )
    adc_two = synth_fmcw_tdm(two_paths, tx_pos, rx_pos, radar)
    top2 = topk_freqs_hz(adc_two[:, 0, tx_schedule[0], 0], s.fs_hz, k=2)
    exp1 = s.slope_hz_per_s * (2.0 * r1 / C0)
    exp2 = s.slope_hz_per_s * (2.0 * r2 / C0)
    has_exp1 = any(close_freq(f, exp1, tol) for f in top2)
    has_exp2 = any(close_freq(f, exp2, tol) for f in top2)
    assert has_exp1 and has_exp2, (top2, exp1, exp2, tol)
    print(f"  PASS (top2={[round(x, 1) for x in top2]})")

    print("All step-1 checkpoints passed.")


if __name__ == "__main__":
    run()


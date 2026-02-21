#!/Library/Developer/CommandLineTools/usr/bin/python3
import json
import tempfile
from pathlib import Path

import numpy as np

from avxsim.adapters import load_hybrid_paths_from_frames, load_hybrid_radar_geometry
from avxsim.constants import C0
from avxsim.synth import synth_fmcw_tdm
from avxsim.types import RadarConfig


def dominant_freq_hz(signal: np.ndarray, fs_hz: float) -> float:
    n = signal.shape[0]
    spec = np.fft.fft(signal)
    freqs = np.fft.fftfreq(n, d=1.0 / fs_hz)
    mask = freqs >= 0
    return float(freqs[mask][int(np.argmax(np.abs(spec[mask])) )])


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "hybrid_frames"
        pair = root / "Tx0Rx0"
        pair.mkdir(parents=True, exist_ok=True)

        amp1 = np.zeros((8, 8), dtype=np.float32)
        dist1 = np.zeros((8, 8), dtype=np.float32)
        amp1[2, 3] = 1.0
        dist1[2, 3] = 30.0  # two-way distance [m]
        np.save(pair / "AmplitudeOutput0001.npy", amp1)
        np.save(pair / "DistanceOutput0001.npy", dist1)

        amp2 = np.zeros((8, 8), dtype=np.float32)
        dist2 = np.zeros((8, 8), dtype=np.float32)
        amp2[5, 6] = 0.8
        dist2[5, 6] = 33.0  # two-way distance [m]
        np.save(pair / "AmplitudeOutput0002.npy", amp2)
        np.save(pair / "DistanceOutput0002.npy", dist2)

        radar_json = Path(tmp) / "radar_parameters_hybrid.json"
        payload = {
            "antenna_offsets_tx": {"Tx0": [0, 0, 0], "Tx1": [0, -0.0078, 0]},
            "antenna_offsets_rx": {
                "Rx0": [0, 0.00185, 0],
                "Rx1": [0, 0.0037, 0],
                "Rx2": [0, 0.00555, 0],
                "Rx3": [0, 0.0074, 0],
            },
        }
        radar_json.write_text(json.dumps(payload), encoding="utf-8")

        tx_pos, rx_pos = load_hybrid_radar_geometry(str(radar_json))
        assert tx_pos.shape == (2, 3)
        assert rx_pos.shape == (4, 3)

        paths = load_hybrid_paths_from_frames(
            root_dir=str(root),
            frame_indices=[1, 2],
            camera_fov_deg=90.0,
            mode="reflection",
            file_ext=".npy",
            amplitude_threshold=0.05,
            top_k_per_chirp=1,
            distance_limits_m=(1.0, 80.0),
        )
        assert len(paths) == 2
        assert len(paths[0]) == 1
        assert len(paths[1]) == 1

        d0 = paths[0][0].delay_s
        d1 = paths[1][0].delay_s
        assert abs(d0 - (30.0 / C0)) < 1e-9
        assert abs(d1 - (33.0 / C0)) < 1e-9

        radar = RadarConfig(
            fc_hz=77e9,
            slope_hz_per_s=20e12,
            fs_hz=20e6,
            samples_per_chirp=4096,
            tx_schedule=[0, 1],
        )
        adc = synth_fmcw_tdm(paths, tx_pos, rx_pos, radar)
        assert adc.shape == (4096, 2, 2, 4), adc.shape

        expected0 = radar.slope_hz_per_s * d0
        actual0 = dominant_freq_hz(adc[:, 0, 0, 0], radar.fs_hz)
        tol = 1.5 * radar.fs_hz / radar.samples_per_chirp
        assert abs(actual0 - expected0) <= tol, (actual0, expected0, tol)
        print("Hybrid frame adapter validation passed.")


if __name__ == "__main__":
    run()


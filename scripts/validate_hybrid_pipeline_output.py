#!/Library/Developer/CommandLineTools/usr/bin/python3
import json
import tempfile
from pathlib import Path

import numpy as np

from avxsim.pipeline import run_hybrid_frames_pipeline


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        frames_root = tmp_path / "frames"
        pair = frames_root / "Tx0Rx0"
        pair.mkdir(parents=True, exist_ok=True)

        for idx, (rtt_dist, amp) in enumerate([(30.0, 1.0), (33.0, 0.7)], start=1):
            amp_map = np.zeros((8, 8), dtype=np.float32)
            dist_map = np.zeros((8, 8), dtype=np.float32)
            amp_map[2 + idx, 3] = amp
            dist_map[2 + idx, 3] = rtt_dist
            np.save(pair / f"AmplitudeOutput{idx:04d}.npy", amp_map)
            np.save(pair / f"DistanceOutput{idx:04d}.npy", dist_map)

        radar_json = tmp_path / "radar_parameters_hybrid.json"
        radar_json.write_text(
            json.dumps(
                {
                    "antenna_offsets_tx": {"Tx0": [0, 0, 0], "Tx1": [0, -0.0078, 0]},
                    "antenna_offsets_rx": {
                        "Rx0": [0, 0.00185, 0],
                        "Rx1": [0, 0.0037, 0],
                        "Rx2": [0, 0.00555, 0],
                        "Rx3": [0, 0.0074, 0],
                    },
                }
            ),
            encoding="utf-8",
        )

        out_dir = tmp_path / "outputs"
        result = run_hybrid_frames_pipeline(
            frames_root_dir=str(frames_root),
            radar_json_path=str(radar_json),
            frame_indices=[1, 2],
            fc_hz=77e9,
            slope_hz_per_s=20e12,
            fs_hz=20e6,
            samples_per_chirp=2048,
            camera_fov_deg=90.0,
            mode="reflection",
            file_ext=".npy",
            amplitude_threshold=0.01,
            top_k_per_chirp=1,
            run_hybrid_estimation=True,
            estimation_nfft=96,
            estimation_range_bin_length=8,
            estimation_doppler_window="hann",
            output_dir=str(out_dir),
        )

        path_json = out_dir / "path_list.json"
        adc_npz = out_dir / "adc_cube.npz"
        est_npz = out_dir / "hybrid_estimation.npz"
        assert path_json.exists(), str(path_json)
        assert adc_npz.exists(), str(adc_npz)
        assert est_npz.exists(), str(est_npz)

        loaded = np.load(adc_npz)
        adc = loaded["adc"]
        assert adc.shape == (2048, 2, 2, 4), adc.shape
        meta = json.loads(str(loaded["metadata_json"]))
        assert meta["samples_per_chirp"] == 2048

        est_loaded = np.load(est_npz)
        assert est_loaded["fx_dop"].shape == (96, 2048)
        assert est_loaded["fx_ang"].shape == (96, 2048)
        assert est_loaded["fx_dop_max"].shape == (96, 1)

        assert "paths_by_chirp" in result
        assert len(result["paths_by_chirp"]) == 2
        assert "hybrid_estimation" in result
        print("Hybrid pipeline output validation passed.")


if __name__ == "__main__":
    run()

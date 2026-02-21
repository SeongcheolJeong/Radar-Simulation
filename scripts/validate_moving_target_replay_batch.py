#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _gaussian2d(shape, c0, c1, s0, s1, amp):
    y = np.arange(shape[0], dtype=np.float64)[:, None]
    x = np.arange(shape[1], dtype=np.float64)[None, :]
    z = np.exp(-0.5 * (((y - c0) / s0) ** 2 + ((x - c1) / s1) ** 2))
    return amp * z


def _write_est(path, rd, ra):
    np.savez_compressed(path, fx_dop_win=rd, fx_ang=ra)


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        rd_ref = _gaussian2d((96, 128), 42.0, 62.0, 6.5, 8.0, 10.0)
        ra_ref = _gaussian2d((96, 128), 53.0, 60.0, 7.0, 6.0, 7.5)

        ref_npz = tmp_path / "ref.npz"
        _write_est(ref_npz, rd_ref, ra_ref)

        good_npz = tmp_path / "good.npz"
        bad_npz = tmp_path / "bad.npz"
        _write_est(
            good_npz,
            np.roll(rd_ref * 1.01, shift=1, axis=0),
            np.roll(ra_ref * 0.99, shift=1, axis=0),
        )
        _write_est(
            bad_npz,
            np.roll(rd_ref, shift=12, axis=0),
            np.roll(ra_ref, shift=-10, axis=0),
        )

        profile_json = tmp_path / "scenario_profile.json"
        profile_json.write_text(
            json.dumps(
                {
                    "version": 1,
                    "scenario_id": "moving_target_case",
                    "created_utc": "2026-02-21T00:00:00+00:00",
                    "global_jones_matrix": [
                        {"re": 1.0, "im": 0.0},
                        {"re": 0.0, "im": 0.0},
                        {"re": 0.0, "im": 0.0},
                        {"re": 1.0, "im": 0.0},
                    ],
                    "parity_thresholds": {
                        "rd_peak_doppler_bin_abs_error_max": 2.0,
                        "rd_peak_range_bin_abs_error_max": 2.0,
                        "rd_peak_power_db_abs_error_max": 5.0,
                        "rd_centroid_doppler_bin_abs_error_max": 2.0,
                        "rd_centroid_range_bin_abs_error_max": 2.0,
                        "rd_spread_doppler_rel_error_max": 0.5,
                        "rd_spread_range_rel_error_max": 0.5,
                        "rd_shape_nmse_max": 0.3,
                        "ra_peak_angle_bin_abs_error_max": 2.0,
                        "ra_peak_range_bin_abs_error_max": 2.0,
                        "ra_peak_power_db_abs_error_max": 5.0,
                        "ra_centroid_angle_bin_abs_error_max": 2.0,
                        "ra_centroid_range_bin_abs_error_max": 2.0,
                        "ra_spread_angle_rel_error_max": 0.5,
                        "ra_spread_range_rel_error_max": 0.5,
                        "ra_shape_nmse_max": 0.3,
                    },
                    "motion_compensation_defaults": {
                        "enabled": True,
                        "fd_hz": 1000.0,
                        "chirp_interval_s": 6e-5,
                        "reference_tx": 0,
                    },
                    "reference_estimation_npz": str(ref_npz),
                }
            ),
            encoding="utf-8",
        )

        manifest_json = tmp_path / "manifest.json"
        manifest_json.write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "scenario_id": "moving_target_case",
                            "profile_json": str(profile_json),
                            "candidates": [
                                {"name": "good", "estimation_npz": str(good_npz)},
                                {"name": "bad", "estimation_npz": str(bad_npz)},
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        out_json = tmp_path / "replay_report.json"
        proc = subprocess.run(
            [
                "python3",
                "scripts/run_moving_target_replay_batch.py",
                "--manifest-json",
                str(manifest_json),
                "--output-json",
                str(out_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 2, proc.stdout + "\n" + proc.stderr
        assert "Replay batch evaluation completed." in proc.stdout, proc.stdout

        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["summary"]["case_count"] == 1
        assert report["summary"]["candidate_count"] == 2
        assert report["summary"]["pass_count"] == 1
        assert report["summary"]["fail_count"] == 1
        case0 = report["cases"][0]
        assert case0["scenario_id"] == "moving_target_case"
        assert case0["motion_compensation_defaults"]["enabled"] is True

        proc2 = subprocess.run(
            [
                "python3",
                "scripts/run_moving_target_replay_batch.py",
                "--manifest-json",
                str(manifest_json),
                "--output-json",
                str(out_json),
                "--allow-failures",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "fail: 1" in proc2.stdout, proc2.stdout

    print("Moving-target replay batch validation passed.")


if __name__ == "__main__":
    run()


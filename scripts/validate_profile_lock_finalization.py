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


def _write_est(path: Path, rd: np.ndarray, ra: np.ndarray) -> None:
    np.savez_compressed(path, fx_dop_win=rd, fx_ang=ra)


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        rd_ref = _gaussian2d((72, 96), 30.0, 44.0, 5.5, 7.0, 12.0)
        ra_ref = _gaussian2d((72, 96), 28.0, 41.0, 6.0, 5.5, 9.0)
        ref_npz = tmp_path / "reference.npz"
        _write_est(ref_npz, rd_ref, ra_ref)

        good1_npz = tmp_path / "good_case1.npz"
        good2_npz = tmp_path / "good_case2.npz"
        bad2_npz = tmp_path / "bad_case2.npz"
        _write_est(good1_npz, np.roll(rd_ref * 1.01, shift=1, axis=0), np.roll(ra_ref, shift=1, axis=0))
        _write_est(good2_npz, np.roll(rd_ref * 0.99, shift=1, axis=1), np.roll(ra_ref, shift=1, axis=1))
        _write_est(bad2_npz, np.roll(rd_ref, shift=11, axis=0), np.roll(ra_ref, shift=-12, axis=0))

        profile_ok = tmp_path / "profile_case_ok.json"
        profile_bad = tmp_path / "profile_case_bad.json"

        base_profile = {
            "version": 1,
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
            "reference_estimation_npz": str(ref_npz),
        }

        payload_ok = dict(base_profile)
        payload_ok["scenario_id"] = "moving_case_ok"
        payload_ok["motion_compensation_defaults"] = {
            "enabled": True,
            "fd_hz": 900.0,
            "chirp_interval_s": 6e-5,
            "reference_tx": 0,
        }
        profile_ok.write_text(json.dumps(payload_ok), encoding="utf-8")

        payload_bad = dict(base_profile)
        payload_bad["scenario_id"] = "moving_case_bad"
        payload_bad["motion_compensation_defaults"] = {
            "enabled": False,
            "fd_hz": None,
            "chirp_interval_s": None,
            "reference_tx": None,
        }
        profile_bad.write_text(json.dumps(payload_bad), encoding="utf-8")

        manifest_json = tmp_path / "replay_manifest.json"
        manifest_json.write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "scenario_id": "moving_case_ok",
                            "profile_json": str(profile_ok),
                            "candidates": [
                                {"name": "good_ok", "estimation_npz": str(good1_npz)},
                            ],
                        },
                        {
                            "scenario_id": "moving_case_bad",
                            "profile_json": str(profile_bad),
                            "candidates": [
                                {"name": "good_bad", "estimation_npz": str(good2_npz)},
                                {"name": "bad_bad", "estimation_npz": str(bad2_npz)},
                            ],
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

        replay_report_json = tmp_path / "replay_report.json"
        replay_proc = subprocess.run(
            [
                "python3",
                "scripts/run_moving_target_replay_batch.py",
                "--manifest-json",
                str(manifest_json),
                "--output-json",
                str(replay_report_json),
                "--allow-failures",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Replay batch evaluation completed." in replay_proc.stdout, replay_proc.stdout

        lock_json = tmp_path / "profile_lock.json"
        locked_dir = tmp_path / "locked_profiles"
        strict_proc = subprocess.run(
            [
                "python3",
                "scripts/finalize_scenario_profile_lock.py",
                "--replay-report-json",
                str(replay_report_json),
                "--output-lock-json",
                str(lock_json),
                "--output-locked-profile-dir",
                str(locked_dir),
                "--require-motion-defaults-enabled",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert strict_proc.returncode == 2, strict_proc.stdout + "\n" + strict_proc.stderr
        assert "Scenario profile lock finalization completed." in strict_proc.stdout, strict_proc.stdout

        lock_payload = json.loads(lock_json.read_text(encoding="utf-8"))
        assert lock_payload["summary"]["case_count"] == 2
        assert lock_payload["summary"]["locked_count"] == 1
        assert lock_payload["summary"]["unlocked_count"] == 1
        assert lock_payload["overall_lock_pass"] is False
        assert len(lock_payload["locked_profiles"]) == 2

        lock_by_id = {c["scenario_id"]: c for c in lock_payload["cases"]}
        assert lock_by_id["moving_case_ok"]["lock_pass"] is True
        assert lock_by_id["moving_case_bad"]["lock_pass"] is False
        assert len(lock_by_id["moving_case_bad"]["lock_reasons"]) >= 1

        locked_ok_json = locked_dir / "moving_case_ok.locked.json"
        locked_bad_json = locked_dir / "moving_case_bad.locked.json"
        assert locked_ok_json.exists()
        assert locked_bad_json.exists()

        locked_ok = json.loads(locked_ok_json.read_text(encoding="utf-8"))
        locked_bad = json.loads(locked_bad_json.read_text(encoding="utf-8"))
        assert locked_ok["profile_lock"]["locked"] is True
        assert locked_bad["profile_lock"]["locked"] is False

        lock_json_allow = tmp_path / "profile_lock_allow.json"
        relaxed_proc = subprocess.run(
            [
                "python3",
                "scripts/finalize_scenario_profile_lock.py",
                "--replay-report-json",
                str(replay_report_json),
                "--output-lock-json",
                str(lock_json_allow),
                "--allow-unlocked",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "overall_lock_pass" in relaxed_proc.stdout, relaxed_proc.stdout

    print("Scenario profile lock finalization validation passed.")


if __name__ == "__main__":
    run()

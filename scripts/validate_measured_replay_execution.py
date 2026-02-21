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


def _write_profile(path: Path, scenario_id: str, reference_npz: Path, motion_enabled: bool) -> None:
    payload = {
        "version": 1,
        "scenario_id": scenario_id,
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
        "reference_estimation_npz": str(reference_npz),
        "motion_compensation_defaults": {
            "enabled": bool(motion_enabled),
            "fd_hz": 1200.0 if motion_enabled else None,
            "chirp_interval_s": 6e-5 if motion_enabled else None,
            "reference_tx": 0 if motion_enabled else None,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        rd_ref = _gaussian2d((80, 100), 31.0, 45.0, 6.0, 7.0, 10.0)
        ra_ref = _gaussian2d((80, 100), 29.0, 43.0, 5.5, 6.5, 8.5)
        ref_npz = tmp_path / "reference.npz"
        _write_est(ref_npz, rd_ref, ra_ref)

        good_npz = tmp_path / "good.npz"
        bad_npz = tmp_path / "bad.npz"
        _write_est(good_npz, np.roll(rd_ref * 1.01, shift=1, axis=0), np.roll(ra_ref * 0.99, shift=1, axis=1))
        _write_est(bad_npz, np.roll(rd_ref, shift=12, axis=0), np.roll(ra_ref, shift=-11, axis=0))

        profile_good_json = tmp_path / "profile_good.json"
        profile_bad_json = tmp_path / "profile_bad.json"
        _write_profile(profile_good_json, "pack_good_case", ref_npz, motion_enabled=True)
        _write_profile(profile_bad_json, "pack_bad_case", ref_npz, motion_enabled=False)

        replay_manifest_good = tmp_path / "replay_manifest_good.json"
        replay_manifest_good.write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "scenario_id": "pack_good_case",
                            "profile_json": str(profile_good_json),
                            "candidates": [
                                {"name": "good", "estimation_npz": str(good_npz)},
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        replay_manifest_bad = tmp_path / "replay_manifest_bad.json"
        replay_manifest_bad.write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "scenario_id": "pack_bad_case",
                            "profile_json": str(profile_bad_json),
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

        plan_json = tmp_path / "measured_plan.json"
        plan_json.write_text(
            json.dumps(
                {
                    "packs": [
                        {
                            "pack_id": "pack_good",
                            "replay_manifest_json": str(replay_manifest_good),
                            "output_subdir": "pack_good_outputs",
                        },
                        {
                            "pack_id": "pack_bad",
                            "replay_manifest_json": str(replay_manifest_bad),
                            "lock_policy": {
                                "require_motion_defaults_enabled": True,
                            },
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

        out_root = tmp_path / "measured_outputs"
        summary_json = tmp_path / "measured_summary.json"

        proc_fail = subprocess.run(
            [
                "python3",
                "scripts/run_measured_replay_execution.py",
                "--plan-json",
                str(plan_json),
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(summary_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_fail.returncode == 2, proc_fail.stdout + "\n" + proc_fail.stderr
        assert "Measured replay execution completed." in proc_fail.stdout, proc_fail.stdout

        summary = json.loads(summary_json.read_text(encoding="utf-8"))
        assert summary["summary"]["pack_count"] == 2
        assert summary["summary"]["case_count"] == 2
        assert summary["summary"]["locked_count"] == 1
        assert summary["summary"]["unlocked_count"] == 1
        assert summary["overall_lock_pass"] is False

        pack_by_id = {p["pack_id"]: p for p in summary["packs"]}
        assert pack_by_id["pack_good"]["overall_lock_pass"] is True
        assert pack_by_id["pack_bad"]["overall_lock_pass"] is False

        good_out = Path(pack_by_id["pack_good"]["output_dir"])
        bad_out = Path(pack_by_id["pack_bad"]["output_dir"])
        assert (good_out / "replay_report.json").exists()
        assert (good_out / "profile_lock_report.json").exists()
        assert (good_out / "locked_profiles" / "pack_good_case.locked.json").exists()
        assert (bad_out / "locked_profiles" / "pack_bad_case.locked.json").exists()

        bad_lock_payload = json.loads((bad_out / "profile_lock_report.json").read_text(encoding="utf-8"))
        assert bad_lock_payload["overall_lock_pass"] is False

        summary_json_allow = tmp_path / "measured_summary_allow.json"
        proc_allow = subprocess.run(
            [
                "python3",
                "scripts/run_measured_replay_execution.py",
                "--plan-json",
                str(plan_json),
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(summary_json_allow),
                "--allow-unlocked",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "overall_lock_pass" in proc_allow.stdout, proc_allow.stdout

    print("Measured replay execution validation passed.")


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


def _write_radar_npz(path: Path, rd: np.ndarray, ra: np.ndarray, tag: str) -> None:
    payload = {
        "system_tag": tag,
        "rd_shape": list(rd.shape),
        "ra_shape": list(ra.shape),
    }
    np.savez(path, fx_dop_win=rd, fx_ang=ra, metadata_json=json.dumps(payload))


def _write_adc_npz(path: Path, adc: np.ndarray, tag: str, include_metadata: bool) -> None:
    if include_metadata:
        np.savez(path, adc=adc, metadata_json=json.dumps({"system_tag": tag, "shape": list(adc.shape)}))
    else:
        np.savez(path, adc=adc)


def _write_path_json(path: Path, rows: list) -> None:
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="validate_run_avx_export_benchmark_") as td:
        root = Path(td)

        rd_truth = np.full((16, 64), 1.0e-12, dtype=np.float64)
        ra_truth = np.full((12, 64), 1.0e-12, dtype=np.float64)
        rd_truth[5, 28] = 2.0
        rd_truth[5, 29] = 1.2
        rd_truth[6, 28] = 0.9
        ra_truth[6, 28] = 1.5
        ra_truth[6, 29] = 0.8
        ra_truth[5, 28] = 0.6

        rd_candidate = rd_truth.copy()
        ra_candidate = ra_truth.copy()
        rd_reference = np.roll(rd_truth, 1, axis=1)
        ra_reference = np.roll(ra_truth, 1, axis=1)

        candidate_radar = root / "candidate_radar_map.npz"
        reference_radar = root / "reference_radar_map.npz"
        truth_radar = root / "truth_radar_map.npz"
        _write_radar_npz(candidate_radar, rd_candidate, ra_candidate, "candidate")
        _write_radar_npz(reference_radar, rd_reference, ra_reference, "reference")
        _write_radar_npz(truth_radar, rd_truth, ra_truth, "truth")

        shape = (128, 6, 2, 2)
        idx = np.arange(np.prod(shape), dtype=np.float64).reshape(shape)
        base_adc = np.exp(1j * (idx * 1.0e-3)).astype(np.complex64)
        candidate_adc = base_adc.copy()
        reference_adc = (0.7 * base_adc).astype(np.complex64)

        candidate_adc_npz = root / "candidate_adc.npz"
        reference_adc_npz = root / "reference_adc.npz"
        _write_adc_npz(candidate_adc_npz, candidate_adc, "candidate", include_metadata=True)
        _write_adc_npz(reference_adc_npz, reference_adc, "reference", include_metadata=False)

        candidate_paths = []
        reference_paths = []
        for chirp_idx in range(6):
            candidate_paths.append(
                [
                    {
                        "delay_s": 2.0 * 25.0 / 299_792_458.0,
                        "doppler_hz": 0.0,
                        "unit_direction": [1.0, 0.0, 0.0],
                        "amp_complex": {"re": 1.0e-3, "im": 0.0},
                        "path_id": f"cand_path_{chirp_idx}",
                        "material_tag": "metal",
                        "reflection_order": 1,
                    }
                ]
            )
            reference_paths.append(
                [
                    {
                        "delay_s": 2.0 * 25.0 / 299_792_458.0,
                        "doppler_hz": 0.0,
                        "unit_direction": [1.0, 0.0, 0.0],
                        "amp": 1.0e-3,
                    }
                ]
            )

        candidate_path_json = root / "candidate_path_list.json"
        reference_path_json = root / "reference_path_list.json"
        _write_path_json(candidate_path_json, candidate_paths)
        _write_path_json(reference_path_json, reference_paths)

        thresholds_json = root / "thresholds.json"
        thresholds_json.write_text(
            json.dumps(
                {
                    "rd_peak_doppler_bin_abs_error_max": 100.0,
                    "rd_peak_range_bin_abs_error_max": 100.0,
                    "rd_peak_power_db_abs_error_max": 100.0,
                    "rd_centroid_doppler_bin_abs_error_max": 100.0,
                    "rd_centroid_range_bin_abs_error_max": 100.0,
                    "rd_spread_doppler_rel_error_max": 100.0,
                    "rd_spread_range_rel_error_max": 100.0,
                    "rd_shape_nmse_max": 100.0,
                    "ra_peak_angle_bin_abs_error_max": 100.0,
                    "ra_peak_range_bin_abs_error_max": 100.0,
                    "ra_peak_power_db_abs_error_max": 100.0,
                    "ra_centroid_angle_bin_abs_error_max": 100.0,
                    "ra_centroid_range_bin_abs_error_max": 100.0,
                    "ra_spread_angle_rel_error_max": 100.0,
                    "ra_spread_range_rel_error_max": 100.0,
                    "ra_shape_nmse_max": 100.0,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        out_json = root / "benchmark_summary.json"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        run_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_avx_export_benchmark.py",
                "--candidate-label",
                "po_sbr",
                "--reference-label",
                "avx_export",
                "--truth-label",
                "truth_lab",
                "--candidate-radar-map-npz",
                str(candidate_radar),
                "--reference-radar-map-npz",
                str(reference_radar),
                "--truth-radar-map-npz",
                str(truth_radar),
                "--candidate-path-list-json",
                str(candidate_path_json),
                "--reference-path-list-json",
                str(reference_path_json),
                "--candidate-adc-cube-npz",
                str(candidate_adc_npz),
                "--reference-adc-cube-npz",
                str(reference_adc_npz),
                "--thresholds-json",
                str(thresholds_json),
                "--output-json",
                str(out_json),
                "--strict-ready",
                "--strict-candidate-better-physics",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if run_proc.returncode != 0:
            raise AssertionError(
                "run_avx_export_benchmark.py failed\n"
                f"stdout:\n{run_proc.stdout}\n"
                f"stderr:\n{run_proc.stderr}\n"
            )
        assert "AVX export benchmark completed." in run_proc.stdout, run_proc.stdout

        validate_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/validate_avx_export_benchmark_report.py",
                "--summary-json",
                str(out_json),
                "--require-ready",
                "--require-truth-comparison",
                "--require-candidate-better-physics",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "validate_avx_export_benchmark_report: pass" in validate_proc.stdout, validate_proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["comparison_status"] == "ready"
        assert (
            payload["physics"]["better_than_reference_physics_claim"] == "candidate_better_vs_truth"
        )
        assert (
            payload["function_usability"]["better_than_reference_function_usability_claim"]
            == "candidate_better"
        )

    print("validate_run_avx_export_benchmark: pass")


if __name__ == "__main__":
    run()

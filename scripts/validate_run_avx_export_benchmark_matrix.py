#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


def _write_radar_npz(path: Path, rd: np.ndarray, ra: np.ndarray, tag: str) -> None:
    np.savez(path, fx_dop_win=rd, fx_ang=ra, metadata_json=json.dumps({"tag": tag}))


def _write_adc_npz(path: Path, adc: np.ndarray) -> None:
    np.savez(path, adc=adc, metadata_json=json.dumps({"shape": list(adc.shape)}))


def _write_path_json(path: Path) -> None:
    rows = []
    for chirp_idx in range(4):
        rows.append(
            [
                {
                    "delay_s": 2.0 * 25.0 / 299_792_458.0,
                    "doppler_hz": 0.0,
                    "unit_direction": [1.0, 0.0, 0.0],
                    "amp_complex": {"re": 1.0e-3, "im": 0.0},
                    "path_id": f"path_{chirp_idx}",
                    "material_tag": "metal",
                    "reflection_order": 1,
                }
            ]
        )
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def _mk_profile(root: Path, profile: str, truth_rd: np.ndarray, truth_ra: np.ndarray, cand_rd: np.ndarray, cand_ra: np.ndarray, ref_rd: np.ndarray, ref_ra: np.ndarray) -> None:
    for backend, rd, ra in (
        ("analytic_targets", truth_rd, truth_ra),
        ("po_sbr_rt", cand_rd, cand_ra),
        ("sionna_rt", ref_rd, ref_ra),
    ):
        out = root / profile / "golden_outputs" / backend / "pipeline_outputs"
        out.mkdir(parents=True, exist_ok=True)
        _write_radar_npz(out / "radar_map.npz", rd=rd, ra=ra, tag=f"{profile}:{backend}")
        _write_path_json(out / "path_list.json")
        adc = np.ones((32, 4, 2, 2), dtype=np.complex64)
        _write_adc_npz(out / "adc_cube.npz", adc=adc)


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="validate_run_avx_export_benchmark_matrix_") as td:
        root = Path(td)
        matrix_root = root / "matrix"

        rd_truth = np.full((16, 64), 1.0e-12, dtype=np.float64)
        ra_truth = np.full((12, 64), 1.0e-12, dtype=np.float64)
        rd_truth[5, 27] = 2.0
        ra_truth[6, 27] = 1.5

        # Profile A: candidate is one-bin shifted, reference is two-bin shifted.
        _mk_profile(
            root=matrix_root,
            profile="profile_a",
            truth_rd=rd_truth,
            truth_ra=ra_truth,
            cand_rd=np.roll(rd_truth, 1, axis=1),
            cand_ra=np.roll(ra_truth, 1, axis=1),
            ref_rd=np.roll(rd_truth, 2, axis=1),
            ref_ra=np.roll(ra_truth, 2, axis=1),
        )

        # Profile B: all equal.
        _mk_profile(
            root=matrix_root,
            profile="profile_b",
            truth_rd=rd_truth,
            truth_ra=ra_truth,
            cand_rd=rd_truth.copy(),
            cand_ra=ra_truth.copy(),
            ref_rd=rd_truth.copy(),
            ref_ra=ra_truth.copy(),
        )

        out_root = root / "out"
        out_json = root / "matrix_summary.json"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_avx_export_benchmark_matrix.py",
                "--matrix-root",
                str(matrix_root),
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_json),
                "--auto-tune-candidate-vs-truth",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(
                "run_avx_export_benchmark_matrix.py failed\n"
                f"stdout:\n{proc.stdout}\n"
                f"stderr:\n{proc.stderr}\n"
            )
        assert "AVX export benchmark matrix completed." in proc.stdout, proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        counts = payload["counts"]
        assert counts["total_profiles"] == 2, counts
        assert counts["ready_count"] >= 1, counts
        assert counts["physics_worse_count"] == 0, counts
        assert counts["physics_better_count"] >= 1, counts

    print("validate_run_avx_export_benchmark_matrix: pass")


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Tuple


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _write_sionna_reference_scene(root: Path) -> Path:
    return _write_json(
        root / "scene_analytic_reference.json",
        {
            "scene_id": "sionna_parity_reference",
            "backend": {
                "type": "analytic_targets",
                "n_chirps": 4,
                "chirp_interval_s": 4.0e-5,
                "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                "rx_pos_m": [
                    [0.0, 0.00185, 0.0],
                    [0.0, 0.0037, 0.0],
                    [0.0, 0.00555, 0.0],
                    [0.0, 0.0074, 0.0],
                ],
                "targets": [
                    {
                        "range_m": 25.0,
                        "radial_velocity_mps": 0.0,
                        "az_deg": 0.0,
                        "el_deg": 0.0,
                        "amp": 1.0,
                        "range_amp_exponent": 2.0,
                        "path_id": "ref_path",
                    }
                ],
                "noise_sigma": 0.0,
            },
            "radar": {
                "fc_hz": 77e9,
                "slope_hz_per_s": 20e12,
                "fs_hz": 20e6,
                "samples_per_chirp": 1024,
            },
            "map_config": {
                "nfft_range": 1024,
                "nfft_doppler": 64,
                "nfft_angle": 32,
                "range_bin_limit": 128,
            },
        },
    )


def _write_sionna_candidate_scene(root: Path) -> Path:
    delay_s = 2.0 * 25.0 / 299_792_458.0
    amp = 1.0 / (25.0 * 25.0)
    sionna_paths_json = _write_json(
        root / "sionna_paths.json",
        {
            "version": 1,
            "paths_by_chirp": [
                [
                    {
                        "delay_s": delay_s,
                        "doppler_hz": 0.0,
                        "unit_direction": [1.0, 0.0, 0.0],
                        "amp": amp,
                        "path_id": "cand_path_0",
                        "material_tag": "sionna_rt",
                        "reflection_order": 1,
                    }
                ],
                [
                    {
                        "delay_s": delay_s,
                        "doppler_hz": 0.0,
                        "unit_direction": [1.0, 0.0, 0.0],
                        "amp": amp,
                        "path_id": "cand_path_1",
                        "material_tag": "sionna_rt",
                        "reflection_order": 1,
                    }
                ],
                [
                    {
                        "delay_s": delay_s,
                        "doppler_hz": 0.0,
                        "unit_direction": [1.0, 0.0, 0.0],
                        "amp": amp,
                        "path_id": "cand_path_2",
                        "material_tag": "sionna_rt",
                        "reflection_order": 1,
                    }
                ],
                [
                    {
                        "delay_s": delay_s,
                        "doppler_hz": 0.0,
                        "unit_direction": [1.0, 0.0, 0.0],
                        "amp": amp,
                        "path_id": "cand_path_3",
                        "material_tag": "sionna_rt",
                        "reflection_order": 1,
                    }
                ],
            ],
        },
    )
    return _write_json(
        root / "scene_sionna_candidate.json",
        {
            "scene_id": "sionna_parity_candidate",
            "backend": {
                "type": "sionna_rt",
                "n_chirps": 4,
                "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                "rx_pos_m": [
                    [0.0, 0.00185, 0.0],
                    [0.0, 0.0037, 0.0],
                    [0.0, 0.00555, 0.0],
                    [0.0, 0.0074, 0.0],
                ],
                "sionna_paths_json": str(sionna_paths_json),
                "noise_sigma": 0.0,
            },
            "radar": {
                "fc_hz": 77e9,
                "slope_hz_per_s": 20e12,
                "fs_hz": 20e6,
                "samples_per_chirp": 1024,
            },
            "map_config": {
                "nfft_range": 1024,
                "nfft_doppler": 64,
                "nfft_angle": 32,
                "range_bin_limit": 128,
            },
        },
    )


def _write_po_sbr_reference_scene(root: Path) -> Path:
    return _write_json(
        root / "scene_analytic_reference.json",
        {
            "scene_id": "po_sbr_parity_reference",
            "backend": {
                "type": "analytic_targets",
                "n_chirps": 4,
                "chirp_interval_s": 4.0e-5,
                "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                "rx_pos_m": [
                    [0.0, 0.00185, 0.0],
                    [0.0, 0.0037, 0.0],
                    [0.0, 0.00555, 0.0],
                    [0.0, 0.0074, 0.0],
                ],
                "targets": [
                    {
                        "range_m": 23.0,
                        "radial_velocity_mps": 0.0,
                        "az_deg": 0.0,
                        "el_deg": 0.0,
                        "amp": 1.0,
                        "range_amp_exponent": 2.0,
                        "path_id": "ref_path",
                    }
                ],
                "noise_sigma": 0.0,
            },
            "radar": {
                "fc_hz": 77e9,
                "slope_hz_per_s": 20e12,
                "fs_hz": 20e6,
                "samples_per_chirp": 1024,
            },
            "map_config": {
                "nfft_range": 1024,
                "nfft_doppler": 64,
                "nfft_angle": 32,
                "range_bin_limit": 128,
            },
        },
    )


def _write_po_sbr_candidate_scene(root: Path) -> Path:
    amp = 1.0 / (23.0 * 23.0)
    po_sbr_paths_json = _write_json(
        root / "po_sbr_paths.json",
        {
            "version": 1,
            "paths": [
                {
                    "chirp_index": 0,
                    "range_m": 23.0,
                    "range_mode": "one_way",
                    "radial_velocity_mps": 0.0,
                    "az_deg": 0.0,
                    "el_deg": 0.0,
                    "amp": amp,
                    "path_id": "po_path_0",
                    "reflection_order": 1,
                },
                {
                    "chirp_index": 1,
                    "range_m": 23.0,
                    "range_mode": "one_way",
                    "radial_velocity_mps": 0.0,
                    "az_deg": 0.0,
                    "el_deg": 0.0,
                    "amp": amp,
                    "path_id": "po_path_1",
                    "reflection_order": 1,
                },
                {
                    "chirp_index": 2,
                    "range_m": 23.0,
                    "range_mode": "one_way",
                    "radial_velocity_mps": 0.0,
                    "az_deg": 0.0,
                    "el_deg": 0.0,
                    "amp": amp,
                    "path_id": "po_path_2",
                    "reflection_order": 1,
                },
                {
                    "chirp_index": 3,
                    "range_m": 23.0,
                    "range_mode": "one_way",
                    "radial_velocity_mps": 0.0,
                    "az_deg": 0.0,
                    "el_deg": 0.0,
                    "amp": amp,
                    "path_id": "po_path_3",
                    "reflection_order": 1,
                },
            ],
        },
    )
    return _write_json(
        root / "scene_po_sbr_candidate.json",
        {
            "scene_id": "po_sbr_parity_candidate",
            "backend": {
                "type": "po_sbr_rt",
                "n_chirps": 4,
                "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                "rx_pos_m": [
                    [0.0, 0.00185, 0.0],
                    [0.0, 0.0037, 0.0],
                    [0.0, 0.00555, 0.0],
                    [0.0, 0.0074, 0.0],
                ],
                "po_sbr_paths_json": str(po_sbr_paths_json),
                "noise_sigma": 0.0,
            },
            "radar": {
                "fc_hz": 77e9,
                "slope_hz_per_s": 20e12,
                "fs_hz": 20e6,
                "samples_per_chirp": 1024,
            },
            "map_config": {
                "nfft_range": 1024,
                "nfft_doppler": 64,
                "nfft_angle": 32,
                "range_bin_limit": 128,
            },
        },
    )


CASE_BUILDERS: Dict[str, Tuple[str, Callable[[Path], Path], Callable[[Path], Path]]] = {
    "sionna_rt": (
        "scene_backend_parity_sionna_rt",
        _write_sionna_reference_scene,
        _write_sionna_candidate_scene,
    ),
    "po_sbr_rt": (
        "scene_backend_parity_po_sbr_rt",
        _write_po_sbr_reference_scene,
        _write_po_sbr_candidate_scene,
    ),
}


def run_scene_backend_parity_case(
    *,
    case_name: str,
    repo_root: Path,
    output_root: Path,
    output_json: Path,
    python_bin: str = "",
) -> Dict[str, Any]:
    if case_name not in CASE_BUILDERS:
        raise KeyError(f"unknown case_name: {case_name}")

    report_name, write_reference_scene, write_candidate_scene = CASE_BUILDERS[case_name]
    output_root = output_root.expanduser().resolve()
    output_json = output_json.expanduser().resolve()
    python_text = str(python_bin).strip() or sys.executable

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    scene_root = output_root / "scenes"
    scene_root.mkdir(parents=True, exist_ok=True)
    reference_scene_json = write_reference_scene(scene_root)
    candidate_scene_json = write_candidate_scene(scene_root)
    raw_summary_json = output_root / "scene_backend_parity_summary.json"

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    proc = subprocess.run(
        [
            python_text,
            str((repo_root / "scripts" / "run_scene_backend_parity.py").resolve()),
            "--reference-scene-json",
            str(reference_scene_json),
            "--candidate-scene-json",
            str(candidate_scene_json),
            "--output-root",
            str(output_root),
            "--output-summary-json",
            str(raw_summary_json),
        ],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{report_name} failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}\n"
        )

    raw_payload = json.loads(raw_summary_json.read_text(encoding="utf-8"))
    if not isinstance(raw_payload, dict):
        raise AssertionError(f"expected object json at {raw_summary_json}")

    report = {
        "report_name": report_name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "case_name": case_name,
        "output_root": str(output_root),
        "raw_summary_json": str(raw_summary_json),
        "reference_scene_json": str(reference_scene_json),
        "candidate_scene_json": str(candidate_scene_json),
        "reference_backend_type": str(raw_payload.get("reference_backend_type", "")),
        "candidate_backend_type": str(raw_payload.get("candidate_backend_type", "")),
        "reference_radar_map_npz": str(raw_payload.get("reference_radar_map_npz", "")),
        "candidate_radar_map_npz": str(raw_payload.get("candidate_radar_map_npz", "")),
        "parity": raw_payload.get("parity", {}),
        "pass": bool((raw_payload.get("parity") or {}).get("pass", False)),
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

#!/usr/bin/env python3
"""Build a frontend-ready radar simulation demo artifact bundle.

This script generates an analytic object-scene example and emits:
- path_list.json
- adc_cube.npz
- radar_map.npz
- visuals/*.png (RD, RA, ADC, path scatter)
- summary JSON consumed by frontend/avx_like_dashboard.html
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import numpy as np

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


C0 = 299_792_458.0

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: E402
except Exception:
    plt = None


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_output_root = repo_root / "data" / "demo" / "frontend_quickstart_v1"
    default_summary = repo_root / "docs" / "reports" / "frontend_quickstart_v1.json"

    p = argparse.ArgumentParser(description="Build frontend demo artifacts from analytic scene")
    p.add_argument(
        "--output-root",
        default=str(default_output_root),
        help="Directory that will contain scene/output/visuals",
    )
    p.add_argument(
        "--summary-json",
        default=str(default_summary),
        help="Output summary JSON path for frontend",
    )
    p.add_argument(
        "--scene-json",
        default=None,
        help="Optional existing scene JSON path (default: generate built-in analytic scene)",
    )
    p.add_argument(
        "--skip-visuals",
        action="store_true",
        help="Skip PNG visual generation",
    )
    return p.parse_args()


def _default_scene_payload() -> Dict[str, Any]:
    today = date.today().isoformat().replace("-", "_")
    return {
        "scene_id": f"frontend_quickstart_{today}",
        "backend": {
            "type": "analytic_targets",
            "n_chirps": 16,
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
                    "path_id": "front_static_car",
                    "material_tag": "vehicle_static",
                    "reflection_order": 1,
                    "range_m": 24.0,
                    "radial_velocity_mps": 0.0,
                    "az_deg": 6.0,
                    "el_deg": 0.0,
                    "amp": 1.0,
                    "range_amp_exponent": 2.0,
                },
                {
                    "path_id": "front_moving_car",
                    "material_tag": "vehicle_moving",
                    "reflection_order": 1,
                    "range_m": 35.0,
                    "radial_velocity_mps": -8.0,
                    "az_deg": -3.0,
                    "el_deg": 0.0,
                    "amp": {"re": 0.9, "im": 0.2},
                    "range_amp_exponent": 2.2,
                },
                {
                    "path_id": "right_slow_target",
                    "material_tag": "pedestrian",
                    "reflection_order": 1,
                    "range_m": 48.0,
                    "radial_velocity_mps": 2.0,
                    "az_deg": 14.0,
                    "el_deg": 0.0,
                    "amp": {"re": 0.45, "im": -0.05},
                    "range_amp_exponent": 2.1,
                },
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
            "range_bin_limit": 256,
        },
    }


def _top_peaks(
    matrix: np.ndarray,
    row_key: str,
    col_key: str,
    top_k: int = 6,
) -> List[Dict[str, Any]]:
    arr = np.asarray(matrix, dtype=np.float64)
    if arr.ndim != 2 or arr.size == 0:
        return []

    max_power = float(np.max(arr))
    if not np.isfinite(max_power) or max_power <= 0.0:
        max_power = float(np.finfo(np.float64).tiny)

    flat_idx = np.argsort(arr.ravel())[::-1][: int(top_k)]
    out: List[Dict[str, Any]] = []
    for idx in flat_idx:
        r, c = np.unravel_index(int(idx), arr.shape)
        power = float(arr[r, c])
        rel_db = 10.0 * np.log10(max(power, np.finfo(np.float64).tiny) / max_power)
        out.append(
            {
                row_key: int(r),
                col_key: int(c),
                "power": power,
                "rel_db": float(rel_db),
            }
        )
    return out


def _save_visuals(
    output_root: Path,
    adc: np.ndarray,
    rd: np.ndarray,
    ra: np.ndarray,
    first_chirp_paths: List[Mapping[str, Any]],
    fc_hz: float,
) -> Dict[str, str]:
    if plt is None:
        raise RuntimeError(
            "matplotlib is required for visuals. Use .venv-sionna311 python or pass --skip-visuals."
        )

    visual_dir = output_root / "visuals"
    visual_dir.mkdir(parents=True, exist_ok=True)

    rd_safe = np.maximum(np.asarray(rd, dtype=np.float64), np.finfo(np.float64).tiny)
    ra_safe = np.maximum(np.asarray(ra, dtype=np.float64), np.finfo(np.float64).tiny)

    rd_db = 10.0 * np.log10(rd_safe / float(np.max(rd_safe)))
    ra_db = 10.0 * np.log10(ra_safe / float(np.max(ra_safe)))

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(rd_db, aspect="auto", origin="lower", cmap="turbo", vmin=-50.0, vmax=0.0)
    ax.set_title("Range-Doppler (dB)")
    ax.set_xlabel("Range bin")
    ax.set_ylabel("Doppler bin")
    fig.colorbar(im, ax=ax, label="dB rel")
    rd_png = visual_dir / "rd_map.png"
    fig.tight_layout()
    fig.savefig(rd_png, dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(ra_db, aspect="auto", origin="lower", cmap="turbo", vmin=-50.0, vmax=0.0)
    ax.set_title("Range-Angle (dB)")
    ax.set_xlabel("Range bin")
    ax.set_ylabel("Angle bin")
    fig.colorbar(im, ax=ax, label="dB rel")
    ra_png = visual_dir / "ra_map.png"
    fig.tight_layout()
    fig.savefig(ra_png, dpi=140)
    plt.close(fig)

    adc_tx0_rx0 = np.abs(np.asarray(adc[:, :, 0, 0], dtype=np.complex128)).T
    adc_tx0_rx0 = np.maximum(adc_tx0_rx0, np.finfo(np.float64).tiny)
    adc_db = 20.0 * np.log10(adc_tx0_rx0 / float(np.max(adc_tx0_rx0)))

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(adc_db, aspect="auto", origin="lower", cmap="magma", vmin=-60.0, vmax=0.0)
    ax.set_title("ADC magnitude (Tx0-Rx0, dB)")
    ax.set_xlabel("Fast-time sample")
    ax.set_ylabel("Chirp")
    fig.colorbar(im, ax=ax, label="dB rel")
    adc_png = visual_dir / "adc_tx0_rx0.png"
    fig.tight_layout()
    fig.savefig(adc_png, dpi=140)
    plt.close(fig)

    lam = C0 / float(fc_hz)
    ranges = []
    velocities = []
    labels = []
    amps_db = []
    for p in first_chirp_paths:
        delay_s = float(p.get("delay_s", 0.0))
        doppler_hz = float(p.get("doppler_hz", 0.0))
        amp_re = float(p.get("amp_complex", {}).get("re", 0.0))
        amp_im = float(p.get("amp_complex", {}).get("im", 0.0))
        amp_abs = max(np.hypot(amp_re, amp_im), 1e-15)
        ranges.append(0.5 * C0 * delay_s)
        velocities.append(0.5 * lam * doppler_hz)
        labels.append(str(p.get("path_id", "path")))
        amps_db.append(20.0 * np.log10(amp_abs))

    fig, ax = plt.subplots(figsize=(8, 4))
    if ranges:
        sc = ax.scatter(ranges, velocities, c=amps_db, cmap="viridis", s=80, edgecolors="k")
        for i, name in enumerate(labels):
            ax.annotate(name, (ranges[i], velocities[i]), textcoords="offset points", xytext=(5, 5), fontsize=8)
        fig.colorbar(sc, ax=ax, label="Amplitude (dB)")
    ax.set_title("First chirp path scatter")
    ax.set_xlabel("Range (m)")
    ax.set_ylabel("Radial velocity (m/s)")
    ax.grid(True, alpha=0.25)
    path_png = visual_dir / "path_scatter_chirp0.png"
    fig.tight_layout()
    fig.savefig(path_png, dpi=140)
    plt.close(fig)

    return {
        "rd_map_png": str(rd_png.resolve()),
        "ra_map_png": str(ra_png.resolve()),
        "adc_tx0_rx0_png": str(adc_png.resolve()),
        "path_scatter_chirp0_png": str(path_png.resolve()),
    }


def _build_summary(
    scene_json: Path,
    output_dir: Path,
    summary_json: Path,
    visuals: Optional[Dict[str, str]],
) -> Dict[str, Any]:
    paths = json.loads((output_dir / "path_list.json").read_text(encoding="utf-8"))
    if not isinstance(paths, list):
        raise ValueError("path_list.json must be a list")

    with np.load(str(output_dir / "adc_cube.npz"), allow_pickle=False) as adc_payload:
        adc = np.asarray(adc_payload["adc"])
        adc_meta = None
        if "metadata_json" in adc_payload:
            raw = adc_payload["metadata_json"]
            adc_meta = json.loads(str(raw.tolist()))

    with np.load(str(output_dir / "radar_map.npz"), allow_pickle=False) as map_payload:
        rd = np.asarray(map_payload["fx_dop_win"], dtype=np.float64)
        ra = np.asarray(map_payload["fx_ang"], dtype=np.float64)
        map_meta = None
        if "metadata_json" in map_payload:
            raw = map_payload["metadata_json"]
            map_meta = json.loads(str(raw.tolist()))

    first_chirp_paths = paths[0] if len(paths) > 0 and isinstance(paths[0], list) else []

    payload: Dict[str, Any] = {
        "scene_json": str(scene_json.resolve()),
        "outputs": {
            "path_list_json": str((output_dir / "path_list.json").resolve()),
            "adc_cube_npz": str((output_dir / "adc_cube.npz").resolve()),
            "radar_map_npz": str((output_dir / "radar_map.npz").resolve()),
        },
        "path_summary": {
            "n_chirps": int(len(paths)),
            "path_count_total": int(sum(len(chirp) for chirp in paths)),
            "path_count_per_chirp": [int(len(chirp)) for chirp in paths],
            "first_chirp_paths": first_chirp_paths,
        },
        "adc_summary": {
            "shape": [int(x) for x in adc.shape],
            "dtype": str(adc.dtype),
            "abs_mean": float(np.mean(np.abs(adc))),
            "abs_max": float(np.max(np.abs(adc))),
            "metadata": adc_meta,
        },
        "radar_map_summary": {
            "rd_shape": [int(x) for x in rd.shape],
            "ra_shape": [int(x) for x in ra.shape],
            "rd_top_peaks": _top_peaks(rd, "doppler_bin", "range_bin", top_k=6),
            "ra_top_peaks": _top_peaks(ra, "angle_bin", "range_bin", top_k=6),
            "metadata": map_meta,
        },
    }

    if visuals is not None:
        payload["visuals"] = visuals

    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    args = parse_args()

    output_root = Path(args.output_root).expanduser().resolve()
    summary_json = Path(args.summary_json).expanduser().resolve()
    output_dir = output_root / "output"

    output_dir.mkdir(parents=True, exist_ok=True)

    if args.scene_json is not None:
        scene_json = Path(args.scene_json).expanduser().resolve()
        if not scene_json.exists():
            raise FileNotFoundError(f"scene json not found: {scene_json}")
    else:
        scene_json = output_root / "scene_frontend_quickstart.json"
        scene_payload = _default_scene_payload()
        scene_json.write_text(json.dumps(scene_payload, indent=2), encoding="utf-8")

    run_out = run_object_scene_to_radar_map_json(
        scene_json_path=str(scene_json),
        output_dir=str(output_dir),
        run_hybrid_estimation=False,
    )

    visuals = None
    if not bool(args.skip_visuals):
        paths = json.loads((output_dir / "path_list.json").read_text(encoding="utf-8"))
        first_chirp_paths = paths[0] if len(paths) > 0 and isinstance(paths[0], list) else []
        with np.load(str(output_dir / "adc_cube.npz"), allow_pickle=False) as adc_payload:
            adc = np.asarray(adc_payload["adc"])
            adc_meta = None
            if "metadata_json" in adc_payload:
                adc_meta = json.loads(str(adc_payload["metadata_json"].tolist()))
        with np.load(str(output_dir / "radar_map.npz"), allow_pickle=False) as map_payload:
            rd = np.asarray(map_payload["fx_dop_win"], dtype=np.float64)
            ra = np.asarray(map_payload["fx_ang"], dtype=np.float64)

        fc_hz = float((adc_meta or {}).get("fc_hz", 77e9))
        visuals = _save_visuals(
            output_root=output_root,
            adc=adc,
            rd=rd,
            ra=ra,
            first_chirp_paths=first_chirp_paths,
            fc_hz=fc_hz,
        )

    summary = _build_summary(
        scene_json=scene_json,
        output_dir=output_dir,
        summary_json=summary_json,
        visuals=visuals,
    )

    print("frontend demo example build completed.")
    print(f"  scene_json: {scene_json}")
    print(f"  path_list_json: {run_out['path_list_json']}")
    print(f"  adc_cube_npz: {run_out['adc_cube_npz']}")
    print(f"  radar_map_npz: {run_out['radar_map_npz']}")
    if visuals is not None:
        print("  visuals:")
        print(f"    rd_map: {visuals['rd_map_png']}")
        print(f"    ra_map: {visuals['ra_map_png']}")
        print(f"    adc_tx0_rx0: {visuals['adc_tx0_rx0_png']}")
        print(f"    path_scatter: {visuals['path_scatter_chirp0_png']}")
    print(f"  summary_json: {summary_json}")
    print(f"  paths_per_chirp: {summary['path_summary']['path_count_per_chirp']}")


if __name__ == "__main__":
    main()

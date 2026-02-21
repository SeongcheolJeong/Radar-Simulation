#!/Library/Developer/CommandLineTools/usr/bin/python3
import argparse
import glob

from avxsim.calibration import load_global_jones_matrix_json
from avxsim.pipeline import run_hybrid_frames_pipeline


def _resolve_optional_glob_list(pattern: str):
    if pattern is None:
        return None
    matches = sorted(glob.glob(pattern))
    if not matches:
        raise ValueError(f"no files matched pattern: {pattern}")
    return matches


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="HybridDynamicRT frame ingest -> canonical path/ADC outputs")
    p.add_argument("--frames-root", required=True, help="Root dir containing Tx*Rx* frame folders")
    p.add_argument("--radar-json", required=True, help="Path to radar_parameters_hybrid.json")
    p.add_argument("--frame-start", type=int, required=True, help="Start frame index (inclusive)")
    p.add_argument("--frame-end", type=int, required=True, help="End frame index (inclusive)")
    p.add_argument("--camera-fov-deg", type=float, required=True, help="Camera FoV in degrees")
    p.add_argument("--mode", choices=["reflection", "scattering"], default="reflection")
    p.add_argument("--file-ext", default=".exr", help="Frame file extension, e.g. .exr or .npy")
    p.add_argument("--fc-hz", type=float, default=77e9)
    p.add_argument("--slope-hz-per-s", type=float, default=20e12)
    p.add_argument("--fs-hz", type=float, default=20e6)
    p.add_argument("--samples-per-chirp", type=int, default=4096)
    p.add_argument("--amplitude-threshold", type=float, default=0.0)
    p.add_argument("--distance-min-m", type=float, default=0.0)
    p.add_argument("--distance-max-m", type=float, default=100.0)
    p.add_argument("--top-k-per-chirp", type=int, default=None)
    p.add_argument("--tx-ffd-glob", default=None, help="Glob pattern for Tx .ffd files")
    p.add_argument("--rx-ffd-glob", default=None, help="Glob pattern for Rx .ffd files")
    p.add_argument(
        "--ffd-field-format",
        choices=["auto", "real_imag", "mag_phase_deg"],
        default="auto",
        help="Field interpretation for .ffd columns",
    )
    p.add_argument(
        "--use-jones-polarization",
        action="store_true",
        help="Use Jones-matrix polarization flow in synthesis (requires antenna model supporting Jones vectors)",
    )
    p.add_argument(
        "--global-jones-json",
        default=None,
        help="Optional JSON file containing global_jones_matrix for polarization calibration",
    )
    p.add_argument(
        "--run-hybrid-estimation",
        action="store_true",
        help="Run Hybrid-compatible post-processing bundle (doppler/angle summaries)",
    )
    p.add_argument("--estimation-nfft", type=int, default=144)
    p.add_argument("--estimation-range-bin-length", type=int, default=10)
    p.add_argument("--estimation-doppler-window", default="hann")
    p.add_argument(
        "--enable-motion-compensation",
        action="store_true",
        help="Enable TDM motion compensation for angle estimation in hybrid bundle",
    )
    p.add_argument(
        "--motion-comp-fd-hz",
        type=float,
        default=None,
        help="Optional Doppler override for motion compensation (Hz). If omitted, estimated from RD peak.",
    )
    p.add_argument(
        "--motion-comp-chirp-interval-s",
        type=float,
        default=None,
        help="Optional chirp interval for motion compensation. Default: samples_per_chirp/fs_hz",
    )
    p.add_argument(
        "--motion-comp-reference-tx",
        type=int,
        default=None,
        help="Reference Tx index for compensation phase (default: first tx in schedule)",
    )
    p.add_argument("--output-dir", required=True, help="Output directory for path_list.json and adc_cube.npz")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.frame_end < args.frame_start:
        raise ValueError("frame-end must be >= frame-start")

    tx_ffd_files = _resolve_optional_glob_list(args.tx_ffd_glob)
    rx_ffd_files = _resolve_optional_glob_list(args.rx_ffd_glob)
    global_jones_matrix = (
        load_global_jones_matrix_json(args.global_jones_json)
        if args.global_jones_json is not None
        else None
    )
    use_jones = bool(args.use_jones_polarization or (global_jones_matrix is not None))

    frames = list(range(args.frame_start, args.frame_end + 1))
    result = run_hybrid_frames_pipeline(
        frames_root_dir=args.frames_root,
        radar_json_path=args.radar_json,
        frame_indices=frames,
        fc_hz=args.fc_hz,
        slope_hz_per_s=args.slope_hz_per_s,
        fs_hz=args.fs_hz,
        samples_per_chirp=args.samples_per_chirp,
        camera_fov_deg=args.camera_fov_deg,
        mode=args.mode,
        file_ext=args.file_ext,
        amplitude_threshold=args.amplitude_threshold,
        distance_limits_m=(args.distance_min_m, args.distance_max_m),
        top_k_per_chirp=args.top_k_per_chirp,
        tx_ffd_files=tx_ffd_files,
        rx_ffd_files=rx_ffd_files,
        ffd_field_format=args.ffd_field_format,
        use_jones_polarization=use_jones,
        global_jones_matrix=global_jones_matrix,
        run_hybrid_estimation=args.run_hybrid_estimation,
        estimation_nfft=args.estimation_nfft,
        estimation_range_bin_length=args.estimation_range_bin_length,
        estimation_doppler_window=args.estimation_doppler_window,
        enable_motion_compensation=args.enable_motion_compensation,
        motion_comp_fd_hz=args.motion_comp_fd_hz,
        motion_comp_chirp_interval_s=args.motion_comp_chirp_interval_s,
        motion_comp_reference_tx=args.motion_comp_reference_tx,
        output_dir=args.output_dir,
    )

    n_paths = [len(x) for x in result["paths_by_chirp"]]
    print("Pipeline completed.")
    print(f"  frames: {len(frames)}")
    print(f"  tx_schedule length: {len(result['tx_schedule'])}")
    print(f"  paths/chirp (min,max): ({min(n_paths) if n_paths else 0}, {max(n_paths) if n_paths else 0})")
    print(f"  adc shape: {result['adc'].shape}")
    print(f"  ffd enabled: {result['ffd_enabled']}")
    print(f"  jones polarization enabled: {result['jones_polarization_enabled']}")
    print(f"  global jones enabled: {result['global_jones_enabled']}")
    print(f"  path_list: {result.get('path_list_json')}")
    print(f"  adc_cube: {result.get('adc_cube_npz')}")
    if args.run_hybrid_estimation:
        print(f"  hybrid_estimation: {result.get('hybrid_estimation_npz')}")
        print(f"  motion compensation enabled: {result['motion_compensation_enabled']}")
        print(f"  motion compensation fd_hz: {result['motion_comp_fd_hz']}")
        print(f"  motion compensation chirp_interval_s: {result['motion_comp_chirp_interval_s']}")


if __name__ == "__main__":
    main()

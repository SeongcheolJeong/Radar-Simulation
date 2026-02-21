#!/Library/Developer/CommandLineTools/usr/bin/python3
import argparse

from avxsim.pipeline import run_hybrid_frames_pipeline


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
    p.add_argument(
        "--run-hybrid-estimation",
        action="store_true",
        help="Run Hybrid-compatible post-processing bundle (doppler/angle summaries)",
    )
    p.add_argument("--estimation-nfft", type=int, default=144)
    p.add_argument("--estimation-range-bin-length", type=int, default=10)
    p.add_argument("--estimation-doppler-window", default="hann")
    p.add_argument("--output-dir", required=True, help="Output directory for path_list.json and adc_cube.npz")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.frame_end < args.frame_start:
        raise ValueError("frame-end must be >= frame-start")

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
        run_hybrid_estimation=args.run_hybrid_estimation,
        estimation_nfft=args.estimation_nfft,
        estimation_range_bin_length=args.estimation_range_bin_length,
        estimation_doppler_window=args.estimation_doppler_window,
        output_dir=args.output_dir,
    )

    n_paths = [len(x) for x in result["paths_by_chirp"]]
    print("Pipeline completed.")
    print(f"  frames: {len(frames)}")
    print(f"  tx_schedule length: {len(result['tx_schedule'])}")
    print(f"  paths/chirp (min,max): ({min(n_paths) if n_paths else 0}, {max(n_paths) if n_paths else 0})")
    print(f"  adc shape: {result['adc'].shape}")
    print(f"  path_list: {result.get('path_list_json')}")
    print(f"  adc_cube: {result.get('adc_cube_npz')}")
    if args.run_hybrid_estimation:
        print(f"  hybrid_estimation: {result.get('hybrid_estimation_npz')}")


if __name__ == "__main__":
    main()

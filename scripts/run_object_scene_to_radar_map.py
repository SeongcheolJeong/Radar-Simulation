#!/Library/Developer/CommandLineTools/usr/bin/python3
import argparse

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Object scene JSON -> path list + ADC cube + radar map")
    p.add_argument("--scene-json", required=True, help="Object scene JSON path")
    p.add_argument("--output-dir", required=True, help="Output directory")
    p.add_argument(
        "--run-hybrid-estimation",
        action="store_true",
        help="Also write hybrid_estimation.npz from the Hybrid compatibility bundle",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out = run_object_scene_to_radar_map_json(
        scene_json_path=args.scene_json,
        output_dir=args.output_dir,
        run_hybrid_estimation=bool(args.run_hybrid_estimation),
    )
    print("Object scene pipeline completed.")
    print(f"  frame_count: {out['frame_count']}")
    print(f"  path_list_json: {out['path_list_json']}")
    print(f"  adc_cube_npz: {out['adc_cube_npz']}")
    print(f"  radar_map_npz: {out['radar_map_npz']}")
    print(f"  hybrid_estimation_npz: {out.get('hybrid_estimation_npz')}")


if __name__ == "__main__":
    main()

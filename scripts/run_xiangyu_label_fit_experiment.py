#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from avxsim.xiangyu_path_power import (
    build_path_power_samples_from_xiangyu_sequence,
    save_path_power_rows_csv,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run Xiangyu label+ADC path-power fit experiments: "
            "build CSVs per frame-count and execute fit batch (reflection/scattering)."
        )
    )
    p.add_argument(
        "--case",
        action="append",
        required=True,
        help=(
            "Repeatable case definition: case_id=adc_root::labels_root "
            "(example: bms=/path/radar_raw_frame::/path/text_labels)"
        ),
    )
    p.add_argument("--frame-counts", default="128", help="Comma-separated frame counts (e.g., 128,512)")
    p.add_argument("--models", default="reflection,scattering")
    p.add_argument("--output-root", required=True)
    p.add_argument("--output-summary-json", default=None)

    p.add_argument("--adc-type", choices=["mat", "npz"], default="mat")
    p.add_argument("--adc-glob", default=None)
    p.add_argument("--labels-glob", default="*.csv")
    p.add_argument("--adc-key", default="adc")
    p.add_argument("--adc-order", default="scrt")
    p.add_argument("--mat-variable", default=None)
    p.add_argument("--stride", type=int, default=1)

    p.add_argument("--min-py-m", type=float, default=0.0)
    p.add_argument("--distance-min-m", type=float, default=0.0)
    p.add_argument("--distance-max-m", type=float, default=100.0)
    p.add_argument("--range-max-m", type=float, default=30.0)

    p.add_argument("--nfft-range", type=int, default=128)
    p.add_argument("--nfft-doppler", type=int, default=256)
    p.add_argument("--nfft-angle", type=int, default=64)
    p.add_argument("--range-window", default="hann")
    p.add_argument("--doppler-window", default="hann")
    p.add_argument("--angle-window", default="hann")
    p.add_argument("--range-bin-limit", type=int, default=128)
    p.add_argument("--bin-search-radius", type=int, default=1)

    p.add_argument("--fit-top-k", type=int, default=10)
    return p.parse_args()


def _parse_case(text: str) -> Tuple[str, str, str]:
    s = str(text)
    if "=" not in s or "::" not in s:
        raise ValueError("--case must be case_id=adc_root::labels_root")
    name, rest = s.split("=", 1)
    adc_root, labels_root = rest.split("::", 1)
    name = name.strip()
    adc_root = adc_root.strip()
    labels_root = labels_root.strip()
    if name == "" or adc_root == "" or labels_root == "":
        raise ValueError("--case contains empty segment")
    return name, adc_root, labels_root


def _parse_int_list(text: str) -> List[int]:
    vals = [x.strip() for x in str(text).split(",") if x.strip() != ""]
    out = [int(x) for x in vals]
    if len(out) == 0:
        raise ValueError("list argument must contain at least one value")
    for v in out:
        if v <= 0:
            raise ValueError("frame counts must be positive")
    return out


def _parse_models(text: str) -> List[str]:
    vals = [x.strip().lower() for x in str(text).split(",") if x.strip() != ""]
    allowed = {"reflection", "scattering"}
    if len(vals) == 0:
        raise ValueError("models must contain at least one value")
    for v in vals:
        if v not in allowed:
            raise ValueError(f"unsupported model: {v}")
    return vals


def _run(cmd: Sequence[str], cwd: Path, env: Dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, check=False)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    cases = [_parse_case(x) for x in args.case]
    frame_counts = _parse_int_list(args.frame_counts)
    models = _parse_models(args.models)

    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    experiments = []
    for frame_count in frame_counts:
        csv_dir = out_root / f"csv_{frame_count}"
        csv_dir.mkdir(parents=True, exist_ok=True)

        csv_rows = []
        for case_name, adc_root, labels_root in cases:
            scenario_id = f"xiangyu_{case_name}_{frame_count}"
            payload = build_path_power_samples_from_xiangyu_sequence(
                adc_root_dir=adc_root,
                labels_root_dir=labels_root,
                scenario_id=scenario_id,
                adc_type=args.adc_type,
                adc_glob=args.adc_glob,
                labels_glob=args.labels_glob,
                adc_key=args.adc_key,
                adc_order=args.adc_order,
                mat_variable=args.mat_variable,
                max_frames=frame_count,
                stride=args.stride,
                min_py_m=args.min_py_m,
                distance_limits_m=(args.distance_min_m, args.distance_max_m),
                range_max_m=args.range_max_m,
                nfft_range=args.nfft_range,
                nfft_doppler=args.nfft_doppler,
                nfft_angle=args.nfft_angle,
                range_window=args.range_window,
                doppler_window=args.doppler_window,
                angle_window=args.angle_window,
                range_bin_limit=args.range_bin_limit,
                bin_search_radius=args.bin_search_radius,
            )
            out_csv = csv_dir / f"{case_name}_path_power_samples_{frame_count}.csv"
            out_meta = csv_dir / f"{case_name}_path_power_samples_{frame_count}.meta.json"
            save_path_power_rows_csv(str(out_csv), payload["rows"])
            out_meta.write_text(json.dumps(payload["metadata"], indent=2), encoding="utf-8")

            csv_rows.append(
                {
                    "case_name": case_name,
                    "scenario_id": scenario_id,
                    "csv_path": str(out_csv),
                    "meta_json": str(out_meta),
                    "selected_row_count": int(payload["metadata"]["selected_row_count"]),
                    "processed_frame_count": int(payload["metadata"]["processed_frame_count"]),
                    "raw_label_count": int(payload["metadata"]["raw_label_count"]),
                }
            )

        fit_dir = out_root / f"fit_{frame_count}"
        fit_dir.mkdir(parents=True, exist_ok=True)
        fit_summary = fit_dir / f"path_power_fit_batch_summary_{frame_count}.json"

        fit_cmd = [
            "python3",
            "scripts/run_path_power_fit_batch.py",
        ]
        for row in csv_rows:
            fit_cmd += ["--csv-case", f"{row['case_name']}={row['csv_path']}"]
        for m in models:
            fit_cmd += ["--model", m]
        fit_cmd += [
            "--batch-id",
            f"xiangyu_label_fit_{frame_count}",
            "--top-k",
            str(args.fit_top_k),
            "--output-root",
            str(fit_dir),
            "--output-summary-json",
            str(fit_summary),
        ]

        proc = _run(fit_cmd, cwd=repo_root, env=env)
        if proc.returncode != 0:
            raise RuntimeError(
                "fit batch failed:\n" + proc.stdout + "\n" + proc.stderr
            )

        fit_payload = json.loads(fit_summary.read_text(encoding="utf-8"))
        experiments.append(
            {
                "frame_count": int(frame_count),
                "csv_rows": csv_rows,
                "fit_summary_json": str(fit_summary),
                "fit_summary": fit_payload,
            }
        )

    summary = {
        "version": 1,
        "cases": [
            {
                "case_name": case_name,
                "adc_root": adc_root,
                "labels_root": labels_root,
            }
            for case_name, adc_root, labels_root in cases
        ],
        "frame_counts": frame_counts,
        "models": models,
        "output_root": str(out_root),
        "experiments": experiments,
    }

    out_summary = (
        out_root / "xiangyu_label_fit_experiment_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Xiangyu label fit experiment completed.")
    print(f"  cases: {len(cases)}")
    print(f"  frame_counts: {frame_counts}")
    print(f"  models: {models}")
    print(f"  output_summary_json: {out_summary}")


if __name__ == "__main__":
    main()

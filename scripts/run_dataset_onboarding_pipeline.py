#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run end-to-end dataset onboarding pipeline (extract -> pack -> plan -> replay)"
    )
    p.add_argument("--input-type", choices=["adc_npz", "mat"], required=True)
    p.add_argument("--input-root", required=True)
    p.add_argument("--scenario-id", required=True)
    p.add_argument("--work-root", required=True)

    p.add_argument("--adc-npz-glob", default="*.npz")
    p.add_argument("--mat-glob", default="*.mat")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--max-files", type=int, default=None)
    p.add_argument("--stride", type=int, default=1)

    p.add_argument("--adc-key", default="adc")
    p.add_argument("--adc-order", default="sctr")
    p.add_argument("--reference-index", type=int, default=0)
    p.add_argument("--nfft-range", type=int, default=None)
    p.add_argument("--nfft-doppler", type=int, default=None)
    p.add_argument("--nfft-angle", type=int, default=None)
    p.add_argument("--range-bin-limit", type=int, default=None)

    p.add_argument("--allow-unlocked", action="store_true")
    return p.parse_args()


def _run(cmd, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    work_root = Path(args.work_root)
    work_root.mkdir(parents=True, exist_ok=True)

    adc_root = Path(args.input_root)
    if args.input_type == "mat":
        adc_root = work_root / "adc_npz"
        extract_cmd = [
            "python3",
            "scripts/extract_mat_adc_to_npz.py",
            "--input-root",
            str(args.input_root),
            "--output-root",
            str(adc_root),
            "--mat-glob",
            str(args.mat_glob),
            "--stride",
            str(args.stride),
        ]
        if args.recursive:
            extract_cmd.append("--recursive")
        if args.max_files is not None:
            extract_cmd += ["--max-files", str(args.max_files)]

        proc = _run(extract_cmd, cwd=repo_root)
        if proc.returncode != 0:
            raise RuntimeError(
                "MAT extraction failed:\n"
                + proc.stdout
                + "\n"
                + proc.stderr
            )

    pack_root = work_root / "packs" / f"pack_{args.scenario_id}"
    pack_cmd = [
        "python3",
        "scripts/build_pack_from_adc_npz_dir.py",
        "--input-root",
        str(adc_root),
        "--input-glob",
        str(args.adc_npz_glob),
        "--output-pack-root",
        str(pack_root),
        "--scenario-id",
        str(args.scenario_id),
        "--adc-key",
        str(args.adc_key),
        "--adc-order",
        str(args.adc_order),
        "--reference-index",
        str(args.reference_index),
        "--stride",
        str(args.stride),
    ]
    if args.recursive:
        pack_cmd.append("--recursive")
    if args.max_files is not None:
        pack_cmd += ["--max-files", str(args.max_files)]
    if args.nfft_range is not None:
        pack_cmd += ["--nfft-range", str(args.nfft_range)]
    if args.nfft_doppler is not None:
        pack_cmd += ["--nfft-doppler", str(args.nfft_doppler)]
    if args.nfft_angle is not None:
        pack_cmd += ["--nfft-angle", str(args.nfft_angle)]
    if args.range_bin_limit is not None:
        pack_cmd += ["--range-bin-limit", str(args.range_bin_limit)]

    proc2 = _run(pack_cmd, cwd=repo_root)
    if proc2.returncode != 0:
        raise RuntimeError(
            "Pack build failed:\n" + proc2.stdout + "\n" + proc2.stderr
        )

    plan_json = work_root / "measured_replay_plan.json"
    plan_cmd = [
        "python3",
        "scripts/build_measured_replay_plan.py",
        "--packs-root",
        str(work_root / "packs"),
        "--output-plan-json",
        str(plan_json),
    ]
    proc3 = _run(plan_cmd, cwd=repo_root)
    if proc3.returncode != 0:
        raise RuntimeError(
            "Plan build failed:\n" + proc3.stdout + "\n" + proc3.stderr
        )

    replay_out_root = work_root / "measured_replay_outputs"
    summary_json = work_root / "measured_replay_summary.json"
    run_cmd = [
        "python3",
        "scripts/run_measured_replay_execution.py",
        "--plan-json",
        str(plan_json),
        "--output-root",
        str(replay_out_root),
        "--output-summary-json",
        str(summary_json),
    ]
    if args.allow_unlocked:
        run_cmd.append("--allow-unlocked")

    proc4 = _run(run_cmd, cwd=repo_root)
    if proc4.returncode not in (0, 2):
        raise RuntimeError(
            "Replay run failed:\n" + proc4.stdout + "\n" + proc4.stderr
        )

    payload = {
        "version": 1,
        "input_type": str(args.input_type),
        "input_root": str(args.input_root),
        "scenario_id": str(args.scenario_id),
        "work_root": str(work_root),
        "pack_root": str(pack_root),
        "plan_json": str(plan_json),
        "replay_output_root": str(replay_out_root),
        "summary_json": str(summary_json),
        "replay_exit_code": int(proc4.returncode),
    }
    onboarding_summary = work_root / "onboarding_summary.json"
    onboarding_summary.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Dataset onboarding pipeline completed.")
    print(f"  input_type: {args.input_type}")
    print(f"  scenario_id: {args.scenario_id}")
    print(f"  pack_root: {pack_root}")
    print(f"  plan_json: {plan_json}")
    print(f"  summary_json: {summary_json}")
    print(f"  replay_exit_code: {proc4.returncode}")
    print(f"  onboarding_summary_json: {onboarding_summary}")


if __name__ == "__main__":
    main()

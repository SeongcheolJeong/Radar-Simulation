#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _make_adc(shape, shift_s=0, shift_c=0, seed=0):
    rng = np.random.default_rng(seed)
    s, c, t, r = shape
    ys = np.arange(s, dtype=np.float64)[:, None, None, None]
    yc = np.arange(c, dtype=np.float64)[None, :, None, None]
    tone_s = np.exp(1j * 2.0 * np.pi * ((ys + shift_s) / max(s, 1)))
    tone_c = np.exp(1j * 2.0 * np.pi * ((yc + shift_c) / max(c, 1)))
    base = tone_s * tone_c
    noise = 0.03 * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    return (base + noise).astype(np.complex64)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_fit_aware_pack_") as td:
        root = Path(td)
        adc_root = root / "adc_npz"
        adc_root.mkdir(parents=True, exist_ok=True)

        np.savez_compressed(adc_root / "frame_000.npz", adc=_make_adc((96, 48, 2, 4), shift_s=2, shift_c=1, seed=1))
        np.savez_compressed(adc_root / "frame_001.npz", adc=_make_adc((96, 48, 2, 4), shift_s=3, shift_c=2, seed=2))
        np.savez_compressed(adc_root / "frame_002.npz", adc=_make_adc((96, 48, 2, 4), shift_s=4, shift_c=3, seed=3))

        src_pack = root / "src_pack"
        cmd_build_src = [
            "python3",
            "scripts/build_pack_from_adc_npz_dir.py",
            "--input-root",
            str(adc_root),
            "--input-glob",
            "*.npz",
            "--output-pack-root",
            str(src_pack),
            "--scenario-id",
            "fitaware_src_v1",
            "--adc-order",
            "sctr",
            "--nfft-doppler",
            "64",
            "--nfft-angle",
            "16",
            "--range-bin-limit",
            "64",
        ]
        proc_src = subprocess.run(cmd_build_src, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc_src.returncode != 0:
            raise RuntimeError(f"source pack build failed:\nSTDOUT:\n{proc_src.stdout}\nSTDERR:\n{proc_src.stderr}")

        fit_json = root / "path_power_fit_reflection.json"
        fit_json.write_text(
            json.dumps(
                {
                    "version": 1,
                    "fit": {
                        "model": "reflection",
                        "best_params": {
                            "range_power_exponent": 5.0,
                            "gain_scale": 1.0,
                        },
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        out_pack = root / "fit_aware_pack"
        out_summary = root / "fit_aware_pack_summary.json"
        cmd_fit_aware = [
            "python3",
            "scripts/build_fit_aware_pack_from_existing_pack.py",
            "--source-pack-root",
            str(src_pack),
            "--output-pack-root",
            str(out_pack),
            "--path-power-fit-json",
            str(fit_json),
            "--output-summary-json",
            str(out_summary),
        ]
        proc_fit = subprocess.run(cmd_fit_aware, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc_fit.returncode != 0:
            raise RuntimeError(f"fit-aware pack build failed:\nSTDOUT:\n{proc_fit.stdout}\nSTDERR:\n{proc_fit.stderr}")

        src_manifest = json.loads((src_pack / "replay_manifest.json").read_text(encoding="utf-8"))
        out_manifest = json.loads((out_pack / "replay_manifest.json").read_text(encoding="utf-8"))
        src_cands = src_manifest["cases"][0]["candidates"]
        out_cands = out_manifest["cases"][0]["candidates"]
        if len(src_cands) != len(out_cands):
            raise AssertionError("candidate count changed unexpectedly")

        src_npz = Path(src_cands[0]["estimation_npz"])
        out_npz = Path(out_cands[0]["estimation_npz"])
        with np.load(str(src_npz), allow_pickle=False) as s0, np.load(str(out_npz), allow_pickle=False) as s1:
            rd0 = np.asarray(s0["fx_dop_win"], dtype=np.float64)
            rd1 = np.asarray(s1["fx_dop_win"], dtype=np.float64)
            if np.allclose(rd0, rd1):
                raise AssertionError("fit-aware proxy did not change RD map")

            meta1 = json.loads(str(s1["metadata_json"].tolist()))
            if "path_power_fit_proxy" not in meta1:
                raise AssertionError("missing path_power_fit_proxy metadata in output candidate")

        src_profile = json.loads((src_pack / "scenario_profile.json").read_text(encoding="utf-8"))
        out_profile = json.loads((out_pack / "scenario_profile.json").read_text(encoding="utf-8"))
        if src_profile.get("parity_thresholds") != out_profile.get("parity_thresholds"):
            raise AssertionError("parity thresholds were not preserved")
        if "fit_aware_rebuild" not in out_profile:
            raise AssertionError("fit_aware_rebuild metadata missing")

    print("validate_build_fit_aware_pack_from_existing_pack: pass")


if __name__ == "__main__":
    main()

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


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        in_root = tmp_path / "adc_npz"
        in_root.mkdir(parents=True, exist_ok=True)
        adc1 = _make_adc((96, 48, 2, 4), shift_s=2, shift_c=1, seed=1)
        adc2 = _make_adc((96, 48, 2, 4), shift_s=3, shift_c=2, seed=2)
        np.savez_compressed(in_root / "frame_000.npz", adc=adc1)
        np.savez_compressed(in_root / "frame_001.npz", adc=adc2)

        pack_root = tmp_path / "pack_out"
        proc = subprocess.run(
            [
                "python3",
                "scripts/build_pack_from_adc_npz_dir.py",
                "--input-root",
                str(in_root),
                "--input-glob",
                "*.npz",
                "--output-pack-root",
                str(pack_root),
                "--scenario-id",
                "rawadc_mock_v1",
                "--adc-order",
                "sctr",
                "--nfft-doppler",
                "64",
                "--nfft-angle",
                "16",
                "--range-bin-limit",
                "64",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "ADC pack build completed." in proc.stdout, proc.stdout

        manifest_json = pack_root / "replay_manifest.json"
        profile_json = pack_root / "scenario_profile.json"
        lock_policy_json = pack_root / "lock_policy.json"
        assert manifest_json.exists()
        assert profile_json.exists()
        assert lock_policy_json.exists()

        manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
        assert len(manifest["cases"]) == 1
        case = manifest["cases"][0]
        assert case["scenario_id"] == "rawadc_mock_v1"
        assert len(case["candidates"]) == 2

        cand0 = Path(case["candidates"][0]["estimation_npz"])
        with np.load(str(cand0), allow_pickle=False) as payload:
            assert "fx_dop_win" in payload
            assert "fx_ang" in payload
            rd = np.asarray(payload["fx_dop_win"])
            ra = np.asarray(payload["fx_ang"])
            assert rd.ndim == 2
            assert ra.ndim == 2
            assert rd.shape[0] == 64
            assert ra.shape[0] == 16
            assert np.all(np.isfinite(rd))
            assert np.all(np.isfinite(ra))

    print("ADC pack builder validation passed.")


if __name__ == "__main__":
    run()

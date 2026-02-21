#!/usr/bin/env python3
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from avxsim.parity import compare_hybrid_estimation_npz
from avxsim.scenario_profile import build_scenario_profile_payload, save_scenario_profile_json


def _write_estimation_npz(path: Path, scale: float, seed: int) -> None:
    rng = np.random.default_rng(seed)
    rd = np.abs(rng.normal(size=(32, 48))).astype(np.float64)
    ra = np.abs(rng.normal(size=(16, 32))).astype(np.float64)
    np.savez_compressed(
        str(path),
        fx_dop_win=rd * float(scale),
        fx_ang=ra * float(scale),
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "build_scenario_profile_from_pack.py"

    with tempfile.TemporaryDirectory(prefix="validate_profile_from_pack_") as td:
        pack = Path(td) / "pack_demo"
        cand_dir = pack / "candidates"
        cand_dir.mkdir(parents=True, exist_ok=True)

        c1 = cand_dir / "c1.npz"
        c2 = cand_dir / "c2.npz"
        c3 = cand_dir / "c3.npz"
        _write_estimation_npz(c1, scale=1.0, seed=0)
        _write_estimation_npz(c2, scale=1.02, seed=1)
        _write_estimation_npz(c3, scale=0.97, seed=2)

        profile = build_scenario_profile_payload(
            scenario_id="demo_profile_from_pack",
            global_jones_matrix=np.eye(2, dtype=np.complex128),
            parity_thresholds={"rd_peak_val_abs_error_max": 1e-9},
            reference_estimation_npz=str(c1),
            motion_compensation_defaults={
                "enabled": False,
                "fd_hz": None,
                "chirp_interval_s": None,
                "reference_tx": None,
            },
        )
        save_scenario_profile_json(str(pack / "scenario_profile.json"), profile)

        manifest = {
            "version": 1,
            "cases": [
                {
                    "scenario_id": "demo_profile_from_pack",
                    "profile_json": str(pack / "scenario_profile.json"),
                    "candidates": [
                        {"name": "c1", "estimation_npz": str(c1)},
                        {"name": "c2", "estimation_npz": str(c2)},
                        {"name": "c3", "estimation_npz": str(c3)},
                    ],
                }
            ],
        }
        (pack / "replay_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        policy_json = pack / "profile_tuning_policy.json"
        emitted_policy_json = pack / "profile_tuning_policy.emitted.json"
        policy_json.write_text(
            json.dumps(
                {
                    "version": 1,
                    "name": "demo_profile_tuning_policy_v1",
                    "profile_rebuild": {
                        "case_index": 0,
                        "reference_candidate_index": 0,
                        "candidate_stride": 2,
                        "max_candidates": 2,
                        "threshold_quantile": 1.0,
                        "threshold_margin": 1.04,
                        "threshold_floor": "none",
                    },
                    "lock_policy": {
                        "min_pass_rate": 1.0,
                        "max_case_fail_count": 0,
                        "require_motion_defaults_enabled": False,
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        cmd = [
            "python3",
            str(script),
            "--pack-root",
            str(pack),
            "--policy-json",
            str(policy_json),
            "--emit-policy-json",
            str(emitted_policy_json),
            "--backup-original",
            "--threshold-margin",
            "1.05",
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"profile-from-pack script failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        rebuilt = json.loads((pack / "scenario_profile.json").read_text(encoding="utf-8"))
        assert rebuilt["threshold_derivation"]["method"] == "from_pack_candidates"
        assert int(rebuilt["threshold_derivation"]["train_count"]) == 2
        assert float(rebuilt["threshold_derivation"]["threshold_margin"]) == 1.05
        assert "scenario_id" in rebuilt
        assert "parity_thresholds" in rebuilt
        assert "profile_tuning_policy" in rebuilt
        assert rebuilt["profile_tuning_policy"]["name"] == "demo_profile_tuning_policy_v1"
        assert int(rebuilt["profile_tuning_policy"]["profile_rebuild"]["candidate_stride"]) == 2
        assert int(rebuilt["profile_tuning_policy"]["profile_rebuild"]["max_candidates"]) == 2

        th = rebuilt["parity_thresholds"]
        ref = str(rebuilt["reference_estimation_npz"])
        selected = [str(x) for x in rebuilt["train_estimation_npz"]]
        assert selected == [str(c1), str(c3)]
        for p in selected:
            rep = compare_hybrid_estimation_npz(reference_npz=ref, candidate_npz=p, thresholds=th)
            if not bool(rep["pass"]):
                raise AssertionError(f"expected candidate to pass with rebuilt thresholds: {p}")
        emitted = json.loads(emitted_policy_json.read_text(encoding="utf-8"))
        assert emitted["name"] == "demo_profile_tuning_policy_v1"
        assert float(emitted["profile_rebuild"]["threshold_margin"]) == 1.05

        print("validate_build_scenario_profile_from_pack: pass")


if __name__ == "__main__":
    main()

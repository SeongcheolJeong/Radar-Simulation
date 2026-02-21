#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _write_est(path: Path) -> None:
    rd = np.ones((8, 8), dtype=np.float64)
    ra = np.ones((8, 8), dtype=np.float64)
    np.savez_compressed(path, fx_dop_win=rd, fx_ang=ra)


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        pack_root = tmp_path / "pack_a"
        cand_dir = pack_root / "candidates"
        cand_dir.mkdir(parents=True, exist_ok=True)

        profile_json = pack_root / "scenario_profile.json"
        profile_json.write_text(
            json.dumps(
                {
                    "version": 1,
                    "scenario_id": "scenario_a",
                    "created_utc": "2026-02-21T00:00:00+00:00",
                    "global_jones_matrix": [
                        {"re": 1.0, "im": 0.0},
                        {"re": 0.0, "im": 0.0},
                        {"re": 0.0, "im": 0.0},
                        {"re": 1.0, "im": 0.0},
                    ],
                    "parity_thresholds": {},
                    "reference_estimation_npz": "/tmp/ref.npz",
                }
            ),
            encoding="utf-8",
        )

        c1 = cand_dir / "cand_good.npz"
        c2 = cand_dir / "cand_bad.npz"
        _write_est(c1)
        _write_est(c2)

        (cand_dir / "cand_good.meta.json").write_text(
            json.dumps({"speed_mps": 1.2, "tag": "good"}),
            encoding="utf-8",
        )

        out_manifest = pack_root / "replay_manifest.json"
        proc = subprocess.run(
            [
                "python3",
                "scripts/build_replay_manifest_from_pack.py",
                "--pack-root",
                str(pack_root),
                "--include-sidecar-metadata",
                "--output-manifest-json",
                str(out_manifest),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Replay manifest build completed." in proc.stdout, proc.stdout

        payload = json.loads(out_manifest.read_text(encoding="utf-8"))
        assert payload["version"] == 1
        assert len(payload["cases"]) == 1
        case = payload["cases"][0]
        assert case["scenario_id"] == "pack_a"
        assert case["profile_json"].endswith("scenario_profile.json")
        assert len(case["candidates"]) == 2

        by_name = {x["name"]: x for x in case["candidates"]}
        assert set(by_name.keys()) == {"cand_good", "cand_bad"}
        assert by_name["cand_good"]["metadata"]["tag"] == "good"
        assert "metadata" not in by_name["cand_bad"]

        proc_empty = subprocess.run(
            [
                "python3",
                "scripts/build_replay_manifest_from_pack.py",
                "--pack-root",
                str(pack_root),
                "--candidate-glob",
                "none/*.npz",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_empty.returncode != 0

        proc_empty_ok = subprocess.run(
            [
                "python3",
                "scripts/build_replay_manifest_from_pack.py",
                "--pack-root",
                str(pack_root),
                "--candidate-glob",
                "none/*.npz",
                "--allow-empty-candidates",
                "--output-manifest-json",
                str(out_manifest),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "candidates: 0" in proc_empty_ok.stdout, proc_empty_ok.stdout

    print("Replay manifest builder validation passed.")


if __name__ == "__main__":
    run()

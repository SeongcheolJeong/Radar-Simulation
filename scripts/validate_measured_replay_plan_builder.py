#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        packs_root = tmp_path / "packs"
        (packs_root / "pack_a").mkdir(parents=True, exist_ok=True)
        (packs_root / "pack_b").mkdir(parents=True, exist_ok=True)

        (packs_root / "pack_a" / "replay_manifest.json").write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "scenario_id": "a_case",
                            "profile_json": "/tmp/a_profile.json",
                            "candidates": [{"name": "a", "estimation_npz": "/tmp/a.npz"}],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        (packs_root / "pack_b" / "replay_manifest.json").write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "scenario_id": "b_case",
                            "profile_json": "/tmp/b_profile.json",
                            "candidates": [{"name": "b", "estimation_npz": "/tmp/b.npz"}],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        (packs_root / "pack_b" / "lock_policy.json").write_text(
            json.dumps(
                {
                    "min_pass_rate": 0.95,
                    "max_case_fail_count": 1,
                    "require_motion_defaults_enabled": True,
                }
            ),
            encoding="utf-8",
        )

        out_plan = tmp_path / "measured_replay_plan.json"
        proc = subprocess.run(
            [
                "python3",
                "scripts/build_measured_replay_plan.py",
                "--packs-root",
                str(packs_root),
                "--output-plan-json",
                str(out_plan),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Measured replay plan build completed." in proc.stdout, proc.stdout

        payload = json.loads(out_plan.read_text(encoding="utf-8"))
        assert payload["version"] == 1
        assert len(payload["packs"]) == 2

        by_id = {p["pack_id"]: p for p in payload["packs"]}
        assert set(by_id.keys()) == {"pack_a", "pack_b"}
        assert by_id["pack_a"]["output_subdir"] == "pack_a"
        assert "lock_policy" not in by_id["pack_a"]
        assert by_id["pack_b"]["lock_policy"]["require_motion_defaults_enabled"] is True

        empty_root = tmp_path / "empty_packs"
        empty_root.mkdir(parents=True, exist_ok=True)
        out_empty = tmp_path / "empty_plan.json"

        proc_fail = subprocess.run(
            [
                "python3",
                "scripts/build_measured_replay_plan.py",
                "--packs-root",
                str(empty_root),
                "--output-plan-json",
                str(out_empty),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_fail.returncode != 0

        proc_ok = subprocess.run(
            [
                "python3",
                "scripts/build_measured_replay_plan.py",
                "--packs-root",
                str(empty_root),
                "--output-plan-json",
                str(out_empty),
                "--allow-empty",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "discovered_packs: 0" in proc_ok.stdout, proc_ok.stdout

    print("Measured replay plan builder validation passed.")


if __name__ == "__main__":
    run()

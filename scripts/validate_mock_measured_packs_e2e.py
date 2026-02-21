#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _run(cmd, cwd, env, check=True):
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=check,
    )


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        # Case 1: All packs should lock
        root_ok = tmp_path / "mock_ok"
        p1 = _run(
            [
                "python3",
                "scripts/generate_mock_measured_packs.py",
                "--output-root",
                str(root_ok),
            ],
            cwd=repo_root,
            env=env,
            check=True,
        )
        assert "Mock measured packs generated." in p1.stdout, p1.stdout

        plan_ok = tmp_path / "plan_ok.json"
        p2 = _run(
            [
                "python3",
                "scripts/build_measured_replay_plan.py",
                "--packs-root",
                str(root_ok),
                "--output-plan-json",
                str(plan_ok),
            ],
            cwd=repo_root,
            env=env,
            check=True,
        )
        assert "discovered_packs: 2" in p2.stdout, p2.stdout

        summary_ok = tmp_path / "summary_ok.json"
        out_ok = tmp_path / "outputs_ok"
        p3 = _run(
            [
                "python3",
                "scripts/run_measured_replay_execution.py",
                "--plan-json",
                str(plan_ok),
                "--output-root",
                str(out_ok),
                "--output-summary-json",
                str(summary_ok),
            ],
            cwd=repo_root,
            env=env,
            check=True,
        )
        assert "overall_lock_pass: True" in p3.stdout, p3.stdout
        payload_ok = json.loads(summary_ok.read_text(encoding="utf-8"))
        assert payload_ok["overall_lock_pass"] is True
        assert payload_ok["summary"]["locked_count"] == 2
        assert payload_ok["summary"]["unlocked_count"] == 0

        # Case 2: Include failing candidate, strict should fail with code 2
        root_bad = tmp_path / "mock_bad"
        p4 = _run(
            [
                "python3",
                "scripts/generate_mock_measured_packs.py",
                "--output-root",
                str(root_bad),
                "--include-failing-pack",
            ],
            cwd=repo_root,
            env=env,
            check=True,
        )
        assert "include_failing_pack: True" in p4.stdout, p4.stdout

        plan_bad = tmp_path / "plan_bad.json"
        _run(
            [
                "python3",
                "scripts/build_measured_replay_plan.py",
                "--packs-root",
                str(root_bad),
                "--output-plan-json",
                str(plan_bad),
            ],
            cwd=repo_root,
            env=env,
            check=True,
        )

        summary_bad = tmp_path / "summary_bad.json"
        out_bad = tmp_path / "outputs_bad"
        p5 = subprocess.run(
            [
                "python3",
                "scripts/run_measured_replay_execution.py",
                "--plan-json",
                str(plan_bad),
                "--output-root",
                str(out_bad),
                "--output-summary-json",
                str(summary_bad),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert p5.returncode == 2, p5.stdout + "\n" + p5.stderr
        assert "overall_lock_pass: False" in p5.stdout, p5.stdout

        payload_bad = json.loads(summary_bad.read_text(encoding="utf-8"))
        assert payload_bad["overall_lock_pass"] is False
        assert payload_bad["summary"]["unlocked_count"] >= 1

    print("Mock measured packs e2e validation passed.")


if __name__ == "__main__":
    run()

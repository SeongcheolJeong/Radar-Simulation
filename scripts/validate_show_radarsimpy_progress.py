#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "show_radarsimpy_progress.py"
    with tempfile.TemporaryDirectory(prefix="validate_show_radarsimpy_progress_") as td:
        root = Path(td)
        reports_root = root / "reports"
        smoke_json = root / "radarsimpy_integration_smoke_gate_hook_latest.json"
        wrapper_json = root / "radarsimpy_wrapper_integration_gate_hook_latest.json"
        migration_json = reports_root / "radarsimpy_migration_stepwise_case" / "summary.json"
        e2e_rollup_json = reports_root / "integration_full_real_e2e_case" / "_status_rollup.json"
        out_json = root / "snapshot.json"

        _write_json(
            smoke_json,
            {
                "pass": True,
                "step_count": 6,
                "pass_count": 6,
                "fail_count": 0,
            },
        )
        _write_json(
            wrapper_json,
            {
                "pass": True,
                "check_count": 6,
                "pass_count": 6,
                "fail_count": 0,
                "with_real_runtime": False,
            },
        )
        _write_json(
            migration_json,
            {
                "migration_status": "ready",
                "summary": {
                    "candidate_backend_count": 3,
                    "pass_count": 3,
                    "fail_count": 0,
                    "blocked_count": 0,
                },
            },
        )
        _write_json(
            e2e_rollup_json,
            {
                "all_steps_passed": True,
                "failed_steps": [],
                "step_rcs": {
                    "radarsimpy_pilot": 0,
                    "radarsimpy_migration_stepwise": 0,
                    "radarsimpy_periodic_manifest": 0,
                    "radarsimpy_periodic_parity_lock": 0,
                },
            },
        )

        env = dict(os.environ)
        proc = subprocess.run(
            [
                str(Path(sys.executable)),
                str(script_path),
                "--reports-root",
                str(reports_root),
                "--smoke-summary-json",
                str(smoke_json),
                "--wrapper-summary-json",
                str(wrapper_json),
                "--migration-summary-json",
                str(migration_json),
                "--e2e-rollup-json",
                str(e2e_rollup_json),
                "--output-json",
                str(out_json),
                "--strict-ready",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy progress snapshot" in proc.stdout, proc.stdout
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["overall_ready"] is True
        assert int(payload["ready_count"]) == int(payload["stage_count"])
        assert int(payload["blocked_count"]) == 0

        names = [str(s.get("name")) for s in payload.get("stages", [])]
        expected = {
            "integration_smoke_gate",
            "wrapper_integration_gate",
            "migration_stepwise",
            "real_e2e",
        }
        assert expected.issubset(set(names)), names
        for row in payload.get("stages", []):
            assert bool(row.get("ready")) is True

    print("validate_show_radarsimpy_progress: pass")


if __name__ == "__main__":
    run()

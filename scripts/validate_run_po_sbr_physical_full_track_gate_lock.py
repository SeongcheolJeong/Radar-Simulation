#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _write_bundle_fixture(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "full_track_status": "ready",
                "summary": {
                    "required_profile_count": 7,
                    "missing_profile_count": 0,
                    "po_sbr_executed_profile_count": 7,
                    "gate_blocked_profile_count": 0,
                },
                "rows": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_runtime_fixture(module_path: Path) -> str:
    module_path.write_text(
        """
import json
from pathlib import Path


def _value(argv, flag, default=None):
    if flag not in argv:
        return default
    idx = argv.index(flag)
    if idx + 1 >= len(argv):
        return default
    return argv[idx + 1]


def _values(argv, flag):
    out = []
    i = 0
    while i < len(argv):
        if argv[i] == flag and i + 1 < len(argv):
            out.append(argv[i + 1])
            i += 2
            continue
        i += 1
    return out


def run_stability(argv):
    summary_path = Path(_value(argv, "--output-summary-json")).resolve()
    runs = int(_value(argv, "--runs", "3"))
    payload = {
        "version": 1,
        "campaign_status": "stable",
        "blockers": [],
        "requested_runs": runs,
        "rows": [],
        "summary": {
            "requested_runs": runs,
            "completed_runs": runs,
            "run_error_count": 0,
            "full_track_blocked_count": 0,
            "matrix_not_ready_count": 0,
            "gate_blocked_run_count": 0,
            "stable_run_count": runs,
        },
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0


def run_hardening(argv):
    summary_path = Path(_value(argv, "--output-summary-json")).resolve()
    full_track_summary_json = Path(_value(argv, "--full-track-bundle-summary-json")).resolve()
    stability_summary_json = Path(_value(argv, "--stability-summary-json")).resolve()
    candidate = str(_value(argv, "--realism-gate-candidate", "realism_tight_v2")).strip()
    threshold_profiles = [str(x).strip() for x in _values(argv, "--threshold-profile") if str(x).strip() != ""]
    if len(threshold_profiles) == 0:
        threshold_profiles = [candidate]
    if candidate not in threshold_profiles:
        threshold_profiles.append(candidate)

    profiles = []
    for profile in threshold_profiles:
        profiles.append(
            {
                "threshold_profile": profile,
                "thresholds_json": str((summary_path.parent / profile / "thresholds.json").resolve()),
                "thresholds": {},
                "status": "ready",
                "summary": {
                    "profile_count": 1,
                    "ready_profile_count": 1,
                    "blocked_profile_count": 0,
                    "failed_profile_count": 0,
                    "total_parity_fail_count": 0,
                },
                "rows": [
                    {
                        "profile": "fixture_realism_profile",
                        "profile_family": "realism_informational",
                        "source_golden_summary_json": str((summary_path.parent / "fixture_golden.json").resolve()),
                        "thresholds_json": str((summary_path.parent / profile / "thresholds.json").resolve()),
                        "output_kpi_json": str((summary_path.parent / profile / "kpi_hardened.json").resolve()),
                        "run_kpi": {"ok": True, "return_code": 0, "stdout": "shim", "stderr": "", "cmd": []},
                        "validate_kpi": {"ok": True, "return_code": 0, "stdout": "shim", "stderr": "", "cmd": []},
                        "run_ok": True,
                        "campaign_status": "ready",
                        "blockers": [],
                        "parity_fail_count": 0,
                        "parity_fail_pairs": [],
                    }
                ],
            }
        )

    payload = {
        "version": 1,
        "hardening_status": "hardened",
        "blockers": [],
        "source_full_track_bundle_summary_json": str(full_track_summary_json),
        "source_stability_summary_json": str(stability_summary_json),
        "source_full_track_status": "ready",
        "source_stability_status": "stable",
        "realism_gate_candidate": candidate,
        "realism_gate_candidate_status": "ready",
        "threshold_profiles": threshold_profiles,
        "realism_profile_names": ["fixture_realism_profile"],
        "profiles": profiles,
        "summary": {
            "threshold_profile_count": len(threshold_profiles),
            "threshold_ready_count": len(threshold_profiles),
            "threshold_failed_count": 0,
            "realism_profile_count": 1,
            "bundle_gate_blocked_profile_count": 0,
            "realism_gate_candidate_status": "ready",
        },
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return module_path.stem


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="validate_po_sbr_gate_lock_") as td:
        root = Path(td)
        bundle_summary = root / "full_track_bundle.json"
        out_root = root / "gate_lock"
        out_summary = root / "gate_lock_summary.json"

        _write_bundle_fixture(bundle_summary)
        fixture_module = _write_runtime_fixture(root / "gate_lock_fixture.py")

        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(root), str(repo_root / "src")])

        shim = root / "run_gate_lock_with_shim.py"
        shim.write_text(
            f"""
import subprocess
import runpy
from pathlib import Path
import {fixture_module} as fx

real_run = subprocess.run


def _proc(return_code, stdout_text):
    class P:
        pass
    p = P()
    p.returncode = int(return_code)
    p.stdout = str(stdout_text)
    p.stderr = ""
    return p


def patched_run(cmd, cwd=None, capture_output=False, text=False, check=False, **kwargs):
    argv = [str(x) for x in cmd]
    if len(argv) >= 2 and argv[1].endswith("scripts/run_po_sbr_physical_full_track_stability_campaign.py"):
        rc = fx.run_stability(argv[2:])
        return _proc(rc, "PO-SBR physical full-track stability campaign completed.")
    if len(argv) >= 2 and argv[1].endswith("scripts/run_po_sbr_realism_threshold_hardening_campaign.py"):
        rc = fx.run_hardening(argv[2:])
        return _proc(rc, "PO-SBR realism threshold hardening campaign completed.")
    return real_run(cmd, cwd=cwd, capture_output=capture_output, text=text, check=check, **kwargs)


subprocess.run = patched_run
script_path = Path({str((repo_root / "scripts" / "run_po_sbr_physical_full_track_gate_lock.py"))!r})
runpy.run_path(str(script_path), run_name="__main__")
""".strip()
            + "\n",
            encoding="utf-8",
        )

        run_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                str(shim),
                "--full-track-bundle-summary-json",
                str(bundle_summary),
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_summary),
                "--stability-runs",
                "3",
                "--threshold-profile",
                "realism_tight_v2",
                "--realism-gate-candidate",
                "realism_tight_v2",
                "--strict-ready",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if run_proc.returncode != 0:
            raise AssertionError(
                "gate-lock run failed\n"
                f"stdout:\n{run_proc.stdout}\n"
                f"stderr:\n{run_proc.stderr}\n"
            )
        assert "PO-SBR physical full-track gate lock completed." in run_proc.stdout, run_proc.stdout

        validate_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/validate_po_sbr_physical_full_track_gate_lock_report.py",
                "--summary-json",
                str(out_summary),
                "--require-ready",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "validate_po_sbr_physical_full_track_gate_lock_report: pass" in validate_proc.stdout, validate_proc.stdout

        payload = json.loads(out_summary.read_text(encoding="utf-8"))
        assert payload.get("gate_lock_status") == "ready"
        assert payload.get("realism_gate_candidate") == "realism_tight_v2"
        summary = dict(payload.get("summary") or {})
        assert int(summary.get("stability_runs_requested", -1)) == 3
        assert int(summary.get("threshold_profile_count", -1)) == 1
        assert str(summary.get("stability_status", "")) == "stable"
        assert str(summary.get("hardening_status", "")) == "hardened"
        assert str(summary.get("realism_gate_candidate_status", "")) == "ready"

    print("validate_run_po_sbr_physical_full_track_gate_lock: pass")


if __name__ == "__main__":
    run()

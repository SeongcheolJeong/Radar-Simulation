#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _write_bundle_fixture(path: Path) -> None:
    root = path.parent
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for profile in (
        "dual_target_split_range25_v1",
        "single_target_material_loss_range25_v1",
        "mesh_dihedral_range25_v1",
        "mesh_trihedral_range25_v1",
    ):
        profile_root = root / profile
        profile_root.mkdir(parents=True, exist_ok=True)
        golden = profile_root / "scene_backend_golden_path.json"
        kpi = profile_root / "scene_backend_kpi_campaign.json"

        # Minimal structure consumed by the campaign runner.
        golden.write_text(
            json.dumps(
                {
                    "version": 1,
                    "requested_backends": ["analytic_targets", "sionna_rt", "po_sbr_rt"],
                    "results": {
                        "analytic_targets": {
                            "status": "executed",
                            "radar_map_npz": str(profile_root / "analytic.npz"),
                        },
                        "sionna_rt": {
                            "status": "executed",
                            "radar_map_npz": str(profile_root / "sionna.npz"),
                        },
                        "po_sbr_rt": {
                            "status": "executed",
                            "radar_map_npz": str(profile_root / "po.npz"),
                        },
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        kpi.write_text(
            json.dumps(
                {
                    "version": 1,
                    "campaign_status": "ready",
                    "blockers": [],
                    "summary": {
                        "requested_backend_count": 3,
                        "executed_backend_count": 3,
                        "compared_pair_count": 2,
                        "parity_fail_count": 0,
                    },
                    "comparisons": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        rows.append(
            {
                "profile": profile,
                "profile_family": "realism_informational",
                "golden_summary_json": str(golden.resolve()),
                "kpi_summary_json": str(kpi.resolve()),
            }
        )
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "full_track_status": "ready",
                "rows": rows,
                "summary": {"gate_blocked_profile_count": 0},
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_stability_fixture(path: Path) -> None:
    path.write_text(
        json.dumps({"version": 1, "campaign_status": "stable"}, indent=2),
        encoding="utf-8",
    )


def _write_runtime_fixture(module_path: Path) -> str:
    module_path.write_text(
        """
import json
from pathlib import Path


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_kpi_campaign(args):
    # Arguments contain: --golden-path-summary-json <path> --thresholds-json <path> --output-summary-json <path>
    argv = list(args)
    g = Path(argv[argv.index("--golden-path-summary-json") + 1]).resolve()
    t = Path(argv[argv.index("--thresholds-json") + 1]).resolve()
    out = Path(argv[argv.index("--output-summary-json") + 1]).resolve()
    _ = _load_json(g)
    thresholds = _load_json(t)
    _ = thresholds
    payload = {
        "version": 1,
        "campaign_status": "ready",
        "blockers": [],
        "summary": {
            "requested_backend_count": 3,
            "executed_backend_count": 3,
            "compared_pair_count": 2,
            "parity_fail_count": 0,
            "parity_fail_pairs": [],
        },
        "comparisons": [],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return module_path.stem


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="validate_po_sbr_threshold_hardening_") as td:
        root = Path(td)
        bundle_summary = root / "full_track_bundle.json"
        stability_summary = root / "stability.json"
        out_root = root / "hardening"
        out_summary = root / "hardening_summary.json"

        _write_bundle_fixture(bundle_summary)
        _write_stability_fixture(stability_summary)
        fixture_module = _write_runtime_fixture(root / "threshold_hardening_fixture.py")

        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(root), str(repo_root / "src")])

        # Monkeypatch by invoking a tiny shim process that intercepts KPI script calls.
        shim = root / "run_hardening_with_shim.py"
        shim.write_text(
            f"""
import subprocess
import sys
from pathlib import Path
import runpy
import {fixture_module} as fx

real_run = subprocess.run

def patched_run(cmd, cwd=None, capture_output=False, text=False, check=False, **kwargs):
    argv = [str(x) for x in cmd]
    if len(argv) >= 2 and argv[1].endswith("scripts/run_scene_backend_kpi_campaign.py"):
        rc = fx.run_kpi_campaign(argv[2:])
        class P: pass
        p = P()
        p.returncode = rc
        p.stdout = "shimmed"
        p.stderr = ""
        return p
    if len(argv) >= 2 and argv[1].endswith("scripts/validate_scene_backend_kpi_campaign_report.py"):
        class P: pass
        p = P()
        p.returncode = 0
        p.stdout = "validate_scene_backend_kpi_campaign_report: pass"
        p.stderr = ""
        return p
    return real_run(cmd, cwd=cwd, capture_output=capture_output, text=text, check=check, **kwargs)

subprocess.run = patched_run
script_path = Path({str((repo_root / "scripts" / "run_po_sbr_realism_threshold_hardening_campaign.py"))!r})
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
                "--stability-summary-json",
                str(stability_summary),
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_summary),
                "--strict-hardened",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if run_proc.returncode != 0:
            raise AssertionError(
                "threshold hardening run failed\n"
                f"stdout:\n{run_proc.stdout}\n"
                f"stderr:\n{run_proc.stderr}\n"
            )
        assert (
            "PO-SBR realism threshold hardening campaign completed." in run_proc.stdout
        ), run_proc.stdout

        validate_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/validate_po_sbr_realism_threshold_hardening_report.py",
                "--summary-json",
                str(out_summary),
                "--require-hardened",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert (
            "validate_po_sbr_realism_threshold_hardening_report: pass" in validate_proc.stdout
        ), validate_proc.stdout

        payload = json.loads(out_summary.read_text(encoding="utf-8"))
        assert payload.get("hardening_status") == "hardened"
        assert payload.get("realism_gate_candidate") == "realism_tight_v2"
        assert payload.get("realism_gate_candidate_status") == "ready"
        summary = dict(payload.get("summary") or {})
        assert int(summary.get("threshold_profile_count", -1)) >= 1
        assert int(summary.get("threshold_failed_count", -1)) == 0
        assert str(summary.get("realism_gate_candidate_status", "")) == "ready"

    print("validate_run_po_sbr_realism_threshold_hardening_campaign: pass")


if __name__ == "__main__":
    run()

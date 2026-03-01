#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _write_runtime_fixture(module_path: Path) -> str:
    module_path.write_text(
        """
C0 = 299_792_458.0


def sionna_provider(context):
    n = int(context.get("n_chirps", 1))
    rng = 25.0
    delay = 2.0 * rng / C0
    out = []
    for k in range(n):
        out.append(
            [
                {
                    "delay_s": delay,
                    "doppler_hz": 0.0,
                    "unit_direction": [1.0, 0.0, 0.0],
                    "amp": 1.0 / (rng * rng),
                    "path_id": f"fixture_sionna_{k}",
                    "material_tag": "fixture",
                    "reflection_order": 1,
                }
            ]
        )
    return {"paths_by_chirp": out}


def po_provider(context):
    n = int(context.get("n_chirps", 1))
    rng = 25.0
    delay = 2.0 * rng / C0
    out = []
    for k in range(n):
        out.append(
            {
                "chirp_index": int(k),
                "delay_s": delay,
                "doppler_hz": 0.0,
                "unit_direction": [1.0, 0.0, 0.0],
                "amp": 1.0 / (rng * rng),
                "path_id": f"fixture_po_{k}",
                "material_tag": "fixture",
                "reflection_order": 1,
            }
        )
    return {"paths": out}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return module_path.stem


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="validate_scene_backend_kpi_campaign_") as td:
        root = Path(td)
        fixture_module = _write_runtime_fixture(root / "kpi_runtime_fixture.py")

        golden_summary = root / "golden_summary.json"
        kpi_summary = root / "kpi_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(root), str(repo_root / "src")])

        run_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_scene_backend_golden_path.py",
                "--output-root",
                str(root / "golden_run"),
                "--output-summary-json",
                str(golden_summary),
                "--n-chirps",
                "4",
                "--samples-per-chirp",
                "512",
                "--sionna-runtime-provider",
                f"{fixture_module}:sionna_provider",
                "--sionna-runtime-required-modules",
                "",
                "--po-sbr-runtime-provider",
                f"{fixture_module}:po_provider",
                "--po-sbr-runtime-required-modules",
                "",
                "--strict-nonexecuted",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scene backend golden-path run completed." in run_proc.stdout, run_proc.stdout

        kpi_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_scene_backend_kpi_campaign.py",
                "--golden-path-summary-json",
                str(golden_summary),
                "--output-summary-json",
                str(kpi_summary),
                "--strict-ready",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scene backend KPI campaign completed." in kpi_proc.stdout, kpi_proc.stdout

        payload = json.loads(kpi_summary.read_text(encoding="utf-8"))
        assert payload["campaign_status"] == "ready"

        validate_proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/validate_scene_backend_kpi_campaign_report.py",
                "--summary-json",
                str(kpi_summary),
                "--require-ready",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "validate_scene_backend_kpi_campaign_report: pass" in validate_proc.stdout, validate_proc.stdout

    print("validate_run_scene_backend_kpi_campaign: pass")


if __name__ == "__main__":
    run()

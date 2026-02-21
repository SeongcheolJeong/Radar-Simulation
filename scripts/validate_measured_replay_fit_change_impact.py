#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def _write_plan(root: Path, name: str, fit_ref: Optional[str]) -> Path:
    pack = root / f"pack_{name}"
    pack.mkdir(parents=True, exist_ok=True)

    profile_json = pack / "scenario_profile.json"
    profile_json.write_text(
        json.dumps(
            {
                "version": 1,
                "scenario_id": name,
                "parity_thresholds": {"ra_shape_nmse": 1.0},
                "reference_estimation_npz": str(pack / "candidates" / "ref.npz"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    cand_dir = pack / "candidates"
    cand_dir.mkdir(parents=True, exist_ok=True)
    # Small placeholder files; analyzer only reads manifest/profile text.
    (cand_dir / "ref.npz").write_bytes(b"npz")
    (cand_dir / "cand.npz").write_bytes(b"npz")

    cand_row = {
        "name": "cand",
        "estimation_npz": str(cand_dir / "cand.npz"),
    }
    if fit_ref is not None:
        cand_row["metadata"] = {
            "path_power_fit_json": str(fit_ref),
        }

    manifest_json = pack / "replay_manifest.json"
    manifest_json.write_text(
        json.dumps(
            {
                "version": 1,
                "cases": [
                    {
                        "scenario_id": name,
                        "profile_json": str(profile_json),
                        "candidates": [cand_row],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    plan_json = root / f"plan_{name}.json"
    plan_json.write_text(
        json.dumps(
            {
                "version": 1,
                "packs": [
                    {
                        "pack_id": f"pack_{name}",
                        "replay_manifest_json": str(manifest_json),
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return plan_json


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "analyze_measured_replay_fit_change_impact.py"

    with tempfile.TemporaryDirectory(prefix="validate_replay_fit_impact_") as td:
        root = Path(td)
        fit_dir = root / "selected_fits_mixed"
        fit_dir.mkdir(parents=True, exist_ok=True)
        fit_json = fit_dir / "path_power_fit_reflection_selected.json"
        fit_json.write_text("{}", encoding="utf-8")

        plan_noop = _write_plan(root, name="noop", fit_ref=None)
        plan_imp = _write_plan(root, name="impact", fit_ref=str(fit_json))

        out_json = root / "impact_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        cmd = [
            "python3",
            str(cli),
            "--plan-json",
            str(plan_noop),
            "--plan-json",
            str(plan_imp),
            "--fit-dir",
            str(fit_dir),
            "--output-json",
            str(out_json),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"fit-impact analyzer failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        if int(payload["plan_count"]) != 2:
            raise AssertionError("unexpected plan_count")
        if int(payload["impacted_plan_count"]) != 1:
            raise AssertionError("expected one impacted plan")

        plans = payload.get("plans", [])
        if len(plans) != 2:
            raise AssertionError("plans length mismatch")
        by_name = {Path(x["plan_json"]).name: x for x in plans}
        if not bool(by_name[plan_noop.name]["predicted_noop_for_fit_change"]):
            raise AssertionError("noop plan should be predicted noop")
        if bool(by_name[plan_imp.name]["predicted_noop_for_fit_change"]):
            raise AssertionError("impact plan should not be predicted noop")

    print("validate_measured_replay_fit_change_impact: pass")


if __name__ == "__main__":
    main()

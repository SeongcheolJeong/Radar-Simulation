#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _write_fit(path: Path, model: str, tag: str) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "fit": {
                    "model": str(model),
                    "best_params": {
                        "tag": str(tag),
                        "range_power_exponent": 3.0,
                        "gain_scale": 1.0,
                    },
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_ab_report(path: Path, mode: str, rmse_score: float, cross_score: float, winner: str, tie: bool) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "mode": str(mode),
                "runs": {
                    "rmse_lock": {
                        "score": float(rmse_score),
                    },
                    "cross_family_lock": {
                        "score": float(cross_score),
                    },
                },
                "ab_comparison": {
                    "winner_run_id": str(winner),
                    "score_tie": bool(tie),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "select_path_power_fit_mixed_from_ab_reports.py"

    with tempfile.TemporaryDirectory(prefix="validate_mixed_fit_selection_") as td:
        root = Path(td)
        rmse_dir = root / "rmse"
        cross_dir = root / "cross"
        rmse_dir.mkdir(parents=True, exist_ok=True)
        cross_dir.mkdir(parents=True, exist_ok=True)

        _write_fit(rmse_dir / "path_power_fit_reflection_selected.json", "reflection", "rmse_ref")
        _write_fit(cross_dir / "path_power_fit_reflection_selected.json", "reflection", "cross_ref")
        _write_fit(rmse_dir / "path_power_fit_scattering_selected.json", "scattering", "rmse_scat")
        _write_fit(cross_dir / "path_power_fit_scattering_selected.json", "scattering", "cross_scat")

        report_ref = root / "ab_reflection.json"
        report_scat = root / "ab_scattering.json"
        _write_ab_report(
            report_ref,
            mode="reflection",
            rmse_score=10.0,
            cross_score=10.0,
            winner="cross_family_lock",
            tie=True,
        )
        _write_ab_report(
            report_scat,
            mode="scattering",
            rmse_score=100.0,
            cross_score=20.0,
            winner="cross_family_lock",
            tie=False,
        )

        out_dir = root / "mixed"
        out_summary = root / "mixed_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        cmd = [
            "python3",
            str(cli),
            "--ab-report",
            f"reflection={report_ref}",
            "--ab-report",
            f"scattering={report_scat}",
            "--rmse-selected-dir",
            str(rmse_dir),
            "--cross-selected-dir",
            str(cross_dir),
            "--tie-policy",
            "keep_rmse",
            "--output-dir",
            str(out_dir),
            "--output-summary-json",
            str(out_summary),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"mixed selection CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        ref_payload = json.loads((out_dir / "path_power_fit_reflection_selected.json").read_text(encoding="utf-8"))
        scat_payload = json.loads((out_dir / "path_power_fit_scattering_selected.json").read_text(encoding="utf-8"))

        ref_sel = ref_payload.get("selection", {})
        scat_sel = scat_payload.get("selection", {})

        if ref_sel.get("source_type") != "rmse_lock":
            raise AssertionError(f"reflection tie policy not applied: {ref_sel}")
        if scat_sel.get("source_type") != "cross_family_lock":
            raise AssertionError(f"scattering winner not applied: {scat_sel}")

        summary = json.loads(out_summary.read_text(encoding="utf-8"))
        models = sorted([str(x.get("model")) for x in summary.get("models", [])])
        if models != ["reflection", "scattering"]:
            raise AssertionError(f"unexpected models in summary: {models}")

    print("validate_path_power_fit_selection_mixed_from_ab: pass")


if __name__ == "__main__":
    main()

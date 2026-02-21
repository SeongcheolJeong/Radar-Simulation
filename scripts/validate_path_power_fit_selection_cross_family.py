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
                        "range_power_exponent": 3.0,
                        "gain_scale": 1.0,
                        "tag": str(tag),
                    },
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_ranking(path: Path, model: str, fit_json: Path, score: float) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "model": str(model),
                "candidate_count": 2,
                "ok_count": 2,
                "ranked": [
                    {
                        "candidate_index": 0,
                        "fit_json": str(fit_json),
                        "status": "ok",
                        "score": float(score),
                        "b_tuned_pass": False,
                        "ra_mean_delta": 1.0,
                        "rd_mean_delta": 0.5,
                    }
                ],
                "best": {
                    "candidate_index": 0,
                    "fit_json": str(fit_json),
                    "status": "ok",
                    "score": float(score),
                    "b_tuned_pass": False,
                    "ra_mean_delta": 1.0,
                    "rd_mean_delta": 0.5,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "select_path_power_fit_from_cross_family_ranking.py"

    with tempfile.TemporaryDirectory(prefix="validate_cross_family_fit_selection_") as td:
        root = Path(td)
        fit_ref = root / "fit_reflection.json"
        fit_scat = root / "fit_scattering.json"
        _write_fit(fit_ref, model="reflection", tag="ref")
        _write_fit(fit_scat, model="scattering", tag="scat")

        ranking_ref = root / "ranking_reflection.json"
        ranking_scat = root / "ranking_scattering.json"
        _write_ranking(ranking_ref, model="reflection", fit_json=fit_ref, score=10.0)
        _write_ranking(ranking_scat, model="scattering", fit_json=fit_scat, score=20.0)

        out_dir = root / "selected"
        out_summary = root / "selected_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        cmd = [
            "python3",
            str(cli),
            "--ranking-summary",
            f"r={ranking_ref}",
            "--ranking-summary",
            f"s={ranking_scat}",
            "--output-dir",
            str(out_dir),
            "--output-summary-json",
            str(out_summary),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"cross-family fit selection failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        out_ref = out_dir / "path_power_fit_reflection_selected.json"
        out_scat = out_dir / "path_power_fit_scattering_selected.json"
        if not out_ref.exists() or not out_scat.exists():
            raise AssertionError("selected fit json outputs are missing")

        p_ref = json.loads(out_ref.read_text(encoding="utf-8"))
        p_scat = json.loads(out_scat.read_text(encoding="utf-8"))
        if p_ref.get("selection", {}).get("selection_strategy") != "cross_family_ranking_best_score":
            raise AssertionError("reflection selection metadata missing")
        if p_scat.get("selection", {}).get("selection_strategy") != "cross_family_ranking_best_score":
            raise AssertionError("scattering selection metadata missing")

        summary = json.loads(out_summary.read_text(encoding="utf-8"))
        models = sorted([str(x.get("model")) for x in summary.get("models", [])])
        if models != ["reflection", "scattering"]:
            raise AssertionError(f"unexpected selected models: {models}")

    print("validate_path_power_fit_selection_cross_family: pass")


if __name__ == "__main__":
    main()

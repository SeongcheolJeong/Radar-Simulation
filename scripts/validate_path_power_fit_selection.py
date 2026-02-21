#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _fit_payload(model: str, rmse: float, rexp: float) -> dict:
    return {
        "version": 1,
        "model": model,
        "fit": {
            "model": model,
            "sample_count": 10,
            "searched_candidates": 1,
            "best_params": {"range_power_exponent": rexp, "gain_scale": 1.0},
            "best_metrics": {"rmse_log": rmse, "mae_log": rmse},
        },
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "select_path_power_fit_from_experiment.py"

    with tempfile.TemporaryDirectory(prefix="validate_fit_selection_") as td:
        root = Path(td)
        fits = root / "fits"
        fits.mkdir(parents=True, exist_ok=True)

        r_128 = fits / "r_128.json"
        r_512_a = fits / "r_512_a.json"
        r_512_b = fits / "r_512_b.json"
        s_128 = fits / "s_128.json"
        s_512 = fits / "s_512.json"

        r_128.write_text(json.dumps(_fit_payload("reflection", rmse=0.10, rexp=2.5)), encoding="utf-8")
        r_512_a.write_text(json.dumps(_fit_payload("reflection", rmse=0.30, rexp=5.0)), encoding="utf-8")
        r_512_b.write_text(json.dumps(_fit_payload("reflection", rmse=0.20, rexp=4.5)), encoding="utf-8")
        s_128.write_text(json.dumps(_fit_payload("scattering", rmse=0.09, rexp=2.5)), encoding="utf-8")
        s_512.write_text(json.dumps(_fit_payload("scattering", rmse=0.15, rexp=5.0)), encoding="utf-8")

        exp_summary = {
            "version": 1,
            "experiments": [
                {
                    "frame_count": 128,
                    "fit_summary": {
                        "runs": [
                            {"case_label": "a", "model": "reflection", "best_rmse_log": 0.10, "best_mae_log": 0.10, "sample_count": 10, "fit_json": str(r_128)},
                            {"case_label": "a", "model": "scattering", "best_rmse_log": 0.09, "best_mae_log": 0.09, "sample_count": 10, "fit_json": str(s_128)},
                        ]
                    },
                },
                {
                    "frame_count": 512,
                    "fit_summary": {
                        "runs": [
                            {"case_label": "a", "model": "reflection", "best_rmse_log": 0.30, "best_mae_log": 0.30, "sample_count": 10, "fit_json": str(r_512_a)},
                            {"case_label": "b", "model": "reflection", "best_rmse_log": 0.20, "best_mae_log": 0.20, "sample_count": 10, "fit_json": str(r_512_b)},
                            {"case_label": "b", "model": "scattering", "best_rmse_log": 0.15, "best_mae_log": 0.15, "sample_count": 10, "fit_json": str(s_512)},
                        ]
                    },
                },
            ],
        }
        exp_json = root / "exp_summary.json"
        exp_json.write_text(json.dumps(exp_summary, indent=2), encoding="utf-8")

        out_dir = root / "selected"
        out_summary = root / "selection_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        cmd = [
            "python3",
            str(cli),
            "--experiment-summary-json",
            str(exp_json),
            "--selection-strategy",
            "largest_frame_then_rmse",
            "--output-dir",
            str(out_dir),
            "--output-summary-json",
            str(out_summary),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"selection CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        payload = json.loads(out_summary.read_text(encoding="utf-8"))
        rows = {x["model"]: x for x in payload["models"]}

        # largest_frame_then_rmse should choose 512/b for reflection.
        sel_ref = rows["reflection"]["selected"]
        if int(sel_ref["frame_count"]) != 512 or str(sel_ref["case_label"]) != "b":
            raise AssertionError(f"unexpected reflection selection: {sel_ref}")

        sel_scat = rows["scattering"]["selected"]
        if int(sel_scat["frame_count"]) != 512:
            raise AssertionError(f"unexpected scattering selection: {sel_scat}")

        for name in ["path_power_fit_reflection_selected.json", "path_power_fit_scattering_selected.json"]:
            p = out_dir / name
            if not p.exists():
                raise AssertionError(f"missing selected fit: {p}")
            j = json.loads(p.read_text(encoding="utf-8"))
            if "selection" not in j:
                raise AssertionError("selection metadata missing")

    print("validate_path_power_fit_selection: pass")


if __name__ == "__main__":
    main()

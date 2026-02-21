#!/usr/bin/env python3
import csv
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _write_csv(path: Path, scenario_id: str, rows) -> None:
    cols = ["scenario_id", "range_m", "az_rad", "el_rad", "observed_amp"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            row = {
                "scenario_id": scenario_id,
                "range_m": float(r[0]),
                "az_rad": float(r[1]),
                "el_rad": float(r[2]),
                "observed_amp": float(r[3]),
            }
            w.writerow(row)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "run_path_power_fit_batch.py"

    with tempfile.TemporaryDirectory(prefix="validate_path_power_fit_batch_") as td:
        root = Path(td)
        csv_a = root / "case_a.csv"
        csv_b = root / "case_b.csv"

        # Case A: relatively flat decay.
        _write_csv(
            csv_a,
            scenario_id="a",
            rows=[
                (20.0, 0.0, 0.0, 1.0),
                (30.0, 0.1, 0.0, 0.9),
                (40.0, 0.2, 0.0, 0.8),
                (50.0, 0.1, 0.05, 0.75),
            ],
        )

        # Case B: steeper decay.
        _write_csv(
            csv_b,
            scenario_id="b",
            rows=[
                (20.0, 0.0, 0.0, 1.0),
                (30.0, 0.1, 0.0, 0.6),
                (40.0, 0.2, 0.0, 0.4),
                (50.0, 0.1, 0.05, 0.25),
            ],
        )

        out_root = root / "out"
        out_summary = root / "batch_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        cmd = [
            "python3",
            str(cli),
            "--csv-case",
            f"caseA={csv_a}",
            "--csv-case",
            f"caseB={csv_b}",
            "--model",
            "reflection",
            "--model",
            "scattering",
            "--batch-id",
            "validate_batch",
            "--top-k",
            "5",
            "--output-root",
            str(out_root),
            "--output-summary-json",
            str(out_summary),
        ]

        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"fit batch CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        payload = json.loads(out_summary.read_text(encoding="utf-8"))
        assert int(payload["run_count"]) == 4
        by_model = payload["by_model"]
        assert "reflection" in by_model and "scattering" in by_model
        assert int(by_model["reflection"]["count"]) == 2
        assert int(by_model["scattering"]["count"]) == 2

        runs = payload["runs"]
        for row in runs:
            if not Path(row["fit_json"]).exists():
                raise AssertionError(f"missing fit json: {row['fit_json']}")

    print("validate_path_power_fit_batch: pass")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import csv
import json
import subprocess
import tempfile
from pathlib import Path

from avxsim.constants import C0


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "build_path_power_samples_from_path_list.py"

    with tempfile.TemporaryDirectory(prefix="validate_path_power_samples_builder_") as td:
        tmp = Path(td)
        path_list_json = tmp / "path_list.json"
        out_csv = tmp / "samples.csv"

        delay0 = (2.0 * 10.0) / C0
        delay1 = (2.0 * 25.0) / C0
        payload = [
            [
                {
                    "delay_s": delay0,
                    "doppler_hz": 0.0,
                    "unit_direction": [1.0, 0.0, 0.0],
                    "amp_complex": {"re": 2.0, "im": 0.0},
                },
                {
                    "delay_s": delay1,
                    "doppler_hz": 0.0,
                    "unit_direction": [0.0, 1.0, 0.0],
                    "amp_complex": {"re": 0.3, "im": 0.4},
                },
            ]
        ]
        path_list_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        cmd = [
            "python3",
            str(cli),
            "--input-path-list-json",
            str(path_list_json),
            "--output-csv",
            str(out_csv),
            "--scenario-id",
            "demo_scenario",
            "--min-observed-amp",
            "0.0",
            "--sort-by-amp-desc",
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"samples builder CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        rows = []
        with out_csv.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        assert len(rows) == 2
        assert rows[0]["scenario_id"] == "demo_scenario"
        # sorted by amplitude desc, first should be amp=2.0 at range=10m
        r0 = float(rows[0]["range_m"])
        a0 = float(rows[0]["observed_amp"])
        assert abs(r0 - 10.0) < 1e-6, r0
        assert abs(a0 - 2.0) < 1e-6, a0

        r1 = float(rows[1]["range_m"])
        a1 = float(rows[1]["observed_amp"])
        assert abs(r1 - 25.0) < 1e-6, r1
        assert abs(a1 - 0.5) < 1e-6, a1

    print("validate_path_power_samples_builder: pass")


if __name__ == "__main__":
    main()

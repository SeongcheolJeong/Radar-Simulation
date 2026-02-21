#!/usr/bin/env python3
import csv
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _make_adc(shape=(64, 32, 2, 4), seed=0):
    rng = np.random.default_rng(seed)
    s, c, t, r = shape
    ys = np.arange(s, dtype=np.float64)[:, None, None, None]
    yc = np.arange(c, dtype=np.float64)[None, :, None, None]
    tone = np.exp(1j * 2.0 * np.pi * (ys / max(s, 1))) * np.exp(1j * 2.0 * np.pi * (yc / max(c, 1)))
    noise = 0.05 * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    return (tone + noise).astype(np.complex64)


def _write_label_csv(path: Path, rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for row in rows:
            w.writerow(row)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "build_path_power_samples_from_xiangyu_labels.py"

    with tempfile.TemporaryDirectory(prefix="validate_xiangyu_path_power_") as td:
        root = Path(td)
        adc_root = root / "adc"
        labels_root = root / "labels"
        adc_root.mkdir(parents=True, exist_ok=True)
        labels_root.mkdir(parents=True, exist_ok=True)

        # Use numeric suffix mismatch style to validate index matching by trailing digits.
        np.savez_compressed(adc_root / "adc_frame_000001.npz", adc=_make_adc(seed=1))
        np.savez_compressed(adc_root / "adc_frame_000002.npz", adc=_make_adc(seed=2))

        _write_label_csv(
            labels_root / "0000000001.csv",
            [
                [10, 2, -2.0, 8.0, 4.5, 1.8],
                [11, 80, 1.5, 10.0, 1.7, 0.6],
            ],
        )
        _write_label_csv(
            labels_root / "0000000002.csv",
            [
                [20, 3, 0.5, 12.0, 2.0, 1.0],
            ],
        )

        out_csv = root / "path_power_samples.csv"
        out_meta = root / "path_power_samples_meta.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        cmd = [
            "python3",
            str(cli),
            "--adc-root",
            str(adc_root),
            "--labels-root",
            str(labels_root),
            "--output-csv",
            str(out_csv),
            "--output-meta-json",
            str(out_meta),
            "--scenario-id",
            "validate_xiangyu_csv",
            "--adc-type",
            "npz",
            "--adc-glob",
            "*.npz",
            "--adc-order",
            "sctr",
            "--range-max-m",
            "30",
            "--nfft-range",
            "64",
            "--nfft-angle",
            "16",
            "--range-bin-limit",
            "48",
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"xiangyu label->csv CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        if not out_csv.exists():
            raise AssertionError("output CSV missing")
        if not out_meta.exists():
            raise AssertionError("output meta json missing")

        with out_csv.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        if len(rows) != 3:
            raise AssertionError(f"expected 3 rows, got {len(rows)}")
        for row in rows:
            if row["scenario_id"] != "validate_xiangyu_csv":
                raise AssertionError("scenario_id mismatch")
            if float(row["observed_amp"]) <= 0:
                raise AssertionError("observed_amp must be positive")

    print("validate_path_power_samples_from_xiangyu_labels: pass")


if __name__ == "__main__":
    main()

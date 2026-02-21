#!/usr/bin/env python3
import csv
import json
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
    noise = 0.03 * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    return (tone + noise).astype(np.complex64)


def _write_label_csv(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for row in rows:
            w.writerow(row)


def _make_case(root: Path, case_id: str, offset: int) -> tuple[str, str]:
    adc_root = root / case_id / "radar_raw_frame"
    label_root = root / case_id / "text_labels"
    adc_root.mkdir(parents=True, exist_ok=True)
    label_root.mkdir(parents=True, exist_ok=True)

    for i in [1, 2, 3]:
        np.savez_compressed(adc_root / f"adc_frame_{i:06d}.npz", adc=_make_adc(seed=offset + i))

    _write_label_csv(label_root / "0000000001.csv", [[10 + offset, 2, 1.0, 8.0, 4.5, 1.8]])
    _write_label_csv(label_root / "0000000002.csv", [[11 + offset, 3, -1.0, 10.0, 2.0, 1.0]])
    _write_label_csv(label_root / "0000000003.csv", [[12 + offset, 80, 0.5, 12.0, 1.7, 0.6]])

    return str(adc_root), str(label_root)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "run_xiangyu_label_fit_experiment.py"

    with tempfile.TemporaryDirectory(prefix="validate_xiangyu_fit_exp_") as td:
        root = Path(td)
        a_adc, a_lbl = _make_case(root, "caseA", offset=0)
        b_adc, b_lbl = _make_case(root, "caseB", offset=100)
        out_root = root / "out"
        out_summary = root / "exp_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        cmd = [
            "python3",
            str(cli),
            "--case",
            f"a={a_adc}::{a_lbl}",
            "--case",
            f"b={b_adc}::{b_lbl}",
            "--frame-counts",
            "2",
            "--models",
            "reflection,scattering",
            "--output-root",
            str(out_root),
            "--output-summary-json",
            str(out_summary),
            "--adc-type",
            "npz",
            "--adc-glob",
            "*.npz",
            "--adc-order",
            "sctr",
            "--nfft-range",
            "64",
            "--nfft-doppler",
            "32",
            "--nfft-angle",
            "16",
            "--range-bin-limit",
            "48",
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"experiment CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        payload = json.loads(out_summary.read_text(encoding="utf-8"))
        assert payload["frame_counts"] == [2]
        assert payload["models"] == ["reflection", "scattering"]
        assert len(payload["experiments"]) == 1

        exp = payload["experiments"][0]
        assert exp["frame_count"] == 2
        assert len(exp["csv_rows"]) == 2
        for row in exp["csv_rows"]:
            assert Path(row["csv_path"]).exists()
            assert int(row["selected_row_count"]) >= 2

        fit_summary = exp["fit_summary"]
        assert int(fit_summary["run_count"]) == 4
        assert "reflection" in fit_summary["by_model"]
        assert "scattering" in fit_summary["by_model"]

    print("validate_xiangyu_label_fit_experiment: pass")


if __name__ == "__main__":
    main()

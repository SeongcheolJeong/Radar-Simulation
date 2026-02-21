#!/usr/bin/env python3
import csv
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from avxsim.constants import C0
from avxsim.hybrid_pcode import (
    calculate_reflecting_path_power,
    calculate_scattering_path_power,
)
from avxsim.path_power_tuning import fit_path_power_parameters


def _make_scattering_samples(n: int, seed: int = 0):
    rng = np.random.default_rng(seed)
    ranges = rng.uniform(4.0, 40.0, size=n)
    az = rng.uniform(-1.0, 1.0, size=n)
    el = rng.uniform(-0.2, 0.8, size=n)
    true = {
        "range_power_exponent": 3.5,
        "elevation_power": 1.5,
        "azimuth_mix": 0.4,
        "azimuth_power": 3.0,
        "gain_scale": 1.8,
    }
    base = calculate_scattering_path_power(
        p_t_dbm=0.0,
        pixel_width=1,
        pixel_height=1,
        scattering_coefficient=1.0,
        lambda_m=C0 / 77e9,
        temp_range_m=ranges,
        temp_angles_rad=np.stack([az, el], axis=1),
        range_power_exponent=true["range_power_exponent"],
        gain_scale=true["gain_scale"],
        elevation_power=true["elevation_power"],
        azimuth_mix=true["azimuth_mix"],
        azimuth_power=true["azimuth_power"],
    )
    noise = np.exp(rng.normal(loc=0.0, scale=0.01, size=n))
    observed = np.maximum(base * noise, np.finfo(np.float64).tiny)
    return ranges, az, el, observed, true


def _make_reflection_samples(n: int, seed: int = 1):
    rng = np.random.default_rng(seed)
    ranges = rng.uniform(3.0, 30.0, size=n)
    true = {
        "range_power_exponent": 4.5,
        "gain_scale": 0.7,
    }
    base = calculate_reflecting_path_power(
        p_t_dbm=0.0,
        pixel_width=1,
        pixel_height=1,
        reflecting_coefficient=1.0,
        lambda_m=C0 / 77e9,
        temp_range_m=ranges,
        range_power_exponent=true["range_power_exponent"],
        gain_scale=true["gain_scale"],
    )
    noise = np.exp(rng.normal(loc=0.0, scale=0.01, size=n))
    observed = np.maximum(base * noise, np.finfo(np.float64).tiny)
    return ranges, observed, true


def main() -> None:
    r, az, el, obs, true_s = _make_scattering_samples(n=120, seed=42)
    fit_s = fit_path_power_parameters(
        range_m=r,
        observed_amp=obs,
        model="scattering",
        az_rad=az,
        el_rad=el,
        fc_hz=77e9,
        grid={
            "range_power_exponent": [3.0, 3.5, 4.0],
            "elevation_power": [1.0, 1.5, 2.0],
            "azimuth_mix": [0.2, 0.4, 0.6],
            "azimuth_power": [2.0, 3.0, 4.0],
        },
        top_k=3,
    )
    bp_s = fit_s["best_params"]
    assert float(bp_s["range_power_exponent"]) == float(true_s["range_power_exponent"])
    assert float(bp_s["elevation_power"]) == float(true_s["elevation_power"])
    assert float(bp_s["azimuth_mix"]) == float(true_s["azimuth_mix"])
    assert float(bp_s["azimuth_power"]) == float(true_s["azimuth_power"])
    assert float(fit_s["best_metrics"]["rmse_log"]) < 0.08

    rr, robs, true_r = _make_reflection_samples(n=80, seed=7)
    fit_r = fit_path_power_parameters(
        range_m=rr,
        observed_amp=robs,
        model="reflection",
        fc_hz=77e9,
        grid={"range_power_exponent": [4.0, 4.5, 5.0]},
        top_k=3,
    )
    bp_r = fit_r["best_params"]
    assert float(bp_r["range_power_exponent"]) == float(true_r["range_power_exponent"])
    assert float(fit_r["best_metrics"]["rmse_log"]) < 0.08

    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "fit_path_power_model_from_csv.py"
    with tempfile.TemporaryDirectory(prefix="validate_path_power_tuning_") as td:
        csv_path = Path(td) / "samples.csv"
        out_json = Path(td) / "fit.json"
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["range_m", "az_rad", "el_rad", "observed_amp"])
            for i in range(r.size):
                w.writerow([float(r[i]), float(az[i]), float(el[i]), float(obs[i])])

        cmd = [
            "python3",
            str(cli),
            "--input-csv",
            str(csv_path),
            "--model",
            "scattering",
            "--output-json",
            str(out_json),
            "--range-power-grid",
            "3.0,3.5,4.0",
            "--elevation-power-grid",
            "1.0,1.5,2.0",
            "--azimuth-mix-grid",
            "0.2,0.4,0.6",
            "--azimuth-power-grid",
            "2.0,3.0,4.0",
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"fit CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        best = payload["fit"]["best_params"]
        assert float(best["range_power_exponent"]) == 3.5
        assert float(best["elevation_power"]) == 1.5
        assert float(best["azimuth_mix"]) == 0.4
        assert float(best["azimuth_power"]) == 3.0

    print("validate_path_power_tuning: pass")


if __name__ == "__main__":
    main()

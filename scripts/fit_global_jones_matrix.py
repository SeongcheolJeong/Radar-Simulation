#!/usr/bin/env python3
import argparse

import numpy as np

from avxsim.calibration import fit_global_jones_matrix, save_global_jones_matrix_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fit global Jones matrix from calibration samples")
    p.add_argument("--samples-npz", required=True, help="NPZ with tx_jones, rx_jones, observed_gain arrays")
    p.add_argument("--ridge", type=float, default=0.0, help="Non-negative ridge regularization")
    p.add_argument("--output-json", required=True, help="Output JSON path for fitted matrix and metrics")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    with np.load(args.samples_npz, allow_pickle=False) as payload:
        if "tx_jones" not in payload or "rx_jones" not in payload or "observed_gain" not in payload:
            raise ValueError("samples-npz must contain tx_jones, rx_jones, observed_gain")
        tx_jones = payload["tx_jones"]
        rx_jones = payload["rx_jones"]
        observed_gain = payload["observed_gain"]
        path_matrices = payload["path_matrices"] if "path_matrices" in payload else None

    result = fit_global_jones_matrix(
        tx_jones=tx_jones,
        rx_jones=rx_jones,
        observed_gain=observed_gain,
        path_matrices=path_matrices,
        ridge=float(args.ridge),
    )
    save_global_jones_matrix_json(
        out_path=args.output_json,
        matrix=result["global_jones_matrix"],
        metrics=result["metrics"],
    )

    m = result["metrics"]
    print("Global Jones calibration completed.")
    print(f"  sample_count: {m['sample_count']}")
    print(f"  nmse: {m['nmse']:.6g}")
    print(f"  relative_rmse: {m['relative_rmse']:.6g}")
    print(f"  output: {args.output_json}")


if __name__ == "__main__":
    main()


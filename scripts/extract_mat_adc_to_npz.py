#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np

from avxsim.mat_adc_extract import load_adc_from_mat


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Extract 4D ADC arrays from MAT files into NPZ files"
    )
    p.add_argument("--input-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--mat-glob", default="*.mat")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--max-files", type=int, default=None)
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--mat-variable", default=None)
    p.add_argument("--output-prefix", default="adc")
    return p.parse_args()


def _collect_mat_files(root: Path, pattern: str, recursive: bool):
    files = sorted(root.rglob(pattern) if recursive else root.glob(pattern))
    return [p for p in files if p.is_file()]


def main() -> None:
    args = parse_args()
    input_root = Path(args.input_root)
    if not input_root.exists() or not input_root.is_dir():
        raise ValueError(f"input-root must be existing directory: {input_root}")
    if int(args.stride) <= 0:
        raise ValueError("--stride must be positive")

    mat_files = _collect_mat_files(input_root, args.mat_glob, recursive=bool(args.recursive))
    mat_files = mat_files[:: int(args.stride)]
    if args.max_files is not None:
        mat_files = mat_files[: int(args.max_files)]
    if len(mat_files) == 0:
        raise ValueError("no MAT files discovered")

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, mat_path in enumerate(mat_files):
        adc, meta = load_adc_from_mat(str(mat_path), variable=args.mat_variable)

        stem = mat_path.stem
        out_name = f"{args.output_prefix}_{i:04d}_{stem}.npz"
        out_path = output_root / out_name

        np.savez_compressed(
            str(out_path),
            adc=np.asarray(adc),
            metadata_json=json.dumps(
                {
                    "source_mat": str(mat_path),
                    "source_variable": meta.get("variable"),
                    "loader": meta.get("loader"),
                    "shape": meta.get("shape"),
                    "dtype": meta.get("dtype"),
                }
            ),
        )

        rows.append(
            {
                "index": int(i),
                "source_mat": str(mat_path),
                "output_npz": str(out_path),
                "variable": str(meta.get("variable")),
                "shape": meta.get("shape"),
                "dtype": meta.get("dtype"),
                "loader": meta.get("loader"),
            }
        )

    index_json = output_root / "adc_npz_index.json"
    index_json.write_text(json.dumps({"items": rows}, indent=2), encoding="utf-8")

    print("MAT->ADC NPZ extraction completed.")
    print(f"  mat_files: {len(mat_files)}")
    print(f"  output_root: {output_root}")
    print(f"  index_json: {index_json}")


if __name__ == "__main__":
    main()

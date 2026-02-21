#!/usr/bin/env python3
import argparse

from avxsim.parity_drift import (
    build_parity_drift_report,
    load_replay_report_json,
    save_parity_drift_report_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Analyze parity-metric drift across replay reports"
    )
    p.add_argument(
        "--report",
        action="append",
        required=True,
        help="Repeatable label=path form. First report is baseline.",
    )
    p.add_argument("--quantiles", default="0.5,0.9,0.99")
    p.add_argument("--output-json", required=True)
    return p.parse_args()


def _parse_report_arg(text: str):
    s = str(text)
    if "=" not in s:
        raise ValueError("--report must be in label=path form")
    label, path = s.split("=", 1)
    label = label.strip()
    path = path.strip()
    if label == "" or path == "":
        raise ValueError("--report label/path must be non-empty")
    return label, path


def _parse_quantiles(text: str):
    parts = [x.strip() for x in str(text).split(",")]
    out = [float(x) for x in parts if x != ""]
    if len(out) == 0:
        raise ValueError("--quantiles must contain at least one value")
    return out


def main() -> None:
    args = parse_args()
    report_rows = []
    for raw in args.report:
        label, path = _parse_report_arg(raw)
        report_rows.append(
            {
                "name": label,
                "report": load_replay_report_json(path),
            }
        )

    quantiles = _parse_quantiles(args.quantiles)
    payload = build_parity_drift_report(
        reports=report_rows,
        quantiles=quantiles,
    )
    save_parity_drift_report_json(args.output_json, payload)

    print("Parity drift analysis completed.")
    print(f"  baseline: {payload['baseline']}")
    print(f"  scenarios: {len(payload['scenarios'])}")
    print(f"  quantiles: {payload['quantiles']}")
    print(f"  output_json: {args.output_json}")


if __name__ == "__main__":
    main()

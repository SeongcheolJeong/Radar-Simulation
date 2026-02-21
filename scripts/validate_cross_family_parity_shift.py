#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _make_report(path: Path, ra_vals, rd_vals, pass_flags) -> None:
    cands = []
    for i, (ra, rd, p) in enumerate(zip(ra_vals, rd_vals, pass_flags)):
        cands.append(
            {
                "name": f"c{i}",
                "pass": bool(p),
                "metrics": {
                    "ra_shape_nmse": float(ra),
                    "rd_shape_nmse": float(rd),
                },
            }
        )

    pass_count = sum(1 for x in cands if bool(x["pass"]))
    payload = {
        "summary": {
            "case_count": 1,
            "candidate_count": len(cands),
            "pass_count": pass_count,
            "fail_count": len(cands) - pass_count,
            "pass_rate": 0.0 if len(cands) == 0 else pass_count / float(len(cands)),
        },
        "cases": [
            {
                "scenario_id": "demo",
                "candidates": cands,
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "evaluate_cross_family_parity_shift.py"

    with tempfile.TemporaryDirectory(prefix="validate_cross_family_shift_") as td:
        root = Path(td)
        base_a = root / "base_a.json"
        base_b = root / "base_b.json"
        tuned_a = root / "tuned_a.json"
        tuned_b = root / "tuned_b.json"
        out_json = root / "cross_family_shift.json"

        # Baseline has large cross-family gap in RA.
        _make_report(base_a, ra_vals=[0.1, 0.12, 0.13], rd_vals=[0.2, 0.22, 0.25], pass_flags=[1, 1, 0])
        _make_report(base_b, ra_vals=[0.5, 0.52, 0.55], rd_vals=[0.4, 0.45, 0.5], pass_flags=[0, 0, 0])

        # Tuned narrows RA gap and improves pass-rate alignment.
        _make_report(tuned_a, ra_vals=[0.2, 0.22, 0.25], rd_vals=[0.22, 0.24, 0.27], pass_flags=[1, 1, 1])
        _make_report(tuned_b, ra_vals=[0.3, 0.32, 0.34], rd_vals=[0.3, 0.32, 0.35], pass_flags=[1, 1, 1])

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        cmd = [
            "python3",
            str(cli),
            "--baseline-a",
            f"baseA={base_a}",
            "--baseline-b",
            f"baseB={base_b}",
            "--tuned-a",
            f"tunedA={tuned_a}",
            "--tuned-b",
            f"tunedB={tuned_b}",
            "--metric",
            "ra_shape_nmse",
            "--metric",
            "rd_shape_nmse",
            "--quantiles",
            "0.5,0.9",
            "--output-json",
            str(out_json),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"cross-family shift CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        imp = payload["cross_family_gap"]["improvement"]["ra_shape_nmse"]
        if float(imp["q50_gap_reduction_abs"]) <= 0.0:
            raise AssertionError(f"expected RA q50 gap reduction > 0, got {imp['q50_gap_reduction_abs']}")
        if float(payload["pass_rate_gap"]["reduction_abs"]) <= 0.0:
            raise AssertionError("expected pass_rate gap reduction > 0")

    print("validate_cross_family_parity_shift: pass")


if __name__ == "__main__":
    main()

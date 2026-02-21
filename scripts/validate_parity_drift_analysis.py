#!/usr/bin/env python3
import json
import subprocess
import tempfile
from pathlib import Path


def _make_replay_report(path: Path, metric_scale: float) -> None:
    cases = [
        {
            "scenario_id": "demo",
            "candidates": [
                {
                    "name": "c0",
                    "pass": True,
                    "metrics": {
                        "rd_shape_nmse": 0.10 * metric_scale,
                        "ra_shape_nmse": 0.20 * metric_scale,
                    },
                },
                {
                    "name": "c1",
                    "pass": True,
                    "metrics": {
                        "rd_shape_nmse": 0.12 * metric_scale,
                        "ra_shape_nmse": 0.24 * metric_scale,
                    },
                },
                {
                    "name": "c2",
                    "pass": False,
                    "metrics": {
                        "rd_shape_nmse": 0.15 * metric_scale,
                        "ra_shape_nmse": 0.30 * metric_scale,
                    },
                },
            ],
        }
    ]
    payload = {
        "summary": {
            "case_count": 1,
            "candidate_count": 3,
            "pass_count": 2,
            "fail_count": 1,
            "pass_rate": 2.0 / 3.0,
        },
        "cases": cases,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cli = repo_root / "scripts" / "analyze_parity_drift_from_replay_reports.py"

    with tempfile.TemporaryDirectory(prefix="validate_parity_drift_") as td:
        base = Path(td) / "base_report.json"
        cand = Path(td) / "cand_report.json"
        out_json = Path(td) / "drift.json"
        _make_replay_report(base, metric_scale=1.0)
        _make_replay_report(cand, metric_scale=1.5)

        cmd = [
            "python3",
            str(cli),
            "--report",
            f"baseline={base}",
            "--report",
            f"candidate={cand}",
            "--quantiles",
            "0.5,0.9",
            "--output-json",
            str(out_json),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"drift CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["baseline"] == "baseline"
        assert len(payload["scenarios"]) == 2
        drift = payload["drift_vs_baseline"][0]
        rd_q90 = drift["metric_drift"]["rd_shape_nmse"]["q90"]
        ratio = float(rd_q90["ratio"])
        if abs(ratio - 1.5) > 0.02:
            raise AssertionError(f"unexpected drift ratio: {ratio}")

    print("validate_parity_drift_analysis: pass")


if __name__ == "__main__":
    main()

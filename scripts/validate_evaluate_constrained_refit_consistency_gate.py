#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_search_summary(
    case_count: int,
    recommendation: str,
    aggregate_score: float,
    metric_drift_mean: float,
    pass_rate_drop: float = 0.0,
    pass_count_drop_ratio: float = 0.0,
    fail_count_increase_ratio: float = 0.0,
) -> dict:
    return {
        "version": 1,
        "case_count": int(case_count),
        "objective_effective": "drift",
        "policy_gate": {
            "gate_failed": True,
            "recommendation": "hold_fit_lock_no_material_gain",
        },
        "selection": {
            "selection_mode": "fit",
            "recommendation": recommendation,
            "selected_fit_json": "/tmp/fit.json",
            "selected_fit_summary": {
                "fit_json": "/tmp/fit.json",
                "case_count": int(case_count),
                "coverage_count": int(case_count),
                "aggregate_score": float(aggregate_score),
                "total_pass_rate_drop": float(pass_rate_drop),
                "total_pass_count_drop_ratio": float(pass_count_drop_ratio),
                "total_fail_count_increase_ratio": float(fail_count_increase_ratio),
                "metric_drift_mean": float(metric_drift_mean),
                "cases": [],
            },
        },
    }


def _run(cmd, cwd: Path, env):
    return subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, check=False)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    with tempfile.TemporaryDirectory(prefix="validate_constrained_consistency_") as td:
        root = Path(td)

        search_flat = root / "search_flat.json"
        search_steep = root / "search_steep.json"
        _write_json(
            search_flat,
            _build_search_summary(
                case_count=3,
                recommendation="adopt_selected_fit_by_drift_objective",
                aggregate_score=0.08,
                metric_drift_mean=0.08,
            ),
        )
        _write_json(
            search_steep,
            _build_search_summary(
                case_count=3,
                recommendation="exploratory_fit_candidate_selected_by_drift",
                aggregate_score=0.6,
                metric_drift_mean=0.6,
                pass_rate_drop=0.02,
                pass_count_drop_ratio=0.02,
                fail_count_increase_ratio=0.02,
            ),
        )

        constrained = {
            "version": 1,
            "rows": [
                {
                    "preset": "flat",
                    "search_ok": True,
                    "selection_mode": "fit",
                    "selection_recommendation": "adopt_selected_fit_by_drift_objective",
                    "selected_fit_json": "/tmp/flat_fit.json",
                    "selected_aggregate_score": 0.08,
                    "search_summary_json": str(search_flat),
                },
                {
                    "preset": "steep",
                    "search_ok": True,
                    "selection_mode": "fit",
                    "selection_recommendation": "exploratory_fit_candidate_selected_by_drift",
                    "selected_fit_json": "/tmp/steep_fit.json",
                    "selected_aggregate_score": 0.6,
                    "search_summary_json": str(search_steep),
                },
            ],
        }
        constrained_json = root / "constrained_summary.json"
        _write_json(constrained_json, constrained)

        out_ok = root / "gate_ok.json"
        cmd_ok = [
            "python3",
            "scripts/evaluate_constrained_refit_consistency_gate.py",
            "--constrained-summary-json",
            str(constrained_json),
            "--output-json",
            str(out_ok),
            "--max-metric-drift-mean",
            "0.2",
        ]
        p_ok = _run(cmd_ok, cwd=repo_root, env=env)
        if p_ok.returncode != 0:
            raise RuntimeError(f"gate eval failed:\nSTDOUT:\n{p_ok.stdout}\nSTDERR:\n{p_ok.stderr}")
        payload_ok = json.loads(out_ok.read_text(encoding="utf-8"))
        if bool(payload_ok.get("gate_failed", True)):
            raise AssertionError("gate should pass for flat preset")
        if str(payload_ok.get("selected_preset", "")) != "flat":
            raise AssertionError("flat should be selected in success case")

        out_fb = root / "gate_fallback.json"
        cmd_fb = [
            "python3",
            "scripts/evaluate_constrained_refit_consistency_gate.py",
            "--constrained-summary-json",
            str(constrained_json),
            "--output-json",
            str(out_fb),
            "--max-metric-drift-mean",
            "0.01",
        ]
        p_fb = _run(cmd_fb, cwd=repo_root, env=env)
        if p_fb.returncode != 0:
            raise RuntimeError(f"gate fallback eval failed:\nSTDOUT:\n{p_fb.stdout}\nSTDERR:\n{p_fb.stderr}")
        payload_fb = json.loads(out_fb.read_text(encoding="utf-8"))
        if bool(payload_fb.get("gate_failed", False)) is not True:
            raise AssertionError("gate should fail under strict drift threshold")
        if str(payload_fb.get("selection_mode", "")) != "baseline_no_fit":
            raise AssertionError("fallback mode should be baseline_no_fit")

    print("validate_evaluate_constrained_refit_consistency_gate: pass")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Build mixed locked fits from A/B comparison reports (RMSE lock vs cross-family lock)."
        )
    )
    p.add_argument(
        "--ab-report",
        action="append",
        required=True,
        help="A/B report path or model=path",
    )
    p.add_argument("--rmse-selected-dir", required=True)
    p.add_argument("--cross-selected-dir", required=True)
    p.add_argument(
        "--tie-policy",
        choices=["keep_rmse", "prefer_cross_family"],
        default="keep_rmse",
    )
    p.add_argument("--output-dir", required=True)
    p.add_argument("--output-summary-json", default=None)
    return p.parse_args()


def _load_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json must be object: {path}")
    return payload


def _parse_report_ref(value: str) -> Tuple[str, str]:
    raw = str(value).strip()
    if raw == "":
        raise ValueError("ab-report entry must be non-empty")
    if "=" in raw:
        model, path = raw.split("=", 1)
        return str(model).strip().lower(), str(path).strip()
    return "", raw


def _path_for_model(root: Path, model: str) -> Path:
    return root / f"path_power_fit_{model}_selected.json"


def _write_selected_fit(
    src_fit: Mapping[str, Any],
    out_json: Path,
    model: str,
    source_type: str,
    source_fit_json: str,
    ab_report_json: str,
    tie_policy: str,
) -> None:
    payload = dict(src_fit)
    payload["selection"] = {
        "selection_strategy": "mixed_from_ab_reports",
        "model": str(model),
        "source_type": str(source_type),
        "source_fit_json": str(source_fit_json),
        "source_ab_report_json": str(ab_report_json),
        "tie_policy": str(tie_policy),
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rmse_dir = Path(args.rmse_selected_dir)
    cross_dir = Path(args.cross_selected_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    seen_models = set()

    for raw in args.ab_report:
        model_hint, report_path = _parse_report_ref(raw)
        report = _load_json(report_path)

        model = str(report.get("mode", "")).strip().lower()
        if model not in {"reflection", "scattering"}:
            raise ValueError(f"invalid mode in report: {report_path}")
        if model_hint not in {"", model}:
            raise ValueError(f"model hint mismatch for {report_path}: hint={model_hint}, report={model}")
        if model in seen_models:
            raise ValueError(f"duplicate model report provided: {model}")

        runs = report.get("runs", {})
        if not isinstance(runs, Mapping):
            raise ValueError(f"invalid runs in report: {report_path}")
        ab = report.get("ab_comparison", {})
        if not isinstance(ab, Mapping):
            raise ValueError(f"invalid ab_comparison in report: {report_path}")

        score_tie = bool(ab.get("score_tie", False))
        winner = str(ab.get("winner_run_id", "")).strip()
        if winner not in {"rmse_lock", "cross_family_lock"}:
            raise ValueError(f"invalid winner in report: {report_path}")

        if score_tie and args.tie_policy == "keep_rmse":
            selected_source = "rmse_lock"
        elif score_tie and args.tie_policy == "prefer_cross_family":
            selected_source = "cross_family_lock"
        else:
            selected_source = winner

        if selected_source == "rmse_lock":
            source_type = "rmse_lock"
            src_fit_json = _path_for_model(rmse_dir, model)
        else:
            source_type = "cross_family_lock"
            src_fit_json = _path_for_model(cross_dir, model)

        if not src_fit_json.exists():
            raise FileNotFoundError(f"missing selected fit for {model}: {src_fit_json}")

        src_fit = _load_json(str(src_fit_json))
        fit_obj = src_fit.get("fit", {})
        if not isinstance(fit_obj, Mapping):
            raise ValueError(f"invalid fit payload: {src_fit_json}")
        if str(fit_obj.get("model", "")).strip().lower() != model:
            raise ValueError(f"fit model mismatch: {src_fit_json}")

        out_fit_json = _path_for_model(out_dir, model)
        _write_selected_fit(
            src_fit=src_fit,
            out_json=out_fit_json,
            model=model,
            source_type=source_type,
            source_fit_json=str(src_fit_json),
            ab_report_json=str(report_path),
            tie_policy=str(args.tie_policy),
        )

        rmse_score = float(runs.get("rmse_lock", {}).get("score", 0.0))
        cross_score = float(runs.get("cross_family_lock", {}).get("score", 0.0))
        rows.append(
            {
                "model": str(model),
                "report_json": str(report_path),
                "winner_run_id": str(winner),
                "score_tie": bool(score_tie),
                "rmse_score": float(rmse_score),
                "cross_family_score": float(cross_score),
                "selected_source": str(selected_source),
                "selected_source_fit_json": str(src_fit_json),
                "output_fit_json": str(out_fit_json),
            }
        )
        seen_models.add(model)

    if len(rows) == 0:
        raise ValueError("no models processed")

    summary = {
        "version": 1,
        "selection_strategy": "mixed_from_ab_reports",
        "tie_policy": str(args.tie_policy),
        "rmse_selected_dir": str(rmse_dir),
        "cross_selected_dir": str(cross_dir),
        "output_dir": str(out_dir),
        "models": rows,
    }

    out_summary = (
        out_dir / "path_power_fit_selection_mixed_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    model_list = ",".join(sorted([str(x["model"]) for x in rows]))
    print("Mixed fit selection from A/B reports completed.")
    print(f"  models: {model_list}")
    print(f"  tie_policy: {args.tie_policy}")
    print(f"  output_dir: {out_dir}")
    print(f"  output_summary_json: {out_summary}")


if __name__ == "__main__":
    main()

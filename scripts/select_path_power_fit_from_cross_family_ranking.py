#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Select/lock path-power fit JSONs from cross-family ranking summaries."
        )
    )
    p.add_argument(
        "--ranking-summary",
        action="append",
        required=True,
        help="Ranking summary path or label=path (label is optional metadata)",
    )
    p.add_argument("--model", action="append", default=None, choices=["reflection", "scattering"])
    p.add_argument("--output-dir", required=True)
    p.add_argument("--output-summary-json", default=None)
    return p.parse_args()


def _load_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json must be object: {path}")
    return payload


def _parse_ref(value: str) -> Tuple[str, str]:
    raw = str(value).strip()
    if raw == "":
        raise ValueError("ranking-summary entry must be non-empty")
    if "=" in raw:
        label, path = raw.split("=", 1)
        return str(label).strip(), str(path).strip()
    return "", raw


def _write_selected_fit(
    fit_payload: Mapping[str, Any],
    out_path: Path,
    ranking_summary_json: str,
    label: str,
    best_row: Mapping[str, Any],
    model: str,
) -> None:
    payload = dict(fit_payload)
    selection = {
        "source_cross_family_ranking_json": str(ranking_summary_json),
        "source_label": str(label),
        "selection_strategy": "cross_family_ranking_best_score",
        "model": str(model),
        "best_row": {
            "fit_json": str(best_row.get("fit_json", "")),
            "score": float(best_row.get("score", 0.0)),
            "b_tuned_pass": bool(best_row.get("b_tuned_pass", False)),
            "ra_mean_delta": float(best_row.get("ra_mean_delta", 0.0)),
            "rd_mean_delta": float(best_row.get("rd_mean_delta", 0.0)),
            "candidate_index": int(best_row.get("candidate_index", -1)),
        },
    }
    payload["selection"] = selection
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    allowed_models = None if args.model is None else set(str(m) for m in args.model)

    selections: List[Dict[str, Any]] = []
    seen_models = set()

    for raw_ref in args.ranking_summary:
        label, ranking_path = _parse_ref(raw_ref)
        ranking_payload = _load_json(ranking_path)

        model = str(ranking_payload.get("model", "")).strip().lower()
        if model not in {"reflection", "scattering"}:
            raise ValueError(f"ranking summary missing valid model: {ranking_path}")
        if allowed_models is not None and model not in allowed_models:
            continue
        if model in seen_models:
            raise ValueError(f"duplicate model ranking provided: {model}")

        best = ranking_payload.get("best", None)
        if not isinstance(best, Mapping):
            raise ValueError(f"ranking summary has no best row: {ranking_path}")
        if str(best.get("status", "")).strip().lower() != "ok":
            raise ValueError(f"ranking best row is not ok: {ranking_path}")

        fit_json = str(best.get("fit_json", "")).strip()
        if fit_json == "":
            raise ValueError(f"ranking best row missing fit_json: {ranking_path}")

        fit_payload = _load_json(fit_json)
        fit_obj = fit_payload.get("fit", None)
        if not isinstance(fit_obj, Mapping):
            raise ValueError(f"selected fit payload missing fit object: {fit_json}")
        fit_model = str(fit_obj.get("model", "")).strip().lower()
        if fit_model != model:
            raise ValueError(
                f"fit model mismatch for {fit_json}: fit.model={fit_model}, ranking.model={model}"
            )

        out_fit = out_dir / f"path_power_fit_{model}_selected.json"
        _write_selected_fit(
            fit_payload=fit_payload,
            out_path=out_fit,
            ranking_summary_json=ranking_path,
            label=label,
            best_row=best,
            model=model,
        )
        seen_models.add(model)

        selections.append(
            {
                "model": str(model),
                "ranking_summary_json": str(ranking_path),
                "source_label": str(label),
                "candidate_count": int(ranking_payload.get("candidate_count", 0)),
                "ok_count": int(ranking_payload.get("ok_count", 0)),
                "selected": {
                    "source_fit_json": str(fit_json),
                    "output_fit_json": str(out_fit),
                    "score": float(best.get("score", 0.0)),
                    "b_tuned_pass": bool(best.get("b_tuned_pass", False)),
                    "ra_mean_delta": float(best.get("ra_mean_delta", 0.0)),
                    "rd_mean_delta": float(best.get("rd_mean_delta", 0.0)),
                },
            }
        )

    if len(selections) == 0:
        raise ValueError("no selections were emitted")

    summary = {
        "version": 1,
        "selection_strategy": "cross_family_ranking_best_score",
        "output_dir": str(out_dir),
        "models": selections,
    }

    out_summary = (
        out_dir / "path_power_fit_selection_cross_family_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    models = [str(x["model"]) for x in selections]
    print("Cross-family ranking fit selection completed.")
    print(f"  models: {','.join(models)}")
    print(f"  output_dir: {out_dir}")
    print(f"  output_summary_json: {out_summary}")


if __name__ == "__main__":
    main()

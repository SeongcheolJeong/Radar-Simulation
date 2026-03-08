#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple


def _http_json(method: str, url: str, payload: Optional[Mapping[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
    with urllib.request.urlopen(req, timeout=300.0) as resp:
        text = resp.read().decode("utf-8")
        return int(resp.status), json.loads(text)


def _resolve_output_json(raw: str, repo_root: Path) -> Path:
    out = Path(raw).expanduser()
    if not out.is_absolute():
        out = (repo_root / out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def _resolve_scene_json(raw: str, repo_root: Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"scene json not found: {path}")
    return path


def _build_sionna_scene_overrides() -> Dict[str, Any]:
    return {
        "backend": {
            "type": "sionna_rt",
            "runtime_provider": "avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba",
            "runtime_required_modules": ["mitsuba", "drjit"],
            "runtime_failure_policy": "error",
            "runtime_input": {
                "simulation_mode": "auto",
                "multiplexing_mode": "tdm",
                "device": "gpu",
                "license_tier_hint": "trial",
                "ego_origin_m": [0.0, 0.0, 0.0],
                "chirp_interval_s": 4.0e-5,
                "min_range_m": 0.5,
                "spheres": [
                    {
                        "center_m": [0.0, 8.0, 0.0],
                        "radius_m": 0.35,
                        "amplitude": 1.0,
                        "radial_velocity_mps": 0.0,
                        "path_id_prefix": "sphere_center",
                        "material_tag": "vehicle_body",
                    },
                    {
                        "center_m": [-1.5, 14.0, 0.0],
                        "radius_m": 0.45,
                        "amplitude": 0.85,
                        "radial_velocity_mps": -2.0,
                        "path_id_prefix": "sphere_left",
                        "material_tag": "guardrail",
                    },
                    {
                        "center_m": [1.75, 18.0, 0.0],
                        "radius_m": 0.4,
                        "amplitude": 0.65,
                        "radial_velocity_mps": 1.2,
                        "path_id_prefix": "sphere_right",
                        "material_tag": "road_surface",
                    },
                ],
            },
        }
    }


def _build_po_sbr_scene_overrides() -> Dict[str, Any]:
    return {
        "backend": {
            "type": "po_sbr_rt",
            "runtime_provider": "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr",
            "runtime_required_modules": ["rtxpy", "igl"],
            "runtime_failure_policy": "error",
            "runtime_input": {
                "simulation_mode": "auto",
                "multiplexing_mode": "tdm",
                "device": "gpu",
                "license_tier_hint": "trial",
                "po_sbr_repo_root": "external/PO-SBR-Python",
                "geometry_path": "geometries/plate.obj",
                "chirp_interval_s": 4.0e-5,
                "bounces": 2,
                "rays_per_lambda": 3.0,
                "alpha_deg": 180.0,
                "phi_deg": 90.0,
                "theta_deg": 90.0,
                "radial_velocity_mps": 0.0,
                "min_range_m": 0.5,
                "material_tag": "po_sbr_runtime",
                "path_id_prefix": "po_sbr_runtime",
                "components": [
                    {
                        "phi_deg": 78.0,
                        "theta_deg": 90.0,
                        "radial_velocity_mps": -2.0,
                        "path_id_prefix": "po_lane_left",
                        "material_tag": "guardrail",
                    },
                    {
                        "phi_deg": 102.0,
                        "theta_deg": 90.0,
                        "radial_velocity_mps": 1.5,
                        "path_id_prefix": "po_lane_right",
                        "material_tag": "vehicle_body",
                    },
                ],
            },
        }
    }


def _fetch_template_graph(api_base: str, template_id: str) -> Dict[str, Any]:
    status, payload = _http_json("GET", f"{api_base}/api/graph/templates")
    if status != 200:
        raise RuntimeError(f"failed to fetch templates: http {status}")
    for row in payload.get("templates", []):
        if str(row.get("template_id", "")).strip() == template_id:
            graph = row.get("graph")
            if isinstance(graph, Mapping):
                return dict(graph)
    raise ValueError(f"template not found: {template_id}")


def _build_graph_run_payload(graph: Mapping[str, Any], scene_json: Path, profile: str, scene_overrides: Mapping[str, Any], tag: str) -> Dict[str, Any]:
    return {
        "graph": dict(graph),
        "scene_json_path": str(scene_json),
        "profile": profile,
        "run_hybrid_estimation": False,
        "tag": tag,
        "cache": {"enable": False, "mode": "off"},
        "scene_overrides": dict(scene_overrides),
    }


def _sync_graph_run(api_base: str, payload: Mapping[str, Any], interactive_budget_s: float) -> Dict[str, Any]:
    t0 = time.perf_counter()
    status, created = _http_json("POST", f"{api_base}/api/graph/runs?async=0", payload=payload)
    elapsed_s = float(time.perf_counter() - t0)
    if status != 200 or bool(created.get("ok")) is not True:
        raise RuntimeError(f"sync graph run failed: http={status}")
    row = created["graph_run"]
    run_id = str(row["graph_run_id"])
    summary_status, summary = _http_json("GET", f"{api_base}/api/graph/runs/{urllib.parse.quote(run_id)}/summary")
    if summary_status != 200:
        raise RuntimeError(f"summary fetch failed for {run_id}: http={summary_status}")
    outputs = summary.get("outputs") or {}
    quicklook = summary.get("quicklook") or {}
    return {
        "mode": "sync",
        "graph_run_id": run_id,
        "http_status": status,
        "status": str(row.get("status", "")),
        "elapsed_wall_s": round(elapsed_s, 3),
        "interactive_budget_s": interactive_budget_s,
        "interactive_ready": bool(str(row.get("status", "")) == "completed" and elapsed_s <= interactive_budget_s),
        "summary_json": str(outputs.get("graph_run_summary_json", "")),
        "path_list_json": str(outputs.get("path_list_json", "")),
        "adc_cube_npz": str(outputs.get("adc_cube_npz", "")),
        "radar_map_npz": str(outputs.get("radar_map_npz", "")),
        "lgit_customized_output_npz": str(outputs.get("lgit_customized_output_npz", "")),
        "path_count_total": quicklook.get("path_count_total"),
        "adc_shape": quicklook.get("adc_shape"),
        "rd_shape": quicklook.get("rd_shape"),
        "ra_shape": quicklook.get("ra_shape"),
    }


def _async_bounded_graph_run(api_base: str, payload: Mapping[str, Any], wait_budget_s: float, interactive_budget_s: float) -> Dict[str, Any]:
    t0 = time.perf_counter()
    status, created = _http_json("POST", f"{api_base}/api/graph/runs?async=1", payload=payload)
    if status != 202 or bool(created.get("ok")) is not True:
        raise RuntimeError(f"async graph run failed to start: http={status}")
    row = created["graph_run"]
    run_id = str(row["graph_run_id"])
    terminal = None
    timed_out = False
    while True:
        if (time.perf_counter() - t0) >= wait_budget_s:
            timed_out = True
            break
        try:
            poll_status, row = _http_json("GET", f"{api_base}/api/graph/runs/{urllib.parse.quote(run_id)}")
        except urllib.error.HTTPError as exc:
            if exc.code in {400, 404}:
                time.sleep(0.1)
                continue
            raise
        if poll_status != 200:
            raise RuntimeError(f"poll failed for {run_id}: http={poll_status}")
        terminal = str(row.get("status", "")).strip().lower()
        if terminal in {"completed", "failed", "canceled", "cancel_requested"}:
            break
        time.sleep(0.25)

    cancel_status = None
    if timed_out:
        cancel_http_status, cancel_resp = _http_json(
            "POST",
            f"{api_base}/api/graph/runs/{urllib.parse.quote(run_id)}/cancel",
            payload={"reason": "graph_lab_high_fidelity_runtime_timing_timeout"},
        )
        cancel_status = cancel_http_status
        row = cancel_resp.get("graph_run") or row
        for _ in range(200):
            try:
                poll_status, row = _http_json("GET", f"{api_base}/api/graph/runs/{urllib.parse.quote(run_id)}")
            except urllib.error.HTTPError as exc:
                if exc.code in {400, 404}:
                    time.sleep(0.1)
                    continue
                raise
            if poll_status != 200:
                raise RuntimeError(f"poll after cancel failed for {run_id}: http={poll_status}")
            terminal = str(row.get("status", "")).strip().lower()
            if terminal in {"completed", "failed", "canceled", "cancel_requested"}:
                break
            time.sleep(0.1)

    elapsed_s = float(time.perf_counter() - t0)
    result: Dict[str, Any] = {
        "mode": "async_timeout_bounded",
        "graph_run_id": run_id,
        "http_status": status,
        "status": str(row.get("status", "")),
        "elapsed_wall_s": round(elapsed_s, 3),
        "interactive_budget_s": interactive_budget_s,
        "wait_budget_s": wait_budget_s,
        "interactive_ready": bool(str(row.get("status", "")) == "completed" and elapsed_s <= interactive_budget_s),
        "timed_out": timed_out,
        "cancel_http_status": cancel_status,
    }
    recovery = row.get("recovery") or {}
    control = row.get("control") or {}
    if recovery:
        result["recoverable"] = bool(recovery.get("recoverable", False))
        result["retry_endpoint"] = recovery.get("retry_endpoint")
    if control:
        result["cancel_requested"] = bool(control.get("cancel_requested", False))
        result["cancel_reason"] = control.get("cancel_reason")
    failure = row.get("failure") or {}
    if failure:
        result["failure_type"] = failure.get("type")
        result["failure_message"] = failure.get("message")
    error_text = row.get("error")
    if error_text:
        result["error"] = str(error_text)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure Graph Lab high-fidelity runtime timing through the frontend/API contract.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8101", help="Graph Lab API base URL")
    parser.add_argument("--template-id", default="radar_minimal_v1", help="Graph template id to execute")
    parser.add_argument(
        "--scene-json",
        default="data/demo/frontend_quickstart_v1/scene_frontend_quickstart.json",
        help="Scene JSON path used for the timing run",
    )
    parser.add_argument("--profile", default="fast_debug", help="Graph profile")
    parser.add_argument("--interactive-budget-s", type=float, default=10.0, help="Budget for interactive-ready judgment")
    parser.add_argument("--po-sbr-wait-budget-s", type=float, default=30.0, help="Max wait before canceling PO-SBR async run")
    parser.add_argument(
        "--output-json",
        default="docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json",
        help="Output JSON report path",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    out_json = _resolve_output_json(args.output_json, repo_root=repo_root)
    scene_json = _resolve_scene_json(args.scene_json, repo_root=repo_root)
    graph = _fetch_template_graph(api_base=args.api_base.rstrip("/"), template_id=str(args.template_id))

    sionna_payload = _build_graph_run_payload(
        graph=graph,
        scene_json=scene_json,
        profile=str(args.profile),
        scene_overrides=_build_sionna_scene_overrides(),
        tag="graph_lab_high_fidelity_sionna_timing",
    )
    po_sbr_payload = _build_graph_run_payload(
        graph=graph,
        scene_json=scene_json,
        profile=str(args.profile),
        scene_overrides=_build_po_sbr_scene_overrides(),
        tag="graph_lab_high_fidelity_po_sbr_timing",
    )

    health_status, health = _http_json("GET", f"{args.api_base.rstrip('/')}/health")
    if health_status != 200 or bool(health.get("ok")) is not True:
        raise RuntimeError(f"api health failed: http={health_status}")

    sionna = _sync_graph_run(
        api_base=args.api_base.rstrip("/"),
        payload=sionna_payload,
        interactive_budget_s=float(args.interactive_budget_s),
    )
    po_sbr = _async_bounded_graph_run(
        api_base=args.api_base.rstrip("/"),
        payload=po_sbr_payload,
        wait_budget_s=float(args.po_sbr_wait_budget_s),
        interactive_budget_s=float(args.interactive_budget_s),
    )

    report = {
        "version": "graph_lab_high_fidelity_runtime_timing_v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "api_base": str(args.api_base).rstrip("/"),
        "template_id": str(args.template_id),
        "scene_json_path": str(scene_json),
        "profile": str(args.profile),
        "interactive_budget_s": float(args.interactive_budget_s),
        "po_sbr_wait_budget_s": float(args.po_sbr_wait_budget_s),
        "measures_api_triggered_graph_runs": True,
        "browser_click_latency_included": False,
        "api_health": health,
        "cases": {
            "high_fidelity_sionna_rt": sionna,
            "high_fidelity_po_sbr_rt": po_sbr,
        },
        "summary": {
            "recommended_interactive_high_fidelity_path": "sionna_rt" if sionna.get("interactive_ready") else "none",
            "sionna_completed": bool(sionna.get("status") == "completed"),
            "po_sbr_completed": bool(po_sbr.get("status") == "completed"),
            "po_sbr_interactive_ready": bool(po_sbr.get("interactive_ready")),
            "po_sbr_note": "PO-SBR remains a dedicated-env, longer-running validation path unless this report flips to completed within budget.",
        },
    }
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")
    print(
        "graph_lab_high_fidelity_runtime_timing: "
        f"sionna={sionna['status']}@{sionna['elapsed_wall_s']}s "
        f"po_sbr={po_sbr['status']}@{po_sbr['elapsed_wall_s']}s"
    )


if __name__ == "__main__":
    main()

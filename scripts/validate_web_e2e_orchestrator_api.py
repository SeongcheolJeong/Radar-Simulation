#!/usr/bin/env python3
import csv
import json
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from avxsim.web_e2e_api import WebE2EOrchestrator, create_web_e2e_http_server


def _http_json(
    method: str,
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = 60.0,
):
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url=url, data=body, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        data = json.loads(raw) if raw else {}
        return resp.status, data


def _build_min_scene(path: Path) -> None:
    payload = {
        "scene_id": "web_e2e_validate_scene_v1",
        "backend": {
            "type": "analytic_targets",
            "n_chirps": 4,
            "chirp_interval_s": 4.0e-5,
            "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
            "rx_pos_m": [[0.0, 0.00185, 0.0], [0.0, 0.0037, 0.0]],
            "targets": [
                {
                    "path_id": "validate_static",
                    "range_m": 20.0,
                    "radial_velocity_mps": 0.0,
                    "az_deg": 5.0,
                    "amp": 1.0,
                },
                {
                    "path_id": "validate_moving",
                    "range_m": 30.0,
                    "radial_velocity_mps": -4.0,
                    "az_deg": -7.0,
                    "amp": {"re": 0.8, "im": 0.1},
                },
            ],
            "noise_sigma": 0.0,
        },
        "radar": {
            "fc_hz": 77e9,
            "slope_hz_per_s": 20e12,
            "fs_hz": 20e6,
            "samples_per_chirp": 256,
        },
        "map_config": {
            "nfft_range": 256,
            "nfft_doppler": 16,
            "nfft_angle": 8,
            "range_bin_limit": 64,
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_shifted_scene(path: Path) -> None:
    payload = {
        "scene_id": "web_e2e_validate_scene_shifted_v1",
        "backend": {
            "type": "analytic_targets",
            "n_chirps": 4,
            "chirp_interval_s": 4.0e-5,
            "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
            "rx_pos_m": [[0.0, 0.00185, 0.0], [0.0, 0.0037, 0.0]],
            "targets": [
                {
                    "path_id": "validate_far_static",
                    "range_m": 55.0,
                    "radial_velocity_mps": 0.0,
                    "az_deg": 18.0,
                    "amp": 1.2,
                },
                {
                    "path_id": "validate_far_moving",
                    "range_m": 70.0,
                    "radial_velocity_mps": 10.0,
                    "az_deg": -16.0,
                    "amp": {"re": 0.5, "im": -0.2},
                },
            ],
            "noise_sigma": 0.0,
        },
        "radar": {
            "fc_hz": 77e9,
            "slope_hz_per_s": 20e12,
            "fs_hz": 20e6,
            "samples_per_chirp": 256,
        },
        "map_config": {
            "nfft_range": 256,
            "nfft_doppler": 16,
            "nfft_angle": 8,
            "range_bin_limit": 64,
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_invalid_scene(path: Path) -> None:
    payload = {
        "scene_id": "web_e2e_validate_invalid_scene_v1",
        "backend": {
            "type": "invalid_backend_type_for_recovery_test",
            "n_chirps": 4,
            "chirp_interval_s": 4.0e-5,
            "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
            "rx_pos_m": [[0.0, 0.00185, 0.0], [0.0, 0.0037, 0.0]],
            "targets": [
                {
                    "path_id": "invalid_case_target",
                    "range_m": 20.0,
                    "radial_velocity_mps": 0.0,
                    "az_deg": 5.0,
                    "amp": 1.0,
                }
            ],
            "noise_sigma": 0.0,
        },
        "radar": {
            "fc_hz": 77e9,
            "slope_hz_per_s": 20e12,
            "fs_hz": 20e6,
            "samples_per_chirp": 256,
        },
        "map_config": {
            "nfft_range": 256,
            "nfft_doppler": 16,
            "nfft_angle": 8,
            "range_bin_limit": 64,
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="validate_web_e2e_api_") as td:
        root = Path(td)
        scene_json = root / "scene.json"
        scene_json_shifted = root / "scene_shifted.json"
        scene_json_invalid = root / "scene_invalid.json"
        _build_min_scene(scene_json)
        _build_shifted_scene(scene_json_shifted)
        _build_invalid_scene(scene_json_invalid)

        store_root = root / "store"
        orchestrator = WebE2EOrchestrator(repo_root=str(repo_root), store_root=str(store_root))
        server = create_web_e2e_http_server(host="127.0.0.1", port=0, orchestrator=orchestrator)
        host, port = server.server_address[0], int(server.server_address[1])

        th = threading.Thread(target=server.serve_forever, daemon=True)
        th.start()

        try:
            base = f"http://{host}:{port}"

            status, health = _http_json("GET", f"{base}/health")
            assert status == 200
            assert health["ok"] is True
            assert "run_count" in health
            assert "comparison_count" in health
            assert "baseline_count" in health
            assert "policy_eval_count" in health
            assert "regression_session_count" in health
            assert "regression_export_count" in health
            assert "graph_template_count" in health
            assert "graph_run_count" in health

            status, prof = _http_json("GET", f"{base}/api/profiles")
            assert status == 200
            assert "fast_debug" in prof["profiles"]

            status, template_resp = _http_json("GET", f"{base}/api/graph/templates")
            assert status == 200
            templates = template_resp.get("templates")
            assert isinstance(templates, list)
            assert len(templates) >= 1
            first_template = templates[0]
            assert isinstance(first_template, dict)
            assert isinstance(first_template.get("graph"), dict)

            status, graph_ok = _http_json(
                "POST",
                f"{base}/api/graph/validate",
                payload=first_template["graph"],
            )
            assert status == 200
            assert graph_ok["ok"] is True
            gv = graph_ok["graph_validation"]
            assert gv["version"] == "web_e2e_graph_validation_v1"
            assert gv["valid"] is True
            assert gv["stats"]["node_count"] >= 1
            assert len(gv["normalized"]["topological_order"]) == gv["stats"]["node_count"]

            invalid_cycle_graph = {
                "version": "web_e2e_graph_schema_v1",
                "graph_id": "invalid_cycle",
                "profile": "fast_debug",
                "nodes": [
                    {"id": "a", "type": "SceneSource", "params": {}},
                    {"id": "b", "type": "RadarMap", "params": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "a", "target": "b", "contract": "x"},
                    {"id": "e2", "source": "b", "target": "a", "contract": "y"},
                ],
            }
            status, graph_bad = _http_json(
                "POST",
                f"{base}/api/graph/validate",
                payload=invalid_cycle_graph,
            )
            assert status == 200
            assert graph_bad["ok"] is False
            bad_errors = [str(x) for x in graph_bad["graph_validation"]["errors"]]
            assert any("cycle" in x for x in bad_errors)

            graph_run_payload = {
                "graph": first_template["graph"],
                "scene_json_path": str(scene_json),
                "profile": "fast_debug",
                "run_hybrid_estimation": False,
                "tag": "validate_graph_run",
            }
            status, graph_run_created = _http_json(
                "POST",
                f"{base}/api/graph/runs?async=0",
                payload=graph_run_payload,
            )
            assert status == 200
            assert graph_run_created["ok"] is True
            graph_run = graph_run_created["graph_run"]
            assert graph_run["version"] == "web_e2e_graph_run_record_v1"
            assert graph_run["status"] == "completed"
            graph_run_id = str(graph_run["graph_run_id"])
            assert graph_run["graph_meta"]["node_count"] >= 1

            status, graph_run_list = _http_json("GET", f"{base}/api/graph/runs")
            assert status == 200
            assert any(
                str(x.get("graph_run_id")) == graph_run_id
                for x in graph_run_list["graph_runs"]
            )

            status, graph_run_row = _http_json(
                "GET",
                f"{base}/api/graph/runs/{urllib.parse.quote(graph_run_id)}",
            )
            assert status == 200
            assert str(graph_run_row["graph_run_id"]) == graph_run_id
            assert graph_run_row["status"] == "completed"

            status, graph_run_summary = _http_json(
                "GET",
                f"{base}/api/graph/runs/{urllib.parse.quote(graph_run_id)}/summary",
            )
            assert status == 200
            assert graph_run_summary["version"] == "web_e2e_graph_run_summary_v1"
            assert graph_run_summary["status"] == "completed"
            assert graph_run_summary["graph"]["node_count"] >= 1
            assert len(graph_run_summary["execution"]["node_results"]) >= 1
            assert Path(str(graph_run_summary["outputs"]["path_list_json"])).exists()
            assert Path(str(graph_run_summary["outputs"]["adc_cube_npz"])).exists()
            assert Path(str(graph_run_summary["outputs"]["radar_map_npz"])).exists()
            graph_run_summary_json = str(graph_run_summary["outputs"]["graph_run_summary_json"])
            assert Path(graph_run_summary_json).exists()
            assert graph_run_summary["execution"]["cache"]["hit"] is False

            graph_nodes = first_template["graph"].get("nodes", [])
            map_node_id = None
            if isinstance(graph_nodes, list):
                for node in graph_nodes:
                    if isinstance(node, dict) and str(node.get("type", "")) == "RadarMap":
                        map_node_id = str(node.get("id", "")).strip() or None
                        break
            assert map_node_id is not None

            # M16.5 full-cache hit path.
            status, graph_run_cached_created = _http_json(
                "POST",
                f"{base}/api/graph/runs?async=0",
                payload={
                    **graph_run_payload,
                    "tag": "validate_graph_run_cache_full",
                    "cache": {"enable": True, "mode": "required"},
                },
            )
            assert status == 200
            assert graph_run_cached_created["ok"] is True
            graph_run_cached = graph_run_cached_created["graph_run"]
            assert graph_run_cached["status"] == "completed"
            assert graph_run_cached["cache"]["hit"] is True
            assert graph_run_cached["cache"]["hit_scope"] == "full"
            graph_run_cached_id = str(graph_run_cached["graph_run_id"])
            assert str(graph_run_cached["cache"]["source_graph_run_id"]) == graph_run_id

            status, graph_run_cached_summary = _http_json(
                "GET",
                f"{base}/api/graph/runs/{urllib.parse.quote(graph_run_cached_id)}/summary",
            )
            assert status == 200
            assert graph_run_cached_summary["execution"]["cache"]["hit"] is True
            assert graph_run_cached_summary["execution"]["cache"]["hit_scope"] == "full"
            assert graph_run_cached_summary["execution"]["bridge_mode"] == "scene_pipeline_cache_full_reuse_v1"

            # M16.5 partial rerun from RadarMap node using cached upstream artifacts.
            status, graph_run_partial_created = _http_json(
                "POST",
                f"{base}/api/graph/runs?async=0",
                payload={
                    **graph_run_payload,
                    "tag": "validate_graph_run_cache_partial_map",
                    "rerun_from_node_id": map_node_id,
                    "cache": {
                        "enable": True,
                        "mode": "required",
                        "reuse_graph_run_id": graph_run_id,
                    },
                },
            )
            assert status == 200
            assert graph_run_partial_created["ok"] is True
            graph_run_partial = graph_run_partial_created["graph_run"]
            assert graph_run_partial["status"] == "completed"
            assert graph_run_partial["cache"]["hit"] is True
            assert graph_run_partial["cache"]["hit_scope"] == "partial"
            graph_run_partial_id = str(graph_run_partial["graph_run_id"])

            status, graph_run_partial_summary = _http_json(
                "GET",
                f"{base}/api/graph/runs/{urllib.parse.quote(graph_run_partial_id)}/summary",
            )
            assert status == 200
            assert graph_run_partial_summary["execution"]["cache"]["hit"] is True
            assert graph_run_partial_summary["execution"]["cache"]["hit_scope"] == "partial"
            assert (
                graph_run_partial_summary["execution"]["bridge_mode"]
                == "scene_pipeline_partial_rerun_radar_map_v1"
            )
            assert any(
                str(row.get("status")) == "cached"
                for row in graph_run_partial_summary["execution"]["node_results"]
            )

            # M16.5 cancel handling on async run.
            status, graph_run_async_created = _http_json(
                "POST",
                f"{base}/api/graph/runs?async=1",
                payload={
                    **graph_run_payload,
                    "tag": "validate_graph_run_cancel",
                    "cache": {"enable": False, "mode": "off"},
                    "execution_options": {"debug_delay_s": 0.6},
                },
            )
            assert status == 202
            assert graph_run_async_created["ok"] is True
            graph_run_async_id = str(graph_run_async_created["graph_run"]["graph_run_id"])

            status, graph_run_cancel_resp = _http_json(
                "POST",
                f"{base}/api/graph/runs/{urllib.parse.quote(graph_run_async_id)}/cancel",
                payload={"reason": "validator_cancel"},
            )
            assert status == 200
            assert graph_run_cancel_resp["ok"] is True

            async_row = graph_run_cancel_resp["graph_run"]
            last_poll_http_err: Optional[urllib.error.HTTPError] = None
            for _ in range(40):
                try:
                    status, async_row = _http_json(
                        "GET",
                        f"{base}/api/graph/runs/{urllib.parse.quote(graph_run_async_id)}",
                    )
                except urllib.error.HTTPError as exc:
                    # Graph record writes are not atomic; a transient read during write can surface
                    # as 400 (JSON decode) or 404 (not-yet-visible file). Treat as poll retry.
                    if exc.code in {400, 404}:
                        last_poll_http_err = exc
                        time.sleep(0.05)
                        continue
                    raise
                assert status == 200
                last_poll_http_err = None
                if str(async_row.get("status", "")).strip().lower() in {
                    "canceled",
                    "failed",
                    "completed",
                }:
                    break
                time.sleep(0.05)
            if last_poll_http_err is not None:
                raise AssertionError(
                    f"graph run poll did not stabilize after cancel: http {last_poll_http_err.code}"
                )
            terminal_status = str(async_row.get("status", "")).strip().lower()
            assert terminal_status in {"canceled", "completed"}
            assert bool((async_row.get("recovery") or {}).get("recoverable", False)) is True

            # M16.5 retry handling from cancel flow (canceled or completed race).
            status, graph_retry_from_cancel_resp = _http_json(
                "POST",
                f"{base}/api/graph/runs/{urllib.parse.quote(graph_run_async_id)}/retry?async=0",
                payload={
                    "cache": {"enable": False, "mode": "off"},
                    "tag": "validate_retry_from_canceled",
                },
            )
            assert status == 200
            assert graph_retry_from_cancel_resp["ok"] is True
            graph_retry_from_cancel = graph_retry_from_cancel_resp["graph_run"]
            assert graph_retry_from_cancel["status"] == "completed"
            assert (
                str(graph_retry_from_cancel["request"]["retry_of_graph_run_id"])
                == graph_run_async_id
            )

            # M16.5 failure surfacing + recovery guidance.
            status, graph_run_fail_created = _http_json(
                "POST",
                f"{base}/api/graph/runs?async=0",
                payload={
                    **graph_run_payload,
                    "scene_json_path": str(scene_json_invalid),
                    "tag": "validate_graph_run_failure",
                    "cache": {"enable": False, "mode": "off"},
                },
            )
            assert status == 200
            assert graph_run_fail_created["ok"] is True
            graph_run_failed = graph_run_fail_created["graph_run"]
            assert graph_run_failed["status"] == "failed"
            assert "ValueError" in str(graph_run_failed.get("error", ""))
            failed_recovery = graph_run_failed.get("recovery", {})
            assert bool(failed_recovery.get("recoverable", False)) is True
            assert isinstance(failed_recovery.get("hints"), list)
            assert len(failed_recovery.get("hints", [])) >= 1
            graph_run_failed_id = str(graph_run_failed["graph_run_id"])

            status, graph_retry_from_failed_resp = _http_json(
                "POST",
                f"{base}/api/graph/runs/{urllib.parse.quote(graph_run_failed_id)}/retry?async=0",
                payload={
                    "scene_json_path": str(scene_json),
                    "cache": {"enable": False, "mode": "off"},
                    "tag": "validate_retry_from_failed",
                },
            )
            assert status == 200
            assert graph_retry_from_failed_resp["ok"] is True
            graph_retry_from_failed = graph_retry_from_failed_resp["graph_run"]
            assert graph_retry_from_failed["status"] == "completed"
            assert (
                str(graph_retry_from_failed["request"]["retry_of_graph_run_id"])
                == graph_run_failed_id
            )

            status, graph_baseline_created = _http_json(
                "POST",
                f"{base}/api/baselines",
                payload={
                    "baseline_id": "validate_graph_baseline",
                    "summary_json": graph_run_summary_json,
                    "overwrite": True,
                    "note": "graph-run baseline",
                },
            )
            assert status == 200
            assert graph_baseline_created["ok"] is True
            assert graph_baseline_created["baseline"]["baseline_id"] == "validate_graph_baseline"

            status, graph_policy_resp = _http_json(
                "POST",
                f"{base}/api/compare/policy",
                payload={
                    "baseline_id": "validate_graph_baseline",
                    "candidate_summary_json": graph_run_summary_json,
                },
            )
            assert status == 200
            assert graph_policy_resp["ok"] is True
            graph_policy_eval = graph_policy_resp["policy_eval"]
            assert graph_policy_eval["baseline"]["baseline_id"] == "validate_graph_baseline"
            assert graph_policy_eval["gate_failed"] is False
            assert graph_policy_eval["recommendation"] == "adopt_candidate"

            post_payload = {
                "scene_json_path": str(scene_json),
                "profile": "fast_debug",
                "run_hybrid_estimation": False,
                "tag": "validate_web_e2e",
            }
            status, created = _http_json("POST", f"{base}/api/runs?async=0", payload=post_payload)
            assert status == 200
            assert created["ok"] is True
            run_id = str(created["run"]["run_id"])
            assert created["run"]["status"] == "completed"

            status, row = _http_json("GET", f"{base}/api/runs/{urllib.parse.quote(run_id)}")
            assert status == 200
            assert row["status"] == "completed"
            assert row["result"] is not None

            status, summary = _http_json(
                "GET", f"{base}/api/runs/{urllib.parse.quote(run_id)}/summary"
            )
            assert status == 200
            assert summary["status"] == "completed"
            assert summary["version"] == "web_e2e_run_summary_v2"
            assert Path(str(summary["scene_json"])).resolve() == scene_json.resolve()
            assert "outputs" in summary
            assert "path_summary" in summary
            assert "adc_summary" in summary
            assert "radar_map_summary" in summary

            out = summary["outputs"]
            assert Path(str(out["path_list_json"])).exists()
            assert Path(str(out["adc_cube_npz"])).exists()
            assert Path(str(out["radar_map_npz"])).exists()
            assert Path(str(out["run_summary_json"])).exists()

            ps = summary["path_summary"]
            assert ps["n_chirps"] == 4
            assert ps["path_count_total"] == 8
            assert ps["path_count_per_chirp"] == [2, 2, 2, 2]
            assert len(ps["first_chirp_paths"]) == 2

            adc_s = summary["adc_summary"]
            assert adc_s["shape"] == [256, 4, 2, 2]
            assert adc_s["metadata"]["samples_per_chirp"] == 256

            rm_s = summary["radar_map_summary"]
            assert rm_s["rd_shape"] == [16, 64]
            assert rm_s["ra_shape"] == [8, 64]
            assert len(rm_s["rd_top_peaks"]) > 0
            assert len(rm_s["ra_top_peaks"]) > 0

            if "visuals" in summary:
                visuals = summary["visuals"]
                assert isinstance(visuals, dict)
                for _, path_value in visuals.items():
                    assert Path(str(path_value)).exists()

            q = summary["quicklook"]
            assert q["n_chirps"] == 4
            assert q["path_count_total"] == 8
            assert q["rd_shape"] == [16, 64]
            assert q["ra_shape"] == [8, 64]

            status, rows = _http_json("GET", f"{base}/api/runs")
            assert status == 200
            assert isinstance(rows["runs"], list)
            assert any(str(x.get("run_id")) == run_id for x in rows["runs"])

            # Compare endpoint smoke: compare two completed runs.
            status, created_2 = _http_json("POST", f"{base}/api/runs?async=0", payload=post_payload)
            assert status == 200
            run_id_2 = str(created_2["run"]["run_id"])
            assert run_id_2 != run_id

            compare_payload = {
                "reference_run_id": run_id,
                "candidate_run_id": run_id_2,
            }
            status, cmp_resp = _http_json("POST", f"{base}/api/compare", payload=compare_payload)
            assert status == 200
            assert cmp_resp["ok"] is True
            cmp_obj = cmp_resp["comparison"]
            assert cmp_obj["version"] == "web_e2e_compare_v1"
            assert cmp_obj["reference"]["run_id"] == run_id
            assert cmp_obj["candidate"]["run_id"] == run_id_2
            assert cmp_obj["parity"]["pass"] is True
            assert cmp_obj["verdict"]["pass"] is True
            cmp_id = str(cmp_obj["comparison_id"])

            status, cmp_list = _http_json("GET", f"{base}/api/comparisons")
            assert status == 200
            assert any(str(x.get("comparison_id")) == cmp_id for x in cmp_list["comparisons"])

            status, cmp_row = _http_json(
                "GET", f"{base}/api/comparisons/{urllib.parse.quote(cmp_id)}"
            )
            assert status == 200
            assert str(cmp_row["comparison_id"]) == cmp_id

            # Baseline pinning + policy verdict.
            baseline_payload = {
                "baseline_id": "validate_baseline",
                "run_id": run_id,
                "note": "baseline for policy validation",
                "tags": ["validate", "web_e2e"],
            }
            status, baseline_created = _http_json(
                "POST", f"{base}/api/baselines", payload=baseline_payload
            )
            assert status == 200
            assert baseline_created["ok"] is True
            baseline = baseline_created["baseline"]
            assert baseline["version"] == "web_e2e_baseline_v1"
            assert baseline["baseline_id"] == "validate_baseline"
            assert baseline["target"]["run_id"] == run_id

            status, baseline_list = _http_json("GET", f"{base}/api/baselines")
            assert status == 200
            assert any(
                str(x.get("baseline_id")) == "validate_baseline"
                for x in baseline_list["baselines"]
            )

            status, baseline_row = _http_json(
                "GET", f"{base}/api/baselines/{urllib.parse.quote('validate_baseline')}"
            )
            assert status == 200
            assert baseline_row["baseline_id"] == "validate_baseline"

            policy_payload = {
                "baseline_id": "validate_baseline",
                "candidate_run_id": run_id_2,
            }
            status, policy_resp = _http_json(
                "POST", f"{base}/api/compare/policy", payload=policy_payload
            )
            assert status == 200
            assert policy_resp["ok"] is True
            policy_eval = policy_resp["policy_eval"]
            assert policy_eval["version"] == "web_e2e_compare_policy_v1"
            assert policy_eval["baseline"]["baseline_id"] == "validate_baseline"
            assert policy_eval["candidate"]["run_id"] == run_id_2
            assert policy_eval["gate_failed"] is False
            assert policy_eval["recommendation"] == "adopt_candidate"
            policy_eval_id = str(policy_eval["policy_eval_id"])

            status, policy_list = _http_json("GET", f"{base}/api/policy-evals")
            assert status == 200
            assert any(
                str(x.get("policy_eval_id")) == policy_eval_id
                for x in policy_list["policy_evals"]
            )

            status, policy_row = _http_json(
                "GET", f"{base}/api/policy-evals/{urllib.parse.quote(policy_eval_id)}"
            )
            assert status == 200
            assert str(policy_row["policy_eval_id"]) == policy_eval_id

            # Build a shifted candidate run to force policy hold.
            post_payload_shifted = {
                "scene_json_path": str(scene_json_shifted),
                "profile": "fast_debug",
                "run_hybrid_estimation": False,
                "tag": "validate_web_e2e_shifted",
            }
            status, created_bad = _http_json(
                "POST", f"{base}/api/runs?async=0", payload=post_payload_shifted
            )
            assert status == 200
            run_id_bad = str(created_bad["run"]["run_id"])

            status, policy_bad_resp = _http_json(
                "POST",
                f"{base}/api/compare/policy",
                payload={
                    "baseline_id": "validate_baseline",
                    "candidate_run_id": run_id_bad,
                },
            )
            assert status == 200
            assert policy_bad_resp["ok"] is True
            policy_bad = policy_bad_resp["policy_eval"]
            assert policy_bad["gate_failed"] is True
            assert policy_bad["recommendation"] == "hold_candidate"

            # Regression session (batch policy verdicts) with stop-on-first-fail.
            session_payload = {
                "session_id": "validate_session",
                "baseline_id": "validate_baseline",
                "candidate_run_ids": [run_id_bad, run_id_2],
                "stop_on_first_fail": True,
                "tag": "validate_batch",
            }
            status, session_resp = _http_json(
                "POST", f"{base}/api/regression-sessions", payload=session_payload
            )
            assert status == 200
            assert session_resp["ok"] is True
            session = session_resp["regression_session"]
            assert session["version"] == "web_e2e_regression_session_v1"
            assert session["session_id"] == "validate_session"
            assert session["requested_candidate_count"] == 2
            assert session["evaluated_candidate_count"] == 1
            assert session["held_count"] == 1
            assert session["adopted_count"] == 0
            assert session["truncated"] is True
            assert session["all_pass"] is False
            assert session["recommendation"] == "stopped_on_first_failure"
            assert len(session["rows"]) == 1
            assert session["rows"][0]["candidate_run_id"] == run_id_bad

            status, sess_list = _http_json("GET", f"{base}/api/regression-sessions")
            assert status == 200
            assert any(
                str(x.get("session_id")) == "validate_session"
                for x in sess_list["regression_sessions"]
            )

            status, sess_row = _http_json(
                "GET", f"{base}/api/regression-sessions/{urllib.parse.quote('validate_session')}"
            )
            assert status == 200
            assert str(sess_row["session_id"]) == "validate_session"

            # Regression artifacts export (CSV + JSON package + summary index).
            export_payload = {
                "session_id": "validate_session",
                "export_id": "validate_export",
                "include_policy_payload": True,
                "tag": "validate_export_tag",
            }
            status, export_resp = _http_json(
                "POST", f"{base}/api/regression-exports", payload=export_payload
            )
            assert status == 200
            assert export_resp["ok"] is True
            export_obj = export_resp["regression_export"]
            assert export_obj["version"] == "web_e2e_regression_export_v1"
            assert export_obj["export_id"] == "validate_export"
            assert export_obj["session_id"] == "validate_session"
            assert export_obj["row_count"] == 1
            assert export_obj["include_policy_payload"] is True
            assert export_obj["tag"] == "validate_export_tag"

            art = export_obj["artifacts"]
            session_json_path = Path(str(art["session_json"]))
            rows_csv_path = Path(str(art["rows_csv"]))
            summary_index_path = Path(str(art["summary_index_json"]))
            package_json_path = Path(str(art["package_json"]))
            assert session_json_path.exists()
            assert rows_csv_path.exists()
            assert summary_index_path.exists()
            assert package_json_path.exists()

            with rows_csv_path.open("r", encoding="utf-8", newline="") as f:
                csv_rows = list(csv.DictReader(f))
            assert len(csv_rows) == 1
            assert csv_rows[0]["candidate_run_id"] == run_id_bad
            assert csv_rows[0]["gate_failed"] in {"True", "true", "1"}

            summary_index = json.loads(summary_index_path.read_text(encoding="utf-8"))
            assert summary_index["version"] == "web_e2e_regression_summary_index_v1"
            assert summary_index["export_id"] == "validate_export"
            assert summary_index["row_count"] == 1
            assert len(summary_index["rows"]) == 1
            assert summary_index["rows"][0]["policy_eval_id"] is not None

            package_payload = json.loads(package_json_path.read_text(encoding="utf-8"))
            assert package_payload["version"] == "web_e2e_regression_package_v1"
            assert package_payload["include_policy_payload"] is True
            assert len(package_payload["rows"]) == 1
            assert "policy_eval" in package_payload["rows"][0]

            status, export_list = _http_json("GET", f"{base}/api/regression-exports")
            assert status == 200
            assert any(
                str(x.get("export_id")) == "validate_export"
                for x in export_list["regression_exports"]
            )

            status, export_row = _http_json(
                "GET", f"{base}/api/regression-exports/{urllib.parse.quote('validate_export')}"
            )
            assert status == 200
            assert str(export_row["export_id"]) == "validate_export"

        finally:
            server.shutdown()
            server.server_close()
            th.join(timeout=3.0)

    print("validate_web_e2e_orchestrator_api: pass")


if __name__ == "__main__":
    run()

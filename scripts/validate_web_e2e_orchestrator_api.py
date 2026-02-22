#!/usr/bin/env python3
import json
import tempfile
import threading
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


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="validate_web_e2e_api_") as td:
        root = Path(td)
        scene_json = root / "scene.json"
        scene_json_shifted = root / "scene_shifted.json"
        _build_min_scene(scene_json)
        _build_shifted_scene(scene_json_shifted)

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

            status, prof = _http_json("GET", f"{base}/api/profiles")
            assert status == 200
            assert "fast_debug" in prof["profiles"]

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

        finally:
            server.shutdown()
            server.server_close()
            th.join(timeout=3.0)

    print("validate_web_e2e_orchestrator_api: pass")


if __name__ == "__main__":
    run()

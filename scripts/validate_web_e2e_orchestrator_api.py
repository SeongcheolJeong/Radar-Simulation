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


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="validate_web_e2e_api_") as td:
        root = Path(td)
        scene_json = root / "scene.json"
        _build_min_scene(scene_json)

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

        finally:
            server.shutdown()
            server.server_close()
            th.join(timeout=3.0)

    print("validate_web_e2e_orchestrator_api: pass")


if __name__ == "__main__":
    run()

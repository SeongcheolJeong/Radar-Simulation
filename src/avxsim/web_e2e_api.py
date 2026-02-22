from __future__ import annotations

import datetime as _dt
import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from urllib.parse import parse_qs, urlparse

import numpy as np

from .scene_pipeline import run_object_scene_to_radar_map_json


PROFILE_PRESETS: Dict[str, Dict[str, Any]] = {
    "fast_debug": {
        "goal": "shortest iteration",
        "backend_hint": "analytic_targets_or_light_sionna",
        "notes": "reduced resolution and simplified physics",
    },
    "balanced_dev": {
        "goal": "daily development",
        "backend_hint": "sionna_rt",
        "notes": "mid resolution with default compensation",
    },
    "fidelity_eval": {
        "goal": "quality gate",
        "backend_hint": "sionna_rt_full_or_po_sbr_rt",
        "notes": "high resolution and strict policy",
    },
}


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat()


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.ndarray,)):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"non-serializable type: {type(value)!r}")


def _top_peaks(matrix: np.ndarray, row_key: str, col_key: str, top_k: int = 6) -> list[dict[str, Any]]:
    arr = np.asarray(matrix, dtype=np.float64)
    if arr.ndim != 2 or arr.size == 0:
        return []

    max_power = float(np.max(arr))
    tiny = float(np.finfo(np.float64).tiny)
    max_power = max(max_power, tiny)

    flat_idx = np.argsort(arr.ravel())[::-1][: int(top_k)]
    out: list[dict[str, Any]] = []
    for idx in flat_idx:
        r, c = np.unravel_index(int(idx), arr.shape)
        power = float(arr[r, c])
        rel_db = 10.0 * np.log10(max(power, tiny) / max_power)
        out.append(
            {
                row_key: int(r),
                col_key: int(c),
                "power": power,
                "rel_db": float(rel_db),
            }
        )
    return out


class WebE2EOrchestrator:
    """Phase-0 web orchestration layer over existing scene pipeline.

    Runs are persisted under:
      <store_root>/runs/<run_id>/
        run_record.json
        run_summary.json
        output/*
    """

    def __init__(self, repo_root: str, store_root: str) -> None:
        self.repo_root = Path(repo_root).expanduser().resolve()
        self.store_root = Path(store_root).expanduser().resolve()
        self.runs_root = self.store_root / "runs"
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def get_profiles(self) -> Dict[str, Dict[str, Any]]:
        return dict(PROFILE_PRESETS)

    def list_runs(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for record_path in sorted(self.runs_root.glob("*/run_record.json")):
            try:
                rows.append(self._load_record_path(record_path))
            except Exception:
                # Keep listing robust even if one run record is corrupted.
                continue
        rows.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return rows

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self._load_record(run_id)

    def submit_run(self, request_payload: Mapping[str, Any], run_async: bool = True) -> dict[str, Any]:
        req = self._normalize_request(request_payload)
        run_id = self._new_run_id()
        run_dir = self.runs_root / run_id
        output_dir = run_dir / str(req["output_subdir"])
        run_summary_json = run_dir / "run_summary.json"
        run_record_json = run_dir / "run_record.json"

        run_dir.mkdir(parents=True, exist_ok=False)

        record: dict[str, Any] = {
            "version": "web_e2e_run_record_v1",
            "run_id": run_id,
            "status": "queued",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "request": req,
            "paths": {
                "run_dir": str(run_dir),
                "output_dir": str(output_dir),
                "run_summary_json": str(run_summary_json),
                "run_record_json": str(run_record_json),
            },
            "result": None,
            "error": None,
        }
        self._save_record(record)

        if run_async:
            th = threading.Thread(target=self._execute_run, args=(run_id,), daemon=True)
            th.start()
        else:
            self._execute_run(run_id)

        return self.get_run(run_id)

    def load_run_summary(self, run_id: str) -> dict[str, Any]:
        record = self.get_run(run_id)
        summary_path = Path(str(record["paths"]["run_summary_json"]))
        if not summary_path.exists() or not summary_path.is_file():
            raise FileNotFoundError(f"run summary not found: {summary_path}")
        return json.loads(summary_path.read_text(encoding="utf-8"))

    def _new_run_id(self) -> str:
        stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:8]
        return f"run_{stamp}_{token}"

    def _normalize_request(self, request_payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(request_payload, Mapping):
            raise ValueError("request payload must be object")

        scene_json_raw = str(request_payload.get("scene_json_path", "")).strip()
        if scene_json_raw == "":
            raise ValueError("scene_json_path is required")

        profile = str(request_payload.get("profile", "balanced_dev")).strip() or "balanced_dev"
        if profile not in PROFILE_PRESETS:
            raise ValueError(
                f"profile must be one of: {', '.join(sorted(PROFILE_PRESETS.keys()))}"
            )

        output_subdir = str(request_payload.get("output_subdir", "output")).strip() or "output"
        out_path = Path(output_subdir)
        if out_path.is_absolute() or any(part == ".." for part in out_path.parts):
            raise ValueError("output_subdir must be a safe relative path")

        scene_json_abs = self._resolve_scene_path(scene_json_raw)

        return {
            "scene_json_path": str(scene_json_abs),
            "scene_json_input": scene_json_raw,
            "profile": profile,
            "run_hybrid_estimation": bool(request_payload.get("run_hybrid_estimation", False)),
            "output_subdir": output_subdir,
            "tag": str(request_payload.get("tag", "")).strip() or None,
            "requested_at": _now_iso(),
        }

    def _resolve_scene_path(self, path_text: str) -> Path:
        path = Path(path_text).expanduser()
        if not path.is_absolute():
            path = (self.repo_root / path).resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"scene json not found: {path}")
        return path

    def _execute_run(self, run_id: str) -> None:
        self._mutate_record(
            run_id,
            lambda rec: rec.update(
                {
                    "status": "running",
                    "updated_at": _now_iso(),
                    "error": None,
                }
            ),
        )

        try:
            record = self.get_run(run_id)
            req = dict(record["request"])
            out_dir = Path(str(record["paths"]["output_dir"]))
            out_dir.mkdir(parents=True, exist_ok=True)

            run_out = run_object_scene_to_radar_map_json(
                scene_json_path=str(req["scene_json_path"]),
                output_dir=str(out_dir),
                run_hybrid_estimation=bool(req.get("run_hybrid_estimation", False)),
            )

            quicklook = self._build_quicklook(out_dir)
            run_summary = {
                "version": "web_e2e_run_summary_v1",
                "run_id": run_id,
                "status": "completed",
                "profile": str(req.get("profile", "balanced_dev")),
                "created_at": str(record.get("created_at")),
                "completed_at": _now_iso(),
                "request": req,
                "artifacts": {
                    "path_list_json": str(run_out["path_list_json"]),
                    "adc_cube_npz": str(run_out["adc_cube_npz"]),
                    "radar_map_npz": str(run_out["radar_map_npz"]),
                    "hybrid_estimation_npz": run_out.get("hybrid_estimation_npz"),
                    "run_summary_json": str(record["paths"]["run_summary_json"]),
                },
                "quicklook": quicklook,
            }

            summary_path = Path(str(record["paths"]["run_summary_json"]))
            summary_path.write_text(json.dumps(run_summary, indent=2, default=_json_default), encoding="utf-8")

            def _ok(rec: dict[str, Any]) -> None:
                rec["status"] = "completed"
                rec["updated_at"] = _now_iso()
                rec["result"] = {
                    "frame_count": int(run_out.get("frame_count", 0)),
                    "tx_schedule_len": len(run_out.get("tx_schedule", [])),
                    "quicklook": quicklook,
                    "run_summary_json": str(summary_path),
                }
                rec["error"] = None

            self._mutate_record(run_id, _ok)

        except Exception as exc:
            def _fail(rec: dict[str, Any]) -> None:
                rec["status"] = "failed"
                rec["updated_at"] = _now_iso()
                rec["error"] = f"{type(exc).__name__}: {exc}"

            self._mutate_record(run_id, _fail)

    def _build_quicklook(self, output_dir: Path) -> dict[str, Any]:
        path_json = output_dir / "path_list.json"
        adc_npz = output_dir / "adc_cube.npz"
        map_npz = output_dir / "radar_map.npz"

        if not path_json.exists() or not adc_npz.exists() or not map_npz.exists():
            raise FileNotFoundError("required output artifacts are missing")

        paths = json.loads(path_json.read_text(encoding="utf-8"))
        if not isinstance(paths, list):
            raise ValueError("path_list.json must contain list")

        with np.load(str(adc_npz), allow_pickle=False) as adc_payload:
            adc = np.asarray(adc_payload["adc"])

        with np.load(str(map_npz), allow_pickle=False) as map_payload:
            rd = np.asarray(map_payload["fx_dop_win"], dtype=np.float64)
            ra = np.asarray(map_payload["fx_ang"], dtype=np.float64)

        first_chirp_paths = paths[0] if len(paths) > 0 and isinstance(paths[0], list) else []

        return {
            "n_chirps": int(len(paths)),
            "path_count_total": int(sum(len(chirp) for chirp in paths)),
            "path_count_first_chirp": int(len(first_chirp_paths)),
            "adc_shape": [int(x) for x in adc.shape],
            "rd_shape": [int(x) for x in rd.shape],
            "ra_shape": [int(x) for x in ra.shape],
            "rd_top_peaks": _top_peaks(rd, "doppler_bin", "range_bin", top_k=6),
            "ra_top_peaks": _top_peaks(ra, "angle_bin", "range_bin", top_k=6),
        }

    def _record_path(self, run_id: str) -> Path:
        return self.runs_root / run_id / "run_record.json"

    def _load_record(self, run_id: str) -> dict[str, Any]:
        return self._load_record_path(self._record_path(run_id))

    def _load_record_path(self, path: Path) -> dict[str, Any]:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"run record not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_record(self, record: Mapping[str, Any]) -> None:
        run_id = str(record.get("run_id", "")).strip()
        if run_id == "":
            raise ValueError("run_id missing in record")
        path = self._record_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, default=_json_default), encoding="utf-8")

    def _mutate_record(self, run_id: str, mutate_fn: Any) -> dict[str, Any]:
        with self._lock:
            rec = self._load_record(run_id)
            mutate_fn(rec)
            rec["updated_at"] = _now_iso()
            self._save_record(rec)
            return rec


def _parse_bool_query(query: Mapping[str, list[str]], key: str, default: bool = True) -> bool:
    raw = query.get(key, None)
    if not raw:
        return bool(default)
    token = str(raw[0]).strip().lower()
    if token in {"1", "true", "yes", "y", "on"}:
        return True
    if token in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


def build_web_e2e_request_handler(orchestrator: WebE2EOrchestrator) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "WebE2EOrchestrator/0.1"

        def _send_json(self, status_code: int, payload: Mapping[str, Any]) -> None:
            body = json.dumps(payload, default=_json_default).encode("utf-8")
            self.send_response(int(status_code))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path

            try:
                if path == "/health":
                    self._send_json(
                        200,
                        {
                            "ok": True,
                            "repo_root": str(orchestrator.repo_root),
                            "store_root": str(orchestrator.store_root),
                            "run_count": len(orchestrator.list_runs()),
                        },
                    )
                    return

                if path == "/api/profiles":
                    self._send_json(200, {"profiles": orchestrator.get_profiles()})
                    return

                if path == "/api/runs":
                    self._send_json(200, {"runs": orchestrator.list_runs()})
                    return

                if path.startswith("/api/runs/"):
                    suffix = path[len("/api/runs/") :]
                    if suffix.endswith("/summary"):
                        run_id = suffix[: -len("/summary")]
                        payload = orchestrator.load_run_summary(run_id)
                        self._send_json(200, payload)
                        return

                    run_id = suffix
                    payload = orchestrator.get_run(run_id)
                    self._send_json(200, payload)
                    return

                self._send_json(404, {"ok": False, "error": f"not found: {path}"})
            except FileNotFoundError as exc:
                self._send_json(404, {"ok": False, "error": str(exc)})
            except ValueError as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
            except Exception as exc:
                self._send_json(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if path != "/api/runs":
                self._send_json(404, {"ok": False, "error": f"not found: {path}"})
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except Exception:
                content_length = 0

            raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception as exc:
                self._send_json(400, {"ok": False, "error": f"invalid json body: {exc}"})
                return

            run_async = _parse_bool_query(query, "async", default=True)
            try:
                record = orchestrator.submit_run(body, run_async=run_async)
                self._send_json(202 if run_async else 200, {"ok": True, "run": record})
            except FileNotFoundError as exc:
                self._send_json(404, {"ok": False, "error": str(exc)})
            except ValueError as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
            except Exception as exc:
                self._send_json(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})

    return Handler


def create_web_e2e_http_server(
    host: str,
    port: int,
    orchestrator: WebE2EOrchestrator,
) -> ThreadingHTTPServer:
    handler = build_web_e2e_request_handler(orchestrator)
    return ThreadingHTTPServer((host, int(port)), handler)


def serve_web_e2e_http_api(host: str, port: int, orchestrator: WebE2EOrchestrator) -> None:
    server = create_web_e2e_http_server(host=host, port=int(port), orchestrator=orchestrator)
    try:
        server.serve_forever()
    finally:
        server.server_close()

from __future__ import annotations

import datetime as _dt
import csv
import hashlib
import json
import re
import shutil
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from urllib.parse import parse_qs, urlparse

import numpy as np

from .graph_contract import build_default_graph_templates, validate_graph_contract_payload
from .parity import compare_hybrid_estimation_payloads
from .adc_pack_builder import estimate_rd_ra_from_adc
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

DEFAULT_COMPARE_POLICY: Dict[str, Any] = {
    "require_parity_pass": True,
    "max_failure_count": 0,
    "max_rd_shape_nmse": 0.25,
    "max_ra_shape_nmse": 0.25,
    "max_rd_peak_range_bin_abs_error": 1.0,
    "max_ra_peak_range_bin_abs_error": 1.0,
}

C0 = 299_792_458.0


class _GraphRunCanceled(RuntimeError):
    pass


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


def _decode_npz_metadata(payload: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    if "metadata_json" not in payload:
        return None

    raw = payload["metadata_json"]
    if isinstance(raw, np.ndarray):
        raw = raw.tolist()

    if isinstance(raw, bytes):
        text = raw.decode("utf-8")
    else:
        text = str(raw)

    try:
        obj = json.loads(text)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def _resolve_optional_visuals(output_dir: Path) -> Optional[dict[str, str]]:
    vis_dir = output_dir.parent / "visuals"
    file_map = {
        "rd_map_png": "rd_map.png",
        "ra_map_png": "ra_map.png",
        "adc_tx0_rx0_png": "adc_tx0_rx0.png",
        "path_scatter_chirp0_png": "path_scatter_chirp0.png",
    }
    out: dict[str, str] = {}
    for key, fname in file_map.items():
        p = (vis_dir / fname).resolve()
        if p.exists() and p.is_file():
            out[key] = str(p)
    return out if len(out) > 0 else None


def _extract_adc_slice_for_visual(adc: np.ndarray) -> np.ndarray:
    """Return 2D matrix for ADC quicklook (chirp x sample)."""
    arr = np.asarray(adc)
    if arr.ndim == 4:
        # Canonical shape in this repo: (sample, chirp, tx, rx)
        return np.abs(np.asarray(arr[:, :, 0, 0], dtype=np.complex128)).T
    if arr.ndim == 3:
        # Heuristic fallback:
        # - if first dimension is likely chirp, keep as is
        # - else transpose sample/chirp view
        if arr.shape[0] <= arr.shape[2]:
            return np.abs(np.asarray(arr[:, 0, :], dtype=np.complex128))
        return np.abs(np.asarray(arr[:, :, 0], dtype=np.complex128)).T
    if arr.ndim == 2:
        return np.abs(np.asarray(arr, dtype=np.complex128))
    raise ValueError(f"unsupported adc ndim for visual: {arr.ndim}")


def _build_visuals_best_effort(
    output_dir: Path,
    paths: list[Any],
    adc: np.ndarray,
    rd: np.ndarray,
    ra: np.ndarray,
    fc_hz: float,
) -> Optional[dict[str, str]]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None

    visual_dir = output_dir.parent / "visuals"
    visual_dir.mkdir(parents=True, exist_ok=True)

    try:
        rd_safe = np.maximum(np.asarray(rd, dtype=np.float64), np.finfo(np.float64).tiny)
        ra_safe = np.maximum(np.asarray(ra, dtype=np.float64), np.finfo(np.float64).tiny)

        rd_db = 10.0 * np.log10(rd_safe / float(np.max(rd_safe)))
        ra_db = 10.0 * np.log10(ra_safe / float(np.max(ra_safe)))

        fig, ax = plt.subplots(figsize=(8, 4))
        im = ax.imshow(rd_db, aspect="auto", origin="lower", cmap="turbo", vmin=-50.0, vmax=0.0)
        ax.set_title("Range-Doppler (dB)")
        ax.set_xlabel("Range bin")
        ax.set_ylabel("Doppler bin")
        fig.colorbar(im, ax=ax, label="dB rel")
        rd_png = visual_dir / "rd_map.png"
        fig.tight_layout()
        fig.savefig(rd_png, dpi=140)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 4))
        im = ax.imshow(ra_db, aspect="auto", origin="lower", cmap="turbo", vmin=-50.0, vmax=0.0)
        ax.set_title("Range-Angle (dB)")
        ax.set_xlabel("Range bin")
        ax.set_ylabel("Angle bin")
        fig.colorbar(im, ax=ax, label="dB rel")
        ra_png = visual_dir / "ra_map.png"
        fig.tight_layout()
        fig.savefig(ra_png, dpi=140)
        plt.close(fig)

        adc_view = _extract_adc_slice_for_visual(adc)
        adc_view = np.maximum(np.asarray(adc_view, dtype=np.float64), np.finfo(np.float64).tiny)
        adc_db = 20.0 * np.log10(adc_view / float(np.max(adc_view)))
        fig, ax = plt.subplots(figsize=(8, 4))
        im = ax.imshow(adc_db, aspect="auto", origin="lower", cmap="magma", vmin=-60.0, vmax=0.0)
        ax.set_title("ADC magnitude (Tx0-Rx0, dB)")
        ax.set_xlabel("Fast-time sample")
        ax.set_ylabel("Chirp")
        fig.colorbar(im, ax=ax, label="dB rel")
        adc_png = visual_dir / "adc_tx0_rx0.png"
        fig.tight_layout()
        fig.savefig(adc_png, dpi=140)
        plt.close(fig)

        first_chirp_paths = paths[0] if len(paths) > 0 and isinstance(paths[0], list) else []
        lam = C0 / float(max(fc_hz, 1e-9))
        ranges = []
        velocities = []
        labels = []
        amps_db = []
        for p in first_chirp_paths:
            if not isinstance(p, Mapping):
                continue
            delay_s = float(p.get("delay_s", 0.0))
            doppler_hz = float(p.get("doppler_hz", 0.0))
            amp_obj = p.get("amp_complex", {})
            if not isinstance(amp_obj, Mapping):
                amp_obj = {}
            amp_re = float(amp_obj.get("re", 0.0))
            amp_im = float(amp_obj.get("im", 0.0))
            amp_abs = max(np.hypot(amp_re, amp_im), 1e-15)
            ranges.append(0.5 * C0 * delay_s)
            velocities.append(0.5 * lam * doppler_hz)
            labels.append(str(p.get("path_id", "path")))
            amps_db.append(20.0 * np.log10(amp_abs))

        fig, ax = plt.subplots(figsize=(8, 4))
        if len(ranges) > 0:
            sc = ax.scatter(ranges, velocities, c=amps_db, cmap="viridis", s=80, edgecolors="k")
            for i, name in enumerate(labels):
                ax.annotate(name, (ranges[i], velocities[i]), textcoords="offset points", xytext=(5, 5), fontsize=8)
            fig.colorbar(sc, ax=ax, label="Amplitude (dB)")
        ax.set_title("First chirp path scatter")
        ax.set_xlabel("Range (m)")
        ax.set_ylabel("Radial velocity (m/s)")
        ax.grid(True, alpha=0.25)
        path_png = visual_dir / "path_scatter_chirp0.png"
        fig.tight_layout()
        fig.savefig(path_png, dpi=140)
        plt.close(fig)

        return {
            "rd_map_png": str(rd_png.resolve()),
            "ra_map_png": str(ra_png.resolve()),
            "adc_tx0_rx0_png": str(adc_png.resolve()),
            "path_scatter_chirp0_png": str(path_png.resolve()),
        }
    except Exception:
        return None


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
        self.comparisons_root = self.store_root / "comparisons"
        self.baselines_root = self.store_root / "baselines"
        self.policy_evals_root = self.store_root / "policy_evals"
        self.regression_sessions_root = self.store_root / "regression_sessions"
        self.regression_exports_root = self.store_root / "regression_exports"
        self.graph_runs_root = self.store_root / "graph_runs"
        self.graph_cache_root = self.store_root / "graph_cache"
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self.comparisons_root.mkdir(parents=True, exist_ok=True)
        self.baselines_root.mkdir(parents=True, exist_ok=True)
        self.policy_evals_root.mkdir(parents=True, exist_ok=True)
        self.regression_sessions_root.mkdir(parents=True, exist_ok=True)
        self.regression_exports_root.mkdir(parents=True, exist_ok=True)
        self.graph_runs_root.mkdir(parents=True, exist_ok=True)
        self.graph_cache_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._recover_stale_graph_runs()

    def get_profiles(self) -> Dict[str, Dict[str, Any]]:
        return dict(PROFILE_PRESETS)

    def get_graph_templates(self) -> list[dict[str, Any]]:
        return build_default_graph_templates()

    def validate_graph_contract(self, request_payload: Mapping[str, Any]) -> dict[str, Any]:
        return validate_graph_contract_payload(
            request_payload,
            allowed_profiles=PROFILE_PRESETS.keys(),
        )

    def list_graph_runs(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for record_path in sorted(self.graph_runs_root.glob("*/graph_run_record.json")):
            try:
                rows.append(self._load_graph_record_path(record_path))
            except Exception:
                continue
        rows.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return rows

    def get_graph_run(self, graph_run_id: str) -> dict[str, Any]:
        return self._load_graph_record(graph_run_id)

    def load_graph_run_summary(self, graph_run_id: str) -> dict[str, Any]:
        record = self.get_graph_run(graph_run_id)
        summary_path = Path(str(record["paths"]["graph_run_summary_json"]))
        if not summary_path.exists() or not summary_path.is_file():
            raise FileNotFoundError(f"graph run summary not found: {summary_path}")
        return json.loads(summary_path.read_text(encoding="utf-8"))

    def cancel_graph_run(
        self,
        graph_run_id: str,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        clean_reason = str(reason or "").strip() or None

        def _mut(rec: dict[str, Any]) -> None:
            status = str(rec.get("status", "")).strip().lower()
            ctrl = rec.get("control")
            if not isinstance(ctrl, Mapping):
                ctrl = {}
            ctrl_out = dict(ctrl)
            ctrl_out["cancel_requested"] = True
            ctrl_out["cancel_requested_at"] = _now_iso()
            ctrl_out["cancel_reason"] = clean_reason
            rec["control"] = ctrl_out

            if status in {"queued", "cancel_requested"}:
                rec["status"] = "canceled"
                rec["error"] = (
                    f"CanceledByUser: {clean_reason}" if clean_reason is not None else "CanceledByUser"
                )
                rec["result"] = None
                rec["recovery"] = {
                    "recoverable": True,
                    "reason": "run canceled before execution",
                    "retry_endpoint": f"/api/graph/runs/{graph_run_id}/retry",
                }
            elif status in {"running"}:
                rec["status"] = "cancel_requested"

        return self._mutate_graph_record(graph_run_id, _mut)

    def retry_graph_run(
        self,
        graph_run_id: str,
        request_payload: Mapping[str, Any],
        *,
        run_async: bool = True,
    ) -> dict[str, Any]:
        source = self.get_graph_run(graph_run_id)
        source_req = source.get("request")
        if not isinstance(source_req, Mapping):
            raise ValueError("source graph run request payload is invalid")

        if not isinstance(request_payload, Mapping):
            raise ValueError("request payload must be object")

        payload: dict[str, Any] = {
            "graph": source_req.get("graph"),
            "scene_json_path": request_payload.get(
                "scene_json_path",
                source_req.get("scene_json_path"),
            ),
            "scene_overrides": request_payload.get(
                "scene_overrides",
                source_req.get("scene_overrides"),
            ),
            "profile": request_payload.get("profile", source_req.get("profile")),
            "run_hybrid_estimation": request_payload.get(
                "run_hybrid_estimation",
                source_req.get("run_hybrid_estimation", False),
            ),
            "output_subdir": request_payload.get(
                "output_subdir",
                source_req.get("output_subdir", "output"),
            ),
            "tag": (
                str(request_payload.get("tag", "")).strip()
                or f"retry_{graph_run_id}"
            ),
            "rerun_from_node_id": request_payload.get(
                "rerun_from_node_id",
                source_req.get("rerun_from_node_id"),
            ),
            "retry_of_graph_run_id": graph_run_id,
        }

        cache_cfg = request_payload.get("cache")
        if isinstance(cache_cfg, Mapping):
            payload["cache"] = dict(cache_cfg)
        else:
            default_cache: dict[str, Any] = {"enable": True, "mode": "auto"}
            if str(source.get("status", "")).strip().lower() == "completed":
                default_cache["reuse_graph_run_id"] = graph_run_id
            payload["cache"] = default_cache

        return self.submit_graph_run(payload, run_async=run_async)

    def submit_graph_run(
        self,
        request_payload: Mapping[str, Any],
        run_async: bool = True,
    ) -> dict[str, Any]:
        req = self._normalize_graph_run_request(request_payload)
        cache_key = self._build_graph_cache_key(req)
        req["cache_key"] = cache_key
        graph_run_id = self._new_graph_run_id()
        graph_run_dir = self.graph_runs_root / graph_run_id
        output_dir = graph_run_dir / str(req["output_subdir"])
        graph_payload_json = graph_run_dir / "graph_payload.json"
        graph_run_summary_json = graph_run_dir / "graph_run_summary.json"
        graph_run_record_json = graph_run_dir / "graph_run_record.json"

        graph_run_dir.mkdir(parents=True, exist_ok=False)
        graph_payload_json.write_text(
            json.dumps(req["graph"], indent=2, default=_json_default),
            encoding="utf-8",
        )

        node_plan = [
            {
                "node_id": str(node.get("id", "")),
                "node_type": str(node.get("type", "")),
                "status": "queued",
            }
            for node in req["graph"]["nodes"]
        ]

        record: dict[str, Any] = {
            "version": "web_e2e_graph_run_record_v1",
            "graph_run_id": graph_run_id,
            "status": "queued",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "request": req,
            "graph_meta": {
                "graph_id": req["graph"]["graph_id"],
                "graph_version": req["graph"]["version"],
                "node_count": len(req["graph"]["nodes"]),
                "edge_count": len(req["graph"]["edges"]),
                "topological_order": list(req["graph_topological_order"]),
            },
            "node_plan": node_plan,
            "paths": {
                "graph_run_dir": str(graph_run_dir),
                "output_dir": str(output_dir),
                "graph_payload_json": str(graph_payload_json),
                "graph_run_summary_json": str(graph_run_summary_json),
                "graph_run_record_json": str(graph_run_record_json),
            },
            "result": None,
            "error": None,
            "cache": {
                "enabled": bool(req.get("cache", {}).get("enable", True)),
                "mode": str(req.get("cache", {}).get("mode", "auto")),
                "cache_key": cache_key,
                "requested_rerun_from_node_id": req.get("rerun_from_node_id"),
                "requested_reuse_graph_run_id": req.get("cache", {}).get("reuse_graph_run_id"),
                "hit": False,
                "hit_scope": "none",
                "source_graph_run_id": None,
            },
            "control": {
                "cancel_requested": False,
                "cancel_requested_at": None,
                "cancel_reason": None,
            },
            "recovery": {
                "recoverable": True,
                "reason": None,
                "retry_endpoint": f"/api/graph/runs/{graph_run_id}/retry",
            },
        }
        self._save_graph_record(record)

        if run_async:
            th = threading.Thread(target=self._execute_graph_run, args=(graph_run_id,), daemon=True)
            th.start()
        else:
            self._execute_graph_run(graph_run_id)

        return self.get_graph_run(graph_run_id)

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

    def list_comparisons(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for p in sorted(self.comparisons_root.glob("*.json")):
            try:
                rows.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        rows.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return rows

    def get_comparison(self, comparison_id: str) -> dict[str, Any]:
        p = self.comparisons_root / f"{comparison_id}.json"
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"comparison not found: {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def list_baselines(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for p in sorted(self.baselines_root.glob("*.json")):
            try:
                rows.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        rows.sort(key=lambda x: str(x.get("updated_at", x.get("created_at", ""))), reverse=True)
        return rows

    def get_baseline(self, baseline_id: str) -> dict[str, Any]:
        safe_id = self._normalize_identifier_token(baseline_id, field_name="baseline_id")
        p = self.baselines_root / f"{safe_id}.json"
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"baseline not found: {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def list_policy_evals(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for p in sorted(self.policy_evals_root.glob("*.json")):
            try:
                rows.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        rows.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return rows

    def get_policy_eval(self, policy_eval_id: str) -> dict[str, Any]:
        safe_id = self._normalize_identifier_token(policy_eval_id, field_name="policy_eval_id")
        p = self.policy_evals_root / f"{safe_id}.json"
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"policy eval not found: {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def list_regression_sessions(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for p in sorted(self.regression_sessions_root.glob("*.json")):
            try:
                rows.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        rows.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return rows

    def get_regression_session(self, session_id: str) -> dict[str, Any]:
        safe_id = self._normalize_identifier_token(session_id, field_name="session_id")
        p = self.regression_sessions_root / f"{safe_id}.json"
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"regression session not found: {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def list_regression_exports(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for p in sorted(self.regression_exports_root.glob("*.json")):
            try:
                rows.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        rows.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return rows

    def get_regression_export(self, export_id: str) -> dict[str, Any]:
        safe_id = self._normalize_identifier_token(export_id, field_name="export_id")
        p = self.regression_exports_root / f"{safe_id}.json"
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"regression export not found: {p}")
        return json.loads(p.read_text(encoding="utf-8"))

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

    def compare_runs(self, request_payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(request_payload, Mapping):
            raise ValueError("request payload must be object")

        ref_summary, ref_info = self._resolve_compare_target(request_payload, prefix="reference")
        cand_summary, cand_info = self._resolve_compare_target(request_payload, prefix="candidate")
        thresholds = self._normalize_thresholds(request_payload.get("thresholds"))

        ref_map_npz = self._extract_radar_map_npz_path(ref_summary)
        cand_map_npz = self._extract_radar_map_npz_path(cand_summary)
        ref_payload = self._load_radar_map_payload(ref_map_npz)
        cand_payload = self._load_radar_map_payload(cand_map_npz)
        parity = compare_hybrid_estimation_payloads(
            reference=ref_payload,
            candidate=cand_payload,
            thresholds=thresholds,
        )

        cmp_id = self._new_comparison_id()
        out = {
            "version": "web_e2e_compare_v1",
            "comparison_id": cmp_id,
            "created_at": _now_iso(),
            "reference": {
                **ref_info,
                "radar_map_npz": str(ref_map_npz),
            },
            "candidate": {
                **cand_info,
                "radar_map_npz": str(cand_map_npz),
            },
            "parity": parity,
            "verdict": {
                "pass": bool(parity.get("pass", False)),
                "failure_count": int(len(parity.get("failures", []))),
            },
        }

        out_path = self.comparisons_root / f"{cmp_id}.json"
        out_path.write_text(json.dumps(out, indent=2, default=_json_default), encoding="utf-8")
        return out

    def create_baseline(self, request_payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(request_payload, Mapping):
            raise ValueError("request payload must be object")

        baseline_id_raw = str(request_payload.get("baseline_id", "")).strip()
        if baseline_id_raw == "":
            raise ValueError("baseline_id is required")
        baseline_id = self._normalize_identifier_token(baseline_id_raw, field_name="baseline_id")

        overwrite = bool(request_payload.get("overwrite", False))
        note = str(request_payload.get("note", "")).strip() or None
        tags_raw = request_payload.get("tags")
        tags: Optional[list[str]] = None
        if isinstance(tags_raw, list):
            tags = [str(x).strip() for x in tags_raw if str(x).strip() != ""]

        summary, info = self._resolve_target_with_optional_prefix(
            request_payload=request_payload,
            run_id_key="run_id",
            summary_key="summary_json",
        )
        radar_map_npz = self._extract_radar_map_npz_path(summary)

        payload = {
            "version": "web_e2e_baseline_v1",
            "baseline_id": baseline_id,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "target": {
                "run_id": info.get("run_id"),
                "run_summary_json": info.get("run_summary_json"),
                "radar_map_npz": str(radar_map_npz),
            },
            "note": note,
            "tags": tags if tags is not None else [],
        }

        out_path = self.baselines_root / f"{baseline_id}.json"
        if out_path.exists() and not overwrite:
            raise ValueError(f"baseline already exists: {baseline_id} (set overwrite=true to replace)")
        if out_path.exists() and out_path.is_file():
            try:
                old = json.loads(out_path.read_text(encoding="utf-8"))
                payload["created_at"] = str(old.get("created_at", payload["created_at"]))
            except Exception:
                pass
        out_path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
        return payload

    def evaluate_compare_policy(self, request_payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(request_payload, Mapping):
            raise ValueError("request payload must be object")

        baseline_id = str(request_payload.get("baseline_id", "")).strip()
        if baseline_id != "":
            baseline = self.get_baseline(baseline_id)
            b_target = baseline.get("target")
            if not isinstance(b_target, Mapping):
                raise ValueError("baseline target is invalid")
            ref_summary, ref_info = self._resolve_target_with_optional_prefix(
                request_payload={
                    "run_id": b_target.get("run_id", ""),
                    "summary_json": b_target.get("run_summary_json", ""),
                },
                run_id_key="run_id",
                summary_key="summary_json",
            )
            baseline_meta = {
                "baseline_id": str(baseline.get("baseline_id", baseline_id)),
                "note": baseline.get("note"),
                "tags": baseline.get("tags", []),
            }
        else:
            ref_summary, ref_info = self._resolve_compare_target(request_payload, prefix="reference")
            baseline_meta = {"baseline_id": None}

        cand_summary, cand_info = self._resolve_compare_target(request_payload, prefix="candidate")
        thresholds = self._normalize_thresholds(request_payload.get("thresholds"))
        policy = self._normalize_compare_policy(request_payload.get("policy"))

        ref_map_npz = self._extract_radar_map_npz_path(ref_summary)
        cand_map_npz = self._extract_radar_map_npz_path(cand_summary)
        ref_payload = self._load_radar_map_payload(ref_map_npz)
        cand_payload = self._load_radar_map_payload(cand_map_npz)
        parity = compare_hybrid_estimation_payloads(
            reference=ref_payload,
            candidate=cand_payload,
            thresholds=thresholds,
        )

        gate_failures = self._evaluate_policy_failures(parity=parity, policy=policy)
        gate_failed = bool(len(gate_failures) > 0)

        eval_id = self._new_policy_eval_id()
        payload = {
            "version": "web_e2e_compare_policy_v1",
            "policy_eval_id": eval_id,
            "created_at": _now_iso(),
            "baseline": {
                **baseline_meta,
                **ref_info,
                "radar_map_npz": str(ref_map_npz),
            },
            "candidate": {
                **cand_info,
                "radar_map_npz": str(cand_map_npz),
            },
            "policy": policy,
            "parity": parity,
            "gate_failed": gate_failed,
            "gate_failures": gate_failures,
            "recommendation": "hold_candidate" if gate_failed else "adopt_candidate",
        }

        out_path = self.policy_evals_root / f"{eval_id}.json"
        out_path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
        return payload

    def run_regression_session(self, request_payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(request_payload, Mapping):
            raise ValueError("request payload must be object")

        session_id_raw = str(request_payload.get("session_id", "")).strip()
        session_id = (
            self._new_regression_session_id()
            if session_id_raw == ""
            else self._normalize_identifier_token(session_id_raw, field_name="session_id")
        )
        overwrite = bool(request_payload.get("overwrite", False))
        stop_on_first_fail = bool(request_payload.get("stop_on_first_fail", False))

        policy = self._normalize_compare_policy(request_payload.get("policy"))
        thresholds = self._normalize_thresholds(request_payload.get("thresholds"))

        baseline_id = str(request_payload.get("baseline_id", "")).strip()
        reference_run_id = str(request_payload.get("reference_run_id", "")).strip()
        reference_summary_json = str(request_payload.get("reference_summary_json", "")).strip()
        if baseline_id == "" and reference_run_id == "" and reference_summary_json == "":
            raise ValueError(
                "regression session requires baseline_id or reference_run_id/reference_summary_json"
            )

        note = str(request_payload.get("note", "")).strip() or None
        tag = str(request_payload.get("tag", "")).strip() or None

        candidates = self._normalize_regression_candidates(request_payload)
        if len(candidates) == 0:
            raise ValueError(
                "regression session requires candidates (candidate_run_ids/candidate_summary_jsons/candidates)"
            )

        rows: list[dict[str, Any]] = []
        adopted_count = 0
        held_count = 0
        truncated = False

        for idx, cand in enumerate(candidates):
            policy_req: dict[str, Any] = {
                "policy": policy,
            }
            if thresholds is not None:
                policy_req["thresholds"] = thresholds

            if baseline_id != "":
                policy_req["baseline_id"] = baseline_id
            else:
                if reference_run_id != "":
                    policy_req["reference_run_id"] = reference_run_id
                if reference_summary_json != "":
                    policy_req["reference_summary_json"] = reference_summary_json

            if cand["run_id"] is not None:
                policy_req["candidate_run_id"] = cand["run_id"]
            if cand["summary_json"] is not None:
                policy_req["candidate_summary_json"] = cand["summary_json"]

            eval_payload = self.evaluate_compare_policy(policy_req)
            gate_failed = bool(eval_payload.get("gate_failed", True))
            if gate_failed:
                held_count += 1
            else:
                adopted_count += 1

            parity = eval_payload.get("parity", {})
            metrics = parity.get("metrics", {}) if isinstance(parity, Mapping) else {}
            row = {
                "index": int(idx),
                "label": cand["label"],
                "candidate_run_id": cand["run_id"],
                "candidate_summary_json": cand["summary_json"],
                "policy_eval_id": str(eval_payload.get("policy_eval_id", "")),
                "gate_failed": gate_failed,
                "recommendation": str(eval_payload.get("recommendation", "")),
                "gate_failure_count": int(len(eval_payload.get("gate_failures", []))),
                "parity_pass": bool((parity or {}).get("pass", False)),
                "rd_shape_nmse": (
                    float(metrics["rd_shape_nmse"]) if "rd_shape_nmse" in metrics else None
                ),
                "ra_shape_nmse": (
                    float(metrics["ra_shape_nmse"]) if "ra_shape_nmse" in metrics else None
                ),
            }
            rows.append(row)

            if gate_failed and stop_on_first_fail:
                truncated = bool(idx + 1 < len(candidates))
                break

        requested_count = int(len(candidates))
        evaluated_count = int(len(rows))
        all_pass = bool(evaluated_count > 0 and held_count == 0 and not truncated)
        if all_pass:
            recommendation = "adopt_all_candidates"
        elif truncated:
            recommendation = "stopped_on_first_failure"
        else:
            recommendation = "hold_some_candidates"

        session_payload = {
            "version": "web_e2e_regression_session_v1",
            "session_id": session_id,
            "created_at": _now_iso(),
            "baseline": {
                "baseline_id": baseline_id if baseline_id != "" else None,
                "reference_run_id": reference_run_id if reference_run_id != "" else None,
                "reference_summary_json": (
                    reference_summary_json if reference_summary_json != "" else None
                ),
            },
            "policy": policy,
            "thresholds": thresholds,
            "stop_on_first_fail": stop_on_first_fail,
            "requested_candidate_count": requested_count,
            "evaluated_candidate_count": evaluated_count,
            "adopted_count": int(adopted_count),
            "held_count": int(held_count),
            "truncated": truncated,
            "all_pass": all_pass,
            "recommendation": recommendation,
            "note": note,
            "tag": tag,
            "rows": rows,
        }

        out_path = self.regression_sessions_root / f"{session_id}.json"
        if out_path.exists() and not overwrite:
            raise ValueError(
                f"regression session already exists: {session_id} (set overwrite=true to replace)"
            )
        out_path.write_text(
            json.dumps(session_payload, indent=2, default=_json_default),
            encoding="utf-8",
        )
        return session_payload

    def export_regression_session(self, request_payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(request_payload, Mapping):
            raise ValueError("request payload must be object")

        session_id_raw = str(request_payload.get("session_id", "")).strip()
        if session_id_raw == "":
            raise ValueError("session_id is required")
        session_id = self._normalize_identifier_token(session_id_raw, field_name="session_id")

        export_id_raw = str(request_payload.get("export_id", "")).strip()
        export_id = (
            self._new_regression_export_id()
            if export_id_raw == ""
            else self._normalize_identifier_token(export_id_raw, field_name="export_id")
        )

        overwrite = bool(request_payload.get("overwrite", False))
        include_policy_payload = bool(request_payload.get("include_policy_payload", False))
        note = str(request_payload.get("note", "")).strip() or None
        tag = str(request_payload.get("tag", "")).strip() or None

        session_payload = self.get_regression_session(session_id)
        rows_raw = session_payload.get("rows", [])
        if not isinstance(rows_raw, list):
            raise ValueError("regression session rows must be array")

        manifest_path = self.regression_exports_root / f"{export_id}.json"
        artifact_dir = self.regression_exports_root / export_id

        if (manifest_path.exists() or artifact_dir.exists()) and not overwrite:
            raise ValueError(
                f"regression export already exists: {export_id} (set overwrite=true to replace)"
            )
        if artifact_dir.exists():
            if not artifact_dir.is_dir():
                raise ValueError(f"artifact path exists and is not directory: {artifact_dir}")
            shutil.rmtree(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        session_json = artifact_dir / "regression_session.json"
        rows_csv = artifact_dir / "regression_rows.csv"
        summary_index_json = artifact_dir / "regression_summary_index.json"
        package_json = artifact_dir / "regression_package.json"

        session_json.write_text(
            json.dumps(session_payload, indent=2, default=_json_default),
            encoding="utf-8",
        )

        csv_fields = [
            "index",
            "label",
            "candidate_run_id",
            "candidate_summary_json",
            "policy_eval_id",
            "gate_failed",
            "recommendation",
            "gate_failure_count",
            "parity_pass",
            "rd_shape_nmse",
            "ra_shape_nmse",
        ]
        with rows_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writeheader()
            for row_raw in rows_raw:
                row = row_raw if isinstance(row_raw, Mapping) else {}
                writer.writerow({k: row.get(k) for k in csv_fields})

        index_rows: list[dict[str, Any]] = []
        package_rows: list[dict[str, Any]] = []
        for row_raw in rows_raw:
            row = dict(row_raw) if isinstance(row_raw, Mapping) else {}
            policy_eval_id = str(row.get("policy_eval_id", "")).strip()
            policy_eval = None
            policy_eval_json_path: Optional[str] = None
            baseline_row: dict[str, Any] = {}
            candidate_row: dict[str, Any] = {}
            parity_pass = bool(row.get("parity_pass", False))

            if policy_eval_id != "":
                try:
                    safe_eval_id = self._normalize_identifier_token(
                        policy_eval_id,
                        field_name="policy_eval_id",
                    )
                    p = self.policy_evals_root / f"{safe_eval_id}.json"
                    if p.exists() and p.is_file():
                        policy_eval_json_path = str(p.resolve())
                        policy_eval = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    policy_eval = None
                    policy_eval_json_path = None

            if isinstance(policy_eval, Mapping):
                b = policy_eval.get("baseline")
                c = policy_eval.get("candidate")
                if isinstance(b, Mapping):
                    baseline_row = {
                        "baseline_id": b.get("baseline_id"),
                        "baseline_run_id": b.get("run_id"),
                        "baseline_run_summary_json": b.get("run_summary_json"),
                        "baseline_radar_map_npz": b.get("radar_map_npz"),
                    }
                if isinstance(c, Mapping):
                    candidate_row = {
                        "candidate_run_id": row.get("candidate_run_id", c.get("run_id")),
                        "candidate_summary_json": row.get(
                            "candidate_summary_json",
                            c.get("run_summary_json"),
                        ),
                        "candidate_run_summary_json": c.get("run_summary_json"),
                        "candidate_radar_map_npz": c.get("radar_map_npz"),
                    }
                parity = policy_eval.get("parity")
                if isinstance(parity, Mapping):
                    parity_pass = bool(parity.get("pass", parity_pass))

            index_row = {
                "index": int(row.get("index", 0)),
                "label": row.get("label"),
                "candidate_run_id": row.get("candidate_run_id"),
                "candidate_summary_json": row.get("candidate_summary_json"),
                "policy_eval_id": policy_eval_id if policy_eval_id != "" else None,
                "policy_eval_json": policy_eval_json_path,
                "gate_failed": bool(row.get("gate_failed", False)),
                "recommendation": row.get("recommendation"),
                "parity_pass": parity_pass,
                "rd_shape_nmse": row.get("rd_shape_nmse"),
                "ra_shape_nmse": row.get("ra_shape_nmse"),
            }
            index_row.update(baseline_row)
            index_row.update(candidate_row)
            index_rows.append(index_row)

            package_row = dict(index_row)
            if include_policy_payload:
                package_row["policy_eval"] = policy_eval
            package_rows.append(package_row)

        index_payload = {
            "version": "web_e2e_regression_summary_index_v1",
            "export_id": export_id,
            "session_id": session_id,
            "created_at": _now_iso(),
            "row_count": len(index_rows),
            "session": {
                "version": session_payload.get("version"),
                "created_at": session_payload.get("created_at"),
                "requested_candidate_count": session_payload.get("requested_candidate_count"),
                "evaluated_candidate_count": session_payload.get("evaluated_candidate_count"),
                "adopted_count": session_payload.get("adopted_count"),
                "held_count": session_payload.get("held_count"),
                "truncated": session_payload.get("truncated"),
                "recommendation": session_payload.get("recommendation"),
            },
            "rows": index_rows,
        }
        summary_index_json.write_text(
            json.dumps(index_payload, indent=2, default=_json_default),
            encoding="utf-8",
        )

        package_payload = {
            "version": "web_e2e_regression_package_v1",
            "export_id": export_id,
            "session_id": session_id,
            "created_at": _now_iso(),
            "session_json": str(session_json.resolve()),
            "summary_index_json": str(summary_index_json.resolve()),
            "rows": package_rows,
            "include_policy_payload": include_policy_payload,
        }
        package_json.write_text(
            json.dumps(package_payload, indent=2, default=_json_default),
            encoding="utf-8",
        )

        export_payload = {
            "version": "web_e2e_regression_export_v1",
            "export_id": export_id,
            "created_at": _now_iso(),
            "session_id": session_id,
            "row_count": int(len(rows_raw)),
            "include_policy_payload": include_policy_payload,
            "session_recommendation": session_payload.get("recommendation"),
            "note": note,
            "tag": tag,
            "artifacts": {
                "artifact_dir": str(artifact_dir.resolve()),
                "session_json": str(session_json.resolve()),
                "rows_csv": str(rows_csv.resolve()),
                "summary_index_json": str(summary_index_json.resolve()),
                "package_json": str(package_json.resolve()),
            },
        }
        manifest_path.write_text(
            json.dumps(export_payload, indent=2, default=_json_default),
            encoding="utf-8",
        )
        return export_payload

    def _new_run_id(self) -> str:
        stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:8]
        return f"run_{stamp}_{token}"

    def _new_graph_run_id(self) -> str:
        stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:8]
        return f"grun_{stamp}_{token}"

    def _new_comparison_id(self) -> str:
        stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:8]
        return f"cmp_{stamp}_{token}"

    def _new_policy_eval_id(self) -> str:
        stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:8]
        return f"cpol_{stamp}_{token}"

    def _new_regression_session_id(self) -> str:
        stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:8]
        return f"rsess_{stamp}_{token}"

    def _new_regression_export_id(self) -> str:
        stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:8]
        return f"rexp_{stamp}_{token}"

    def _normalize_identifier_token(self, token: str, field_name: str) -> str:
        v = str(token).strip()
        if v == "":
            raise ValueError(f"{field_name} is required")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", v):
            raise ValueError(
                f"{field_name} must match [A-Za-z0-9_.-] and be 1..128 chars"
            )
        return v

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

    def _normalize_graph_run_request(self, request_payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(request_payload, Mapping):
            raise ValueError("request payload must be object")

        graph_payload = request_payload.get("graph")
        if not isinstance(graph_payload, Mapping):
            raise ValueError("graph run requires graph object in request.graph")
        gv = self.validate_graph_contract(graph_payload)
        if not bool(gv.get("valid", False)):
            errors = gv.get("errors", [])
            if isinstance(errors, list) and len(errors) > 0:
                joined = "; ".join(str(x) for x in errors[:6])
                raise ValueError(f"graph contract invalid: {joined}")
            raise ValueError("graph contract invalid")
        normalized_graph = dict(gv["normalized"])

        profile = str(request_payload.get("profile", normalized_graph.get("profile", "balanced_dev"))).strip()
        if profile == "":
            profile = str(normalized_graph.get("profile", "balanced_dev"))
        if profile not in PROFILE_PRESETS:
            raise ValueError(
                f"profile must be one of: {', '.join(sorted(PROFILE_PRESETS.keys()))}"
            )
        normalized_graph["profile"] = profile

        output_subdir = str(request_payload.get("output_subdir", "output")).strip() or "output"
        out_path = Path(output_subdir)
        if out_path.is_absolute() or any(part == ".." for part in out_path.parts):
            raise ValueError("output_subdir must be a safe relative path")

        graph_node_ids = {
            str(node.get("id", "")).strip()
            for node in normalized_graph.get("nodes", [])
            if isinstance(node, Mapping)
        }
        rerun_raw = request_payload.get("rerun_from_node_id", "")
        if rerun_raw is None:
            rerun_from_node_id_raw = ""
        else:
            rerun_from_node_id_raw = str(rerun_raw).strip()
            if rerun_from_node_id_raw.lower() in {"none", "null"}:
                rerun_from_node_id_raw = ""
        rerun_from_node_id = rerun_from_node_id_raw or None
        if rerun_from_node_id is not None and rerun_from_node_id not in graph_node_ids:
            raise ValueError(f"rerun_from_node_id not found in graph nodes: {rerun_from_node_id}")

        cache_raw = request_payload.get("cache")
        if cache_raw is None:
            cache_cfg: dict[str, Any] = {}
        elif isinstance(cache_raw, Mapping):
            cache_cfg = dict(cache_raw)
        else:
            raise ValueError("cache must be object when provided")
        cache_enable = bool(cache_cfg.get("enable", True))
        cache_mode = str(cache_cfg.get("mode", "auto")).strip().lower() or "auto"
        if cache_mode not in {"auto", "required", "off"}:
            raise ValueError("cache.mode must be one of: auto, required, off")
        if not cache_enable:
            cache_mode = "off"
        reuse_raw = str(
            cache_cfg.get(
                "reuse_graph_run_id",
                request_payload.get("reuse_graph_run_id", ""),
            )
        ).strip()
        reuse_graph_run_id = (
            self._normalize_identifier_token(reuse_raw, field_name="reuse_graph_run_id")
            if reuse_raw != ""
            else None
        )

        retry_of_raw = str(request_payload.get("retry_of_graph_run_id", "")).strip()
        retry_of_graph_run_id = (
            self._normalize_identifier_token(retry_of_raw, field_name="retry_of_graph_run_id")
            if retry_of_raw != ""
            else None
        )

        exec_raw = request_payload.get("execution_options")
        if exec_raw is None:
            execution_options: dict[str, Any] = {}
        elif isinstance(exec_raw, Mapping):
            execution_options = dict(exec_raw)
        else:
            raise ValueError("execution_options must be object when provided")
        debug_delay_s = float(execution_options.get("debug_delay_s", 0.0))
        if debug_delay_s < 0.0:
            raise ValueError("execution_options.debug_delay_s must be >= 0")
        if debug_delay_s > 60.0:
            raise ValueError("execution_options.debug_delay_s must be <= 60")

        scene_overrides_raw = request_payload.get("scene_overrides")
        if scene_overrides_raw is None:
            scene_overrides: dict[str, Any] = {}
        elif isinstance(scene_overrides_raw, Mapping):
            scene_overrides = self._normalize_scene_overrides(scene_overrides_raw)
        else:
            raise ValueError("scene_overrides must be object when provided")

        scene_json_raw = str(request_payload.get("scene_json_path", "")).strip()
        if scene_json_raw == "":
            for node in normalized_graph.get("nodes", []):
                if not isinstance(node, Mapping):
                    continue
                if str(node.get("type", "")).strip() != "SceneSource":
                    continue
                params = node.get("params")
                if not isinstance(params, Mapping):
                    continue
                candidate = str(params.get("scene_json_path", "")).strip()
                if candidate != "":
                    scene_json_raw = candidate
                    break
        if scene_json_raw == "":
            raise ValueError("scene_json_path is required (request field or SceneSource params)")
        scene_json_abs = self._resolve_scene_path(scene_json_raw)

        return {
            "graph": normalized_graph,
            "graph_topological_order": list(gv["normalized"].get("topological_order", [])),
            "scene_json_path": str(scene_json_abs),
            "scene_json_input": scene_json_raw,
            "scene_overrides": scene_overrides,
            "profile": profile,
            "run_hybrid_estimation": bool(request_payload.get("run_hybrid_estimation", False)),
            "output_subdir": output_subdir,
            "tag": str(request_payload.get("tag", "")).strip() or None,
            "rerun_from_node_id": rerun_from_node_id,
            "cache": {
                "enable": cache_enable,
                "mode": cache_mode,
                "reuse_graph_run_id": reuse_graph_run_id,
            },
            "retry_of_graph_run_id": retry_of_graph_run_id,
            "execution_options": {
                "debug_delay_s": debug_delay_s,
            },
            "requested_at": _now_iso(),
        }

    def _recover_stale_graph_runs(self) -> None:
        """Mark interrupted active graph runs as failed-recoverable on startup."""
        for path in sorted(self.graph_runs_root.glob("*/graph_run_record.json")):
            try:
                rec = self._load_graph_record_path(path)
            except Exception:
                continue
            status = str(rec.get("status", "")).strip().lower()
            if status not in {"queued", "running", "cancel_requested"}:
                continue
            rec["status"] = "failed"
            rec["updated_at"] = _now_iso()
            rec["error"] = (
                "RecoveredInterruptedRun: previous orchestrator instance exited before graph run finished"
            )
            rec["recovery"] = {
                "recoverable": True,
                "reason": "run was interrupted before completion",
                "retry_endpoint": f"/api/graph/runs/{rec.get('graph_run_id')}/retry",
                "hints": [
                    "retry the run from the latest request",
                    "if scene/config changed, pass overrides in retry payload",
                ],
            }
            self._save_graph_record(rec)

    def _scene_revision_token(self, scene_json_path: str) -> str:
        path = Path(str(scene_json_path)).expanduser().resolve()
        stat = path.stat()
        return f"{path}::{int(stat.st_size)}::{int(stat.st_mtime_ns)}"

    def _build_graph_cache_key(self, req: Mapping[str, Any]) -> str:
        payload = {
            "version": "graph_cache_key_v2",
            "graph": req.get("graph"),
            "graph_topological_order": req.get("graph_topological_order"),
            "scene_json_path": str(req.get("scene_json_path", "")),
            "scene_revision": self._scene_revision_token(str(req.get("scene_json_path", ""))),
            "scene_overrides": req.get("scene_overrides"),
            "profile": str(req.get("profile", "")),
            "run_hybrid_estimation": bool(req.get("run_hybrid_estimation", False)),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=_json_default)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"gcache_v2_{digest}"

    def _load_graph_summary_from_record(self, record: Mapping[str, Any]) -> dict[str, Any]:
        paths = record.get("paths")
        if not isinstance(paths, Mapping):
            raise ValueError("graph record paths missing")
        summary_path = Path(str(paths.get("graph_run_summary_json", ""))).expanduser().resolve()
        if not summary_path.exists() or not summary_path.is_file():
            raise FileNotFoundError(f"graph run summary not found: {summary_path}")
        return json.loads(summary_path.read_text(encoding="utf-8"))

    def _resolve_graph_cache_candidate(
        self,
        req: Mapping[str, Any],
        *,
        current_graph_run_id: str,
    ) -> Optional[dict[str, Any]]:
        cache_req = req.get("cache")
        if not isinstance(cache_req, Mapping):
            return None
        if not bool(cache_req.get("enable", True)):
            return None
        mode = str(cache_req.get("mode", "auto")).strip().lower() or "auto"
        if mode == "off":
            return None

        requested_raw = cache_req.get("reuse_graph_run_id", "")
        if requested_raw is None:
            requested_source = ""
        else:
            requested_source = str(requested_raw).strip()
            if requested_source.lower() in {"none", "null"}:
                requested_source = ""
        if requested_source != "":
            src = self.get_graph_run(requested_source)
            if str(src.get("status", "")).strip().lower() != "completed":
                if mode == "required":
                    raise ValueError(f"requested cache source is not completed: {requested_source}")
                return None
            self._load_graph_summary_from_record(src)
            return src

        cache_key = str(req.get("cache_key", "")).strip() or self._build_graph_cache_key(req)
        candidates = self.list_graph_runs()
        for rec in candidates:
            rid = str(rec.get("graph_run_id", "")).strip()
            if rid == "" or rid == current_graph_run_id:
                continue
            if str(rec.get("status", "")).strip().lower() != "completed":
                continue
            cache_meta = rec.get("cache")
            if not isinstance(cache_meta, Mapping):
                continue
            if str(cache_meta.get("cache_key", "")).strip() != cache_key:
                continue
            try:
                self._load_graph_summary_from_record(rec)
            except Exception:
                continue
            return rec

        if mode == "required":
            raise ValueError("graph cache miss while cache.mode=required")
        return None

    def _materialize_cached_graph_artifacts(
        self,
        *,
        source_summary: Mapping[str, Any],
        output_dir: Path,
        include_radar_map: bool,
    ) -> dict[str, str]:
        outputs = source_summary.get("outputs")
        if not isinstance(outputs, Mapping):
            raise ValueError("source summary outputs missing for cache materialization")

        required = [
            ("path_list_json", "path_list.json"),
            ("adc_cube_npz", "adc_cube.npz"),
        ]
        if include_radar_map:
            required.append(("radar_map_npz", "radar_map.npz"))

        copied: dict[str, str] = {}
        output_dir.mkdir(parents=True, exist_ok=True)
        for src_key, dst_name in required:
            src = Path(str(outputs.get(src_key, ""))).expanduser().resolve()
            if not src.exists() or not src.is_file():
                raise FileNotFoundError(f"cache source artifact not found: {src_key} -> {src}")
            dst = (output_dir / dst_name).resolve()
            shutil.copy2(src, dst)
            copied[src_key] = str(dst)
        return copied

    def _recompute_radar_map_from_cached_adc(
        self,
        *,
        scene_json_path: str,
        adc_cube_npz: str,
        output_dir: Path,
    ) -> str:
        scene_payload = json.loads(Path(scene_json_path).read_text(encoding="utf-8"))
        if not isinstance(scene_payload, Mapping):
            raise ValueError("scene json must be object")
        map_cfg = scene_payload.get("map_config")
        if not isinstance(map_cfg, Mapping):
            map_cfg = {}

        with np.load(str(adc_cube_npz), allow_pickle=False) as adc_payload:
            if "adc" not in adc_payload:
                raise ValueError("adc_cube_npz must contain 'adc' array")
            adc = np.asarray(adc_payload["adc"])
            adc_meta = _decode_npz_metadata(adc_payload)

        est = estimate_rd_ra_from_adc(
            adc_sctr=adc,
            nfft_range=self._opt_int_or_none(map_cfg.get("nfft_range")),
            nfft_doppler=self._opt_int_or_none(map_cfg.get("nfft_doppler")),
            nfft_angle=self._opt_int_or_none(map_cfg.get("nfft_angle")),
            range_window=str(map_cfg.get("range_window", "hann")),
            doppler_window=str(map_cfg.get("doppler_window", "hann")),
            angle_window=str(map_cfg.get("angle_window", "hann")),
            range_bin_limit=self._opt_int_or_none(map_cfg.get("range_bin_limit")),
        )

        backend = scene_payload.get("backend")
        backend_type = (
            str(backend.get("type", "")).strip()
            if isinstance(backend, Mapping)
            else "unknown"
        )

        tx_schedule: list[int] = []
        if isinstance(adc_meta, Mapping):
            raw_tx = adc_meta.get("tx_schedule")
            if isinstance(raw_tx, list):
                tx_schedule = [int(x) for x in raw_tx]
        if len(tx_schedule) == 0 and adc.ndim >= 2:
            tx_schedule = [0 for _ in range(int(adc.shape[1]))]

        out_map = (output_dir / "radar_map.npz").resolve()
        metadata = {
            "scene_id": scene_payload.get("scene_id"),
            "backend_type": backend_type,
            "frame_count": int(adc.shape[1]) if adc.ndim >= 2 else 0,
            "tx_schedule": tx_schedule,
            "rd_ra_metadata": est["metadata"],
            "recomputed_from_cached_adc": True,
        }
        np.savez_compressed(
            str(out_map),
            fx_dop_win=np.asarray(est["fx_dop_win"], dtype=np.float64),
            fx_ang=np.asarray(est["fx_ang"], dtype=np.float64),
            metadata_json=json.dumps(metadata),
        )
        return str(out_map)

    def _check_graph_run_cancel_requested(self, graph_run_id: str) -> bool:
        rec = self.get_graph_run(graph_run_id)
        status = str(rec.get("status", "")).strip().lower()
        if status in {"canceled", "cancel_requested"}:
            return True
        ctrl = rec.get("control")
        if isinstance(ctrl, Mapping) and bool(ctrl.get("cancel_requested", False)):
            return True
        return False

    def _raise_if_graph_run_canceled(self, graph_run_id: str, stage: str) -> None:
        if self._check_graph_run_cancel_requested(graph_run_id):
            raise _GraphRunCanceled(f"graph run canceled at stage: {stage}")

    def _sleep_with_cancel_checks(self, graph_run_id: str, delay_s: float) -> None:
        remain = max(float(delay_s), 0.0)
        while remain > 0.0:
            self._raise_if_graph_run_canceled(graph_run_id, "delay")
            dt = min(0.1, remain)
            time.sleep(dt)
            remain -= dt

    def _build_graph_failure_recovery(
        self,
        *,
        graph_run_id: str,
        req: Mapping[str, Any],
        exc: BaseException,
    ) -> dict[str, Any]:
        exc_type = type(exc).__name__
        msg = str(exc)
        hints: list[str] = []
        if isinstance(exc, FileNotFoundError):
            hints.append("check scene_json_path and referenced artifact paths")
        if isinstance(exc, ValueError):
            hints.append("validate graph contract and scene payload fields")
        if "cache" in msg.lower():
            hints.append("retry with cache.mode=off when cache source is stale")
        if len(hints) == 0:
            hints.append("retry the same run once to rule out transient failures")
        hints.append("use /api/graph/runs/{graph_run_id}/retry with overrides when needed")
        return {
            "recoverable": True,
            "reason": f"{exc_type}: {msg}",
            "hints": hints,
            "retry_endpoint": f"/api/graph/runs/{graph_run_id}/retry",
            "request_scene_json_path": req.get("scene_json_path"),
        }

    @staticmethod
    def _opt_int_or_none(value: Any) -> Optional[int]:
        if value is None:
            return None
        return int(value)

    def _resolve_scene_path(self, path_text: str) -> Path:
        path = Path(path_text).expanduser()
        if not path.is_absolute():
            path = (self.repo_root / path).resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"scene json not found: {path}")
        return path

    @staticmethod
    def _merge_nested_mapping(base: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
        out = dict(base)
        for key, value in patch.items():
            if isinstance(value, Mapping) and isinstance(out.get(key), Mapping):
                out[str(key)] = WebE2EOrchestrator._merge_nested_mapping(
                    dict(out.get(key, {})),
                    value,
                )
            else:
                out[str(key)] = value
        return out

    def _normalize_scene_overrides(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for section in ("backend", "radar"):
            value = raw.get(section)
            if value is None:
                continue
            if not isinstance(value, Mapping):
                raise ValueError(f"scene_overrides.{section} must be object")
            out[section] = json.loads(json.dumps(dict(value), default=_json_default))
        return out

    def _materialize_graph_run_scene_json(
        self,
        *,
        req: Mapping[str, Any],
        output_dir: Path,
    ) -> tuple[str, bool]:
        original_scene = str(req.get("scene_json_path", "")).strip()
        scene_overrides = req.get("scene_overrides")
        if (not isinstance(scene_overrides, Mapping)) or len(scene_overrides) == 0:
            return original_scene, False

        source_path = Path(original_scene).expanduser().resolve()
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("scene json must be object")
        scene_mut: dict[str, Any] = dict(payload)

        for section in ("backend", "radar"):
            patch = scene_overrides.get(section)
            if patch is None:
                continue
            if not isinstance(patch, Mapping):
                raise ValueError(f"scene_overrides.{section} must be object")
            existing = scene_mut.get(section)
            if isinstance(existing, Mapping):
                scene_mut[section] = self._merge_nested_mapping(dict(existing), patch)
            else:
                scene_mut[section] = dict(patch)

        out_path = (output_dir / "scene_overrides_applied.json").resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(scene_mut, indent=2, default=_json_default), encoding="utf-8")
        return str(out_path), True

    def _resolve_json_path(self, path_text: str, field_name: str) -> Path:
        path = Path(path_text).expanduser()
        if not path.is_absolute():
            path = (self.repo_root / path).resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"{field_name} not found: {path}")
        return path

    def _normalize_thresholds(self, raw: Any) -> Optional[dict[str, float]]:
        if raw is None:
            return None
        if not isinstance(raw, Mapping):
            raise ValueError("thresholds must be object")
        out: dict[str, float] = {}
        for key, value in raw.items():
            out[str(key)] = float(value)
        return out

    def _normalize_compare_policy(self, raw: Any) -> dict[str, Any]:
        out = dict(DEFAULT_COMPARE_POLICY)
        if raw is None:
            return out
        if not isinstance(raw, Mapping):
            raise ValueError("policy must be object")
        for key, value in raw.items():
            k = str(key)
            if k == "require_parity_pass":
                out[k] = bool(value)
            elif k == "max_failure_count":
                iv = int(value)
                if iv < 0:
                    raise ValueError("policy.max_failure_count must be >= 0")
                out[k] = iv
            else:
                if value is None:
                    out[k] = None
                else:
                    fv = float(value)
                    if fv < 0.0:
                        raise ValueError(f"policy.{k} must be >= 0")
                    out[k] = fv
        return out

    def _normalize_regression_candidates(
        self,
        request_payload: Mapping[str, Any],
    ) -> list[dict[str, Optional[str]]]:
        items: list[dict[str, Optional[str]]] = []

        def _append(run_id: Optional[str], summary_json: Optional[str], label: Optional[str]) -> None:
            r = (run_id or "").strip()
            s = (summary_json or "").strip()
            l = (label or "").strip()
            if r == "" and s == "":
                return
            items.append(
                {
                    "run_id": (r if r != "" else None),
                    "summary_json": (s if s != "" else None),
                    "label": (l if l != "" else None),
                }
            )

        raw_candidates = request_payload.get("candidates")
        if isinstance(raw_candidates, list):
            for item in raw_candidates:
                if isinstance(item, Mapping):
                    _append(
                        run_id=str(item.get("run_id", "")).strip(),
                        summary_json=str(item.get("summary_json", "")).strip(),
                        label=str(item.get("label", "")).strip(),
                    )
                else:
                    _append(run_id=str(item).strip(), summary_json="", label=None)

        raw_run_ids = request_payload.get("candidate_run_ids")
        if isinstance(raw_run_ids, list):
            for v in raw_run_ids:
                _append(run_id=str(v).strip(), summary_json="", label=None)

        raw_summary_jsons = request_payload.get("candidate_summary_jsons")
        if isinstance(raw_summary_jsons, list):
            for v in raw_summary_jsons:
                _append(run_id="", summary_json=str(v).strip(), label=None)

        deduped: list[dict[str, Optional[str]]] = []
        seen: set[tuple[Optional[str], Optional[str]]] = set()
        for item in items:
            key = (item.get("run_id"), item.get("summary_json"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _resolve_target_with_optional_prefix(
        self,
        request_payload: Mapping[str, Any],
        run_id_key: str,
        summary_key: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        run_id_raw = request_payload.get(run_id_key, "")
        if run_id_raw is None:
            run_id = ""
        else:
            run_id = str(run_id_raw).strip()
            if run_id.lower() in {"none", "null"}:
                run_id = ""

        summary_raw = request_payload.get(summary_key, "")
        if summary_raw is None:
            summary_json = ""
        else:
            summary_json = str(summary_raw).strip()
            if summary_json.lower() in {"none", "null"}:
                summary_json = ""

        if run_id != "":
            summary = self.load_run_summary(run_id)
            record = self.get_run(run_id)
            info = {
                "run_id": run_id,
                "run_summary_json": str(record["paths"]["run_summary_json"]),
            }
            return summary, info

        if summary_json != "":
            summary_path = self._resolve_json_path(summary_json, summary_key)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            if not isinstance(summary, Mapping):
                raise ValueError(f"{summary_key} must contain JSON object")
            info = {
                "run_id": None,
                "run_summary_json": str(summary_path),
            }
            return dict(summary), info

        raise ValueError(f"{run_id_key} or {summary_key} is required")

    def _resolve_compare_target(
        self,
        request_payload: Mapping[str, Any],
        prefix: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        run_id_key = f"{prefix}_run_id"
        summary_key = f"{prefix}_summary_json"
        return self._resolve_target_with_optional_prefix(
            request_payload=request_payload,
            run_id_key=run_id_key,
            summary_key=summary_key,
        )

    def _evaluate_policy_failures(
        self,
        parity: Mapping[str, Any],
        policy: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        failures: list[dict[str, Any]] = []
        metrics = parity.get("metrics", {})
        if not isinstance(metrics, Mapping):
            metrics = {}

        if bool(policy.get("require_parity_pass", True)) and (not bool(parity.get("pass", False))):
            failures.append(
                {
                    "rule": "require_parity_pass",
                    "value": bool(parity.get("pass", False)),
                    "limit": True,
                }
            )

        max_failure_count = int(policy.get("max_failure_count", 0))
        failure_count = int(len(parity.get("failures", [])))
        if failure_count > max_failure_count:
            failures.append(
                {
                    "rule": "max_failure_count",
                    "value": failure_count,
                    "limit": max_failure_count,
                }
            )

        metric_rules = {
            "max_rd_shape_nmse": "rd_shape_nmse",
            "max_ra_shape_nmse": "ra_shape_nmse",
            "max_rd_peak_range_bin_abs_error": "rd_peak_range_bin_abs_error",
            "max_ra_peak_range_bin_abs_error": "ra_peak_range_bin_abs_error",
            "max_rd_peak_doppler_bin_abs_error": "rd_peak_doppler_bin_abs_error",
            "max_ra_peak_angle_bin_abs_error": "ra_peak_angle_bin_abs_error",
        }
        for policy_key, metric_key in metric_rules.items():
            if policy_key not in policy:
                continue
            lim = policy.get(policy_key)
            if lim is None:
                continue
            if metric_key not in metrics:
                continue
            val = float(metrics[metric_key])
            limit = float(lim)
            if val > limit:
                failures.append(
                    {
                        "rule": policy_key,
                        "metric": metric_key,
                        "value": val,
                        "limit": limit,
                    }
                )

        return failures

    def _extract_radar_map_npz_path(self, summary_payload: Mapping[str, Any]) -> Path:
        outputs = summary_payload.get("outputs")
        path_text: Optional[str] = None
        if isinstance(outputs, Mapping):
            raw = outputs.get("radar_map_npz")
            if raw is not None:
                path_text = str(raw)
        if path_text is None or path_text.strip() == "":
            artifacts = summary_payload.get("artifacts")
            if isinstance(artifacts, Mapping):
                raw = artifacts.get("radar_map_npz")
                if raw is not None:
                    path_text = str(raw)
        if path_text is None or path_text.strip() == "":
            raise ValueError("summary payload missing outputs.radar_map_npz")
        return self._resolve_json_path(path_text, "radar_map_npz")

    def _load_radar_map_payload(self, radar_map_npz: Path) -> dict[str, Any]:
        with np.load(str(radar_map_npz), allow_pickle=False) as payload:
            if "fx_dop_win" not in payload or "fx_ang" not in payload:
                raise ValueError(f"radar map missing required arrays: {radar_map_npz}")
            out: dict[str, Any] = {
                "fx_dop_win": np.asarray(payload["fx_dop_win"]),
                "fx_ang": np.asarray(payload["fx_ang"]),
            }
        return out

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

            summary_body = self._build_summary_payload(
                scene_json_path=str(req["scene_json_path"]),
                output_dir=out_dir,
                run_out=run_out,
            )
            run_summary = {
                "version": "web_e2e_run_summary_v2",
                "run_id": run_id,
                "status": "completed",
                "profile": str(req.get("profile", "balanced_dev")),
                "created_at": str(record.get("created_at")),
                "completed_at": _now_iso(),
                "request": req,
            }
            run_summary.update(summary_body)

            summary_path = Path(str(record["paths"]["run_summary_json"]))
            run_summary["outputs"]["run_summary_json"] = str(summary_path)
            run_summary["artifacts"] = dict(run_summary["outputs"])
            summary_path.write_text(json.dumps(run_summary, indent=2, default=_json_default), encoding="utf-8")

            def _ok(rec: dict[str, Any]) -> None:
                rec["status"] = "completed"
                rec["updated_at"] = _now_iso()
                rec["result"] = {
                    "frame_count": int(run_out.get("frame_count", 0)),
                    "tx_schedule_len": len(run_out.get("tx_schedule", [])),
                    "path_count_total": int(run_summary["path_summary"]["path_count_total"]),
                    "quicklook": run_summary["quicklook"],
                    "run_summary_json": str(summary_path),
                    "summary_version": str(run_summary["version"]),
                }
                rec["error"] = None

            self._mutate_record(run_id, _ok)

        except Exception as exc:
            def _fail(rec: dict[str, Any]) -> None:
                rec["status"] = "failed"
                rec["updated_at"] = _now_iso()
                rec["error"] = f"{type(exc).__name__}: {exc}"

            self._mutate_record(run_id, _fail)

    def _execute_graph_run(self, graph_run_id: str) -> None:
        req: dict[str, Any] = {}
        cache_meta: dict[str, Any] = {}

        try:
            init_rec = self.get_graph_run(graph_run_id)
            if str(init_rec.get("status", "")).strip().lower() == "canceled":
                return
        except Exception:
            return

        self._mutate_graph_record(
            graph_run_id,
            lambda rec: rec.update(
                {
                    "status": "running",
                    "updated_at": _now_iso(),
                    "error": None,
                }
            ),
        )

        try:
            record = self.get_graph_run(graph_run_id)
            req = dict(record["request"])
            out_dir = Path(str(record["paths"]["output_dir"]))
            out_dir.mkdir(parents=True, exist_ok=True)

            self._raise_if_graph_run_canceled(graph_run_id, "before_execution")
            exec_opts = req.get("execution_options")
            if isinstance(exec_opts, Mapping):
                debug_delay_s = float(exec_opts.get("debug_delay_s", 0.0))
                if debug_delay_s > 0.0:
                    self._sleep_with_cancel_checks(graph_run_id, debug_delay_s)

            graph_obj = req.get("graph", {})
            nodes = graph_obj.get("nodes", []) if isinstance(graph_obj, Mapping) else []
            topological_order = req.get("graph_topological_order", [])
            node_by_id: dict[str, Mapping[str, Any]] = {}
            if isinstance(nodes, list):
                for node in nodes:
                    if isinstance(node, Mapping):
                        node_id = str(node.get("id", "")).strip()
                        if node_id != "":
                            node_by_id[node_id] = node

            rerun_from_node_id = str(req.get("rerun_from_node_id") or "").strip() or None
            rerun_idx: Optional[int] = None
            if rerun_from_node_id is not None and isinstance(topological_order, list):
                try:
                    rerun_idx = list(topological_order).index(rerun_from_node_id)
                except ValueError:
                    rerun_idx = None

            cache_req = req.get("cache")
            cache_meta = {
                "enabled": bool((cache_req or {}).get("enable", True)) if isinstance(cache_req, Mapping) else True,
                "mode": str((cache_req or {}).get("mode", "auto")) if isinstance(cache_req, Mapping) else "auto",
                "cache_key": str(req.get("cache_key", "")),
                "requested_rerun_from_node_id": rerun_from_node_id,
                "requested_reuse_graph_run_id": (
                    (cache_req or {}).get("reuse_graph_run_id")
                    if isinstance(cache_req, Mapping)
                    else None
                ),
                "hit": False,
                "hit_scope": "none",
                "source_graph_run_id": None,
                "note": None,
            }

            run_out: Optional[dict[str, Any]] = None
            bridge_mode = "scene_pipeline_single_pass_v1"
            cache_source = self._resolve_graph_cache_candidate(
                req,
                current_graph_run_id=graph_run_id,
            )
            if cache_source is not None:
                cache_source_id = str(cache_source.get("graph_run_id", "")).strip()
                cache_summary = self._load_graph_summary_from_record(cache_source)
                cache_meta["source_graph_run_id"] = cache_source_id

                source_quicklook = cache_summary.get("quicklook")
                source_adc_summary = cache_summary.get("adc_summary")
                source_frame_count = 0
                if isinstance(source_quicklook, Mapping):
                    source_frame_count = int(source_quicklook.get("n_chirps", 0))
                source_tx_schedule: list[int] = []
                if isinstance(source_adc_summary, Mapping):
                    source_adc_meta = source_adc_summary.get("metadata")
                    if isinstance(source_adc_meta, Mapping):
                        raw_tx = source_adc_meta.get("tx_schedule")
                        if isinstance(raw_tx, list):
                            source_tx_schedule = [int(x) for x in raw_tx]

                rerun_node_type = None
                if rerun_from_node_id is not None:
                    rerun_node = node_by_id.get(rerun_from_node_id, {})
                    rerun_node_type = str(rerun_node.get("type", "")).strip() or None

                if rerun_from_node_id is not None and rerun_node_type == "RadarMap":
                    copied = self._materialize_cached_graph_artifacts(
                        source_summary=cache_summary,
                        output_dir=out_dir,
                        include_radar_map=False,
                    )
                    out_map = self._recompute_radar_map_from_cached_adc(
                        scene_json_path=str(req["scene_json_path"]),
                        adc_cube_npz=str(copied["adc_cube_npz"]),
                        output_dir=out_dir,
                    )
                    run_out = {
                        "path_list_json": str(copied["path_list_json"]),
                        "adc_cube_npz": str(copied["adc_cube_npz"]),
                        "radar_map_npz": str(out_map),
                        "frame_count": source_frame_count,
                        "tx_schedule": source_tx_schedule,
                    }
                    bridge_mode = "scene_pipeline_partial_rerun_radar_map_v1"
                    cache_meta["hit"] = True
                    cache_meta["hit_scope"] = "partial"
                elif rerun_from_node_id is not None:
                    cache_meta["note"] = (
                        f"partial rerun requested from {rerun_from_node_id}, "
                        "but only RadarMap node is cache-rerunnable in bridge v1; falling back to full run"
                    )
                else:
                    copied = self._materialize_cached_graph_artifacts(
                        source_summary=cache_summary,
                        output_dir=out_dir,
                        include_radar_map=True,
                    )
                    run_out = {
                        "path_list_json": str(copied["path_list_json"]),
                        "adc_cube_npz": str(copied["adc_cube_npz"]),
                        "radar_map_npz": str(copied["radar_map_npz"]),
                        "frame_count": source_frame_count,
                        "tx_schedule": source_tx_schedule,
                    }
                    bridge_mode = "scene_pipeline_cache_full_reuse_v1"
                    cache_meta["hit"] = True
                    cache_meta["hit_scope"] = "full"

            if run_out is None:
                scene_json_path_effective, scene_overrides_applied = self._materialize_graph_run_scene_json(
                    req=req,
                    output_dir=out_dir,
                )
                run_out = run_object_scene_to_radar_map_json(
                    scene_json_path=str(scene_json_path_effective),
                    output_dir=str(out_dir),
                    run_hybrid_estimation=bool(req.get("run_hybrid_estimation", False)),
                )
            else:
                scene_json_path_effective = str(req["scene_json_path"])
                scene_overrides_applied = False

            self._raise_if_graph_run_canceled(graph_run_id, "after_execution")

            summary_body = self._build_summary_payload(
                scene_json_path=str(scene_json_path_effective),
                output_dir=out_dir,
                run_out=run_out,
            )

            node_results: list[dict[str, Any]] = []
            now_iso = _now_iso()
            for idx, node_id in enumerate(topological_order if isinstance(topological_order, list) else []):
                raw = node_by_id.get(str(node_id).strip(), {})
                node_type = str(raw.get("type", "unknown"))
                out_contract = "none"
                out_artifacts: dict[str, Any] = {}
                if node_type == "SceneSource":
                    out_contract = "scene_payload"
                    out_artifacts["scene_json"] = str(req["scene_json_path"])
                elif node_type == "Propagation":
                    out_contract = "path_list"
                    out_artifacts["path_list_json"] = summary_body["outputs"]["path_list_json"]
                elif node_type == "SynthFMCW":
                    out_contract = "adc_cube"
                    out_artifacts["adc_cube_npz"] = summary_body["outputs"]["adc_cube_npz"]
                elif node_type == "RadarMap":
                    out_contract = "radar_map"
                    out_artifacts["radar_map_npz"] = summary_body["outputs"]["radar_map_npz"]

                node_status = "completed"
                cache_hit_node = False
                if bool(cache_meta.get("hit", False)):
                    scope = str(cache_meta.get("hit_scope", "none"))
                    if scope == "full":
                        node_status = "cached"
                        cache_hit_node = True
                    elif scope == "partial" and rerun_idx is not None and idx < int(rerun_idx):
                        node_status = "cached"
                        cache_hit_node = True

                node_results.append(
                    {
                        "index": int(idx),
                        "node_id": str(node_id),
                        "node_type": node_type,
                        "status": node_status,
                        "cache_hit": cache_hit_node,
                        "cache_source_graph_run_id": cache_meta.get("source_graph_run_id"),
                        "started_at": now_iso,
                        "completed_at": now_iso,
                        "output_contract": out_contract,
                        "artifacts": out_artifacts,
                    }
                )

            graph_summary = {
                "version": "web_e2e_graph_run_summary_v1",
                "graph_run_id": graph_run_id,
                "status": "completed",
                "profile": str(req.get("profile", "balanced_dev")),
                "created_at": str(record.get("created_at")),
                "completed_at": _now_iso(),
                "request": req,
                "graph": {
                    "graph_id": str(graph_obj.get("graph_id", "unknown"))
                    if isinstance(graph_obj, Mapping)
                    else "unknown",
                    "graph_version": str(graph_obj.get("version", "unknown"))
                    if isinstance(graph_obj, Mapping)
                    else "unknown",
                    "node_count": int(len(nodes)) if isinstance(nodes, list) else 0,
                    "edge_count": int(len(graph_obj.get("edges", [])))
                    if isinstance(graph_obj, Mapping)
                    and isinstance(graph_obj.get("edges", []), list)
                    else 0,
                    "topological_order": list(topological_order)
                    if isinstance(topological_order, list)
                    else [],
                },
                "execution": {
                    "bridge_mode": bridge_mode,
                    "cache": cache_meta,
                    "scene_json_requested": str(req.get("scene_json_path", "")),
                    "scene_json_effective": str(scene_json_path_effective),
                    "scene_overrides_applied": bool(scene_overrides_applied),
                    "node_results": node_results,
                },
            }
            graph_summary.update(summary_body)

            graph_summary_path = Path(str(record["paths"]["graph_run_summary_json"]))
            graph_summary["outputs"]["graph_run_summary_json"] = str(graph_summary_path)
            graph_summary["artifacts"] = dict(graph_summary["outputs"])
            graph_summary["artifacts"]["graph_payload_json"] = str(record["paths"]["graph_payload_json"])
            graph_summary_path.write_text(
                json.dumps(graph_summary, indent=2, default=_json_default),
                encoding="utf-8",
            )

            def _ok(rec: dict[str, Any]) -> None:
                ctrl = rec.get("control")
                cancel_requested = bool(ctrl.get("cancel_requested")) if isinstance(ctrl, Mapping) else False
                if cancel_requested:
                    reason = None
                    if isinstance(ctrl, Mapping):
                        reason = str(ctrl.get("cancel_reason", "")).strip() or None
                    rec["status"] = "canceled"
                    rec["result"] = None
                    rec["error"] = (
                        f"CanceledByUser: {reason}" if reason is not None else "CanceledByUser"
                    )
                    rec["recovery"] = {
                        "recoverable": True,
                        "reason": "run canceled during execution finalization",
                        "retry_endpoint": f"/api/graph/runs/{graph_run_id}/retry",
                    }
                else:
                    rec["status"] = "completed"
                    rec["result"] = {
                        "graph_id": graph_summary["graph"]["graph_id"],
                        "node_count": int(graph_summary["graph"]["node_count"]),
                        "edge_count": int(graph_summary["graph"]["edge_count"]),
                        "path_count_total": int(graph_summary["path_summary"]["path_count_total"]),
                        "quicklook": graph_summary["quicklook"],
                        "graph_run_summary_json": str(graph_summary_path),
                        "summary_version": str(graph_summary["version"]),
                    }
                    rec["error"] = None
                    rec["recovery"] = {
                        "recoverable": True,
                        "reason": None,
                        "retry_endpoint": f"/api/graph/runs/{graph_run_id}/retry",
                    }
                rec["cache"] = dict(cache_meta)

            self._mutate_graph_record(graph_run_id, _ok)

        except _GraphRunCanceled as exc:
            def _cancel(rec: dict[str, Any]) -> None:
                rec["status"] = "canceled"
                rec["error"] = f"{type(exc).__name__}: {exc}"
                rec["result"] = None
                if len(cache_meta) > 0:
                    rec["cache"] = dict(cache_meta)
                rec["recovery"] = {
                    "recoverable": True,
                    "reason": "run canceled by user request",
                    "retry_endpoint": f"/api/graph/runs/{graph_run_id}/retry",
                    "hints": [
                        "submit retry to continue from latest request",
                    ],
                }

            self._mutate_graph_record(graph_run_id, _cancel)

        except Exception as exc:
            recovery = self._build_graph_failure_recovery(
                graph_run_id=graph_run_id,
                req=req,
                exc=exc,
            )
            tb = traceback.format_exc(limit=10)

            def _fail(rec: dict[str, Any]) -> None:
                rec["status"] = "failed"
                rec["error"] = f"{type(exc).__name__}: {exc}"
                rec["result"] = None
                rec["failure"] = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": tb,
                }
                if len(cache_meta) > 0:
                    rec["cache"] = dict(cache_meta)
                rec["recovery"] = recovery

            self._mutate_graph_record(graph_run_id, _fail)

    def _build_summary_payload(
        self,
        scene_json_path: str,
        output_dir: Path,
        run_out: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        path_json = output_dir / "path_list.json"
        adc_npz = output_dir / "adc_cube.npz"
        map_npz = output_dir / "radar_map.npz"

        if not path_json.exists() or not adc_npz.exists() or not map_npz.exists():
            raise FileNotFoundError("required output artifacts are missing")

        paths = json.loads(path_json.read_text(encoding="utf-8"))
        if not isinstance(paths, list):
            raise ValueError("path_list.json must contain list")
        if any(not isinstance(chirp, list) for chirp in paths):
            raise ValueError("path_list.json rows must be list")

        with np.load(str(adc_npz), allow_pickle=False) as adc_payload:
            adc = np.asarray(adc_payload["adc"])
            adc_meta = _decode_npz_metadata(adc_payload)

        with np.load(str(map_npz), allow_pickle=False) as map_payload:
            rd = np.asarray(map_payload["fx_dop_win"], dtype=np.float64)
            ra = np.asarray(map_payload["fx_ang"], dtype=np.float64)
            map_meta = _decode_npz_metadata(map_payload)

        first_chirp_paths = paths[0] if len(paths) > 0 and isinstance(paths[0], list) else []
        path_count_per_chirp = [int(len(chirp)) for chirp in paths]

        hybrid_estimation = (run_out or {}).get("hybrid_estimation_npz")
        outputs = {
            "path_list_json": str(Path(str((run_out or {}).get("path_list_json", path_json))).resolve()),
            "adc_cube_npz": str(Path(str((run_out or {}).get("adc_cube_npz", adc_npz))).resolve()),
            "radar_map_npz": str(Path(str((run_out or {}).get("radar_map_npz", map_npz))).resolve()),
            "hybrid_estimation_npz": (
                str(Path(str(hybrid_estimation)).resolve()) if hybrid_estimation else None
            ),
        }

        quicklook = {
            "n_chirps": int(len(paths)),
            "path_count_total": int(sum(path_count_per_chirp)),
            "path_count_first_chirp": int(len(first_chirp_paths)),
            "adc_shape": [int(x) for x in adc.shape],
            "rd_shape": [int(x) for x in rd.shape],
            "ra_shape": [int(x) for x in ra.shape],
            "rd_top_peaks": _top_peaks(rd, "doppler_bin", "range_bin", top_k=6),
            "ra_top_peaks": _top_peaks(ra, "angle_bin", "range_bin", top_k=6),
        }

        payload: dict[str, Any] = {
            "scene_json": str(Path(scene_json_path).resolve()),
            "outputs": outputs,
            "path_summary": {
                "n_chirps": int(len(paths)),
                "path_count_total": int(sum(path_count_per_chirp)),
                "path_count_per_chirp": path_count_per_chirp,
                "first_chirp_paths": first_chirp_paths,
            },
            "adc_summary": {
                "shape": [int(x) for x in adc.shape],
                "dtype": str(adc.dtype),
                "abs_mean": float(np.mean(np.abs(adc))),
                "abs_max": float(np.max(np.abs(adc))),
                "metadata": adc_meta,
            },
            "radar_map_summary": {
                "rd_shape": [int(x) for x in rd.shape],
                "ra_shape": [int(x) for x in ra.shape],
                "rd_top_peaks": quicklook["rd_top_peaks"],
                "ra_top_peaks": quicklook["ra_top_peaks"],
                "metadata": map_meta,
            },
            "quicklook": quicklook,
        }

        visuals = _resolve_optional_visuals(output_dir)
        if visuals is None:
            fc_hz = 77e9
            if isinstance(adc_meta, Mapping) and "fc_hz" in adc_meta:
                fc_hz = float(adc_meta["fc_hz"])
            visuals = _build_visuals_best_effort(
                output_dir=output_dir,
                paths=paths,
                adc=adc,
                rd=rd,
                ra=ra,
                fc_hz=fc_hz,
            )
        if visuals is not None:
            payload["visuals"] = visuals

        return payload

    def _record_path(self, run_id: str) -> Path:
        return self.runs_root / run_id / "run_record.json"

    def _graph_record_path(self, graph_run_id: str) -> Path:
        return self.graph_runs_root / graph_run_id / "graph_run_record.json"

    def _load_record(self, run_id: str) -> dict[str, Any]:
        return self._load_record_path(self._record_path(run_id))

    def _load_record_path(self, path: Path) -> dict[str, Any]:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"run record not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_graph_record(self, graph_run_id: str) -> dict[str, Any]:
        return self._load_graph_record_path(self._graph_record_path(graph_run_id))

    def _load_graph_record_path(self, path: Path) -> dict[str, Any]:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"graph run record not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_record(self, record: Mapping[str, Any]) -> None:
        run_id = str(record.get("run_id", "")).strip()
        if run_id == "":
            raise ValueError("run_id missing in record")
        path = self._record_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, default=_json_default), encoding="utf-8")

    def _save_graph_record(self, record: Mapping[str, Any]) -> None:
        graph_run_id = str(record.get("graph_run_id", "")).strip()
        if graph_run_id == "":
            raise ValueError("graph_run_id missing in record")
        path = self._graph_record_path(graph_run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, default=_json_default), encoding="utf-8")

    def _mutate_record(self, run_id: str, mutate_fn: Any) -> dict[str, Any]:
        with self._lock:
            rec = self._load_record(run_id)
            mutate_fn(rec)
            rec["updated_at"] = _now_iso()
            self._save_record(rec)
            return rec

    def _mutate_graph_record(self, graph_run_id: str, mutate_fn: Any) -> dict[str, Any]:
        with self._lock:
            rec = self._load_graph_record(graph_run_id)
            mutate_fn(rec)
            rec["updated_at"] = _now_iso()
            self._save_graph_record(rec)
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


def _parse_optional_text_query(query: Mapping[str, list[str]], key: str) -> Optional[str]:
    raw = query.get(key, None)
    if not raw:
        return None
    token = str(raw[0]).strip()
    if token == "":
        return None
    if token.lower() in {"none", "null"}:
        return None
    return token


def _parse_nonneg_int_query(
    query: Mapping[str, list[str]],
    key: str,
    default: int = 0,
) -> int:
    raw = query.get(key, None)
    if not raw:
        return int(default)
    token = str(raw[0]).strip()
    if token == "":
        return int(default)
    value = int(token)
    if value < 0:
        raise ValueError(f"query.{key} must be >= 0")
    return value


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
            query = parse_qs(parsed.query)

            try:
                if path == "/health":
                    self._send_json(
                        200,
                        {
                            "ok": True,
                            "repo_root": str(orchestrator.repo_root),
                            "store_root": str(orchestrator.store_root),
                            "run_count": len(orchestrator.list_runs()),
                            "comparison_count": len(orchestrator.list_comparisons()),
                            "baseline_count": len(orchestrator.list_baselines()),
                            "policy_eval_count": len(orchestrator.list_policy_evals()),
                            "regression_session_count": len(orchestrator.list_regression_sessions()),
                            "regression_export_count": len(orchestrator.list_regression_exports()),
                            "graph_template_count": len(orchestrator.get_graph_templates()),
                            "graph_run_count": len(orchestrator.list_graph_runs()),
                        },
                    )
                    return

                if path == "/api/profiles":
                    self._send_json(200, {"profiles": orchestrator.get_profiles()})
                    return

                if path == "/api/graph/templates":
                    self._send_json(200, {"templates": orchestrator.get_graph_templates()})
                    return

                if path == "/api/graph/runs":
                    self._send_json(200, {"graph_runs": orchestrator.list_graph_runs()})
                    return

                if path == "/api/runs":
                    self._send_json(200, {"runs": orchestrator.list_runs()})
                    return

                if path == "/api/comparisons":
                    self._send_json(200, {"comparisons": orchestrator.list_comparisons()})
                    return

                if path == "/api/baselines":
                    self._send_json(200, {"baselines": orchestrator.list_baselines()})
                    return

                if path == "/api/policy-evals":
                    candidate_run_id = _parse_optional_text_query(query, "candidate_run_id")
                    baseline_id = _parse_optional_text_query(query, "baseline_id")
                    limit = _parse_nonneg_int_query(query, "limit", default=0)
                    offset = _parse_nonneg_int_query(query, "offset", default=0)

                    rows = orchestrator.list_policy_evals()

                    if candidate_run_id is not None:
                        rows = [
                            x
                            for x in rows
                            if str(
                                (
                                    x.get("candidate", {})
                                    if isinstance(x.get("candidate"), Mapping)
                                    else {}
                                ).get("run_id", "")
                            ).strip()
                            == candidate_run_id
                        ]
                    if baseline_id is not None:
                        rows = [
                            x
                            for x in rows
                            if str(
                                (
                                    x.get("baseline", {})
                                    if isinstance(x.get("baseline"), Mapping)
                                    else {}
                                ).get("baseline_id", "")
                            ).strip()
                            == baseline_id
                        ]

                    total_count = len(rows)
                    if offset > 0:
                        rows = rows[offset:]
                    if limit > 0:
                        rows = rows[:limit]

                    self._send_json(
                        200,
                        {
                            "policy_evals": rows,
                            "page": {
                                "total_count": int(total_count),
                                "returned_count": int(len(rows)),
                                "offset": int(offset),
                                "limit": int(limit),
                                "filtered": {
                                    "candidate_run_id": candidate_run_id,
                                    "baseline_id": baseline_id,
                                },
                            },
                        },
                    )
                    return

                if path == "/api/regression-sessions":
                    self._send_json(200, {"regression_sessions": orchestrator.list_regression_sessions()})
                    return

                if path == "/api/regression-exports":
                    self._send_json(200, {"regression_exports": orchestrator.list_regression_exports()})
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

                if path.startswith("/api/graph/runs/"):
                    suffix = path[len("/api/graph/runs/") :]
                    if suffix.endswith("/summary"):
                        graph_run_id = suffix[: -len("/summary")]
                        payload = orchestrator.load_graph_run_summary(graph_run_id)
                        self._send_json(200, payload)
                        return

                    graph_run_id = suffix
                    payload = orchestrator.get_graph_run(graph_run_id)
                    self._send_json(200, payload)
                    return

                if path.startswith("/api/comparisons/"):
                    cmp_id = path[len("/api/comparisons/") :]
                    payload = orchestrator.get_comparison(cmp_id)
                    self._send_json(200, payload)
                    return

                if path.startswith("/api/baselines/"):
                    baseline_id = path[len("/api/baselines/") :]
                    payload = orchestrator.get_baseline(baseline_id)
                    self._send_json(200, payload)
                    return

                if path.startswith("/api/policy-evals/"):
                    eval_id = path[len("/api/policy-evals/") :]
                    payload = orchestrator.get_policy_eval(eval_id)
                    self._send_json(200, payload)
                    return

                if path.startswith("/api/regression-sessions/"):
                    session_id = path[len("/api/regression-sessions/") :]
                    payload = orchestrator.get_regression_session(session_id)
                    self._send_json(200, payload)
                    return

                if path.startswith("/api/regression-exports/"):
                    export_id = path[len("/api/regression-exports/") :]
                    payload = orchestrator.get_regression_export(export_id)
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

            is_graph_run_cancel = path.startswith("/api/graph/runs/") and path.endswith("/cancel")
            is_graph_run_retry = path.startswith("/api/graph/runs/") and path.endswith("/retry")

            if (
                path
                not in {
                    "/api/runs",
                    "/api/compare",
                    "/api/baselines",
                    "/api/compare/policy",
                    "/api/regression-sessions",
                    "/api/regression-exports",
                    "/api/graph/validate",
                    "/api/graph/runs",
                }
                and (not is_graph_run_cancel)
                and (not is_graph_run_retry)
            ):
                self._send_json(404, {"ok": False, "error": f"not found: {path}"})
                return

            if is_graph_run_cancel:
                suffix = path[len("/api/graph/runs/") : -len("/cancel")]
                if str(suffix).strip().strip("/") == "":
                    self._send_json(400, {"ok": False, "error": "graph_run_id is required"})
                    return
            if is_graph_run_retry:
                suffix = path[len("/api/graph/runs/") : -len("/retry")]
                if str(suffix).strip().strip("/") == "":
                    self._send_json(400, {"ok": False, "error": "graph_run_id is required"})
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

            try:
                if is_graph_run_cancel:
                    graph_run_id = str(
                        path[len("/api/graph/runs/") : -len("/cancel")]
                    ).strip().strip("/")
                    reason = None
                    if isinstance(body, Mapping):
                        reason_raw = body.get("reason", None)
                        if reason_raw is not None:
                            reason = str(reason_raw).strip() or None
                    payload = orchestrator.cancel_graph_run(graph_run_id=graph_run_id, reason=reason)
                    self._send_json(200, {"ok": True, "graph_run": payload})
                    return

                if is_graph_run_retry:
                    graph_run_id = str(
                        path[len("/api/graph/runs/") : -len("/retry")]
                    ).strip().strip("/")
                    run_async = _parse_bool_query(query, "async", default=True)
                    payload = body if isinstance(body, Mapping) else {}
                    record = orchestrator.retry_graph_run(
                        graph_run_id=graph_run_id,
                        request_payload=payload,
                        run_async=run_async,
                    )
                    self._send_json(202 if run_async else 200, {"ok": True, "graph_run": record})
                    return

                if path == "/api/runs":
                    run_async = _parse_bool_query(query, "async", default=True)
                    record = orchestrator.submit_run(body, run_async=run_async)
                    self._send_json(202 if run_async else 200, {"ok": True, "run": record})
                    return

                if path == "/api/compare":
                    payload = orchestrator.compare_runs(body)
                    self._send_json(200, {"ok": True, "comparison": payload})
                    return

                if path == "/api/baselines":
                    payload = orchestrator.create_baseline(body)
                    self._send_json(200, {"ok": True, "baseline": payload})
                    return

                if path == "/api/compare/policy":
                    payload = orchestrator.evaluate_compare_policy(body)
                    self._send_json(200, {"ok": True, "policy_eval": payload})
                    return

                if path == "/api/regression-sessions":
                    payload = orchestrator.run_regression_session(body)
                    self._send_json(200, {"ok": True, "regression_session": payload})
                    return

                if path == "/api/regression-exports":
                    payload = orchestrator.export_regression_session(body)
                    self._send_json(200, {"ok": True, "regression_export": payload})
                    return

                if path == "/api/graph/validate":
                    payload = orchestrator.validate_graph_contract(body)
                    self._send_json(200, {"ok": bool(payload.get("valid")), "graph_validation": payload})
                    return

                if path == "/api/graph/runs":
                    run_async = _parse_bool_query(query, "async", default=True)
                    record = orchestrator.submit_graph_run(body, run_async=run_async)
                    self._send_json(
                        202 if run_async else 200,
                        {"ok": True, "graph_run": record},
                    )
                    return

                self._send_json(404, {"ok": False, "error": f"not found: {path}"})
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

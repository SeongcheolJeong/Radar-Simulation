from __future__ import annotations

import datetime as _dt
import json
import re
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from urllib.parse import parse_qs, urlparse

import numpy as np

from .parity import compare_hybrid_estimation_payloads
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
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self.comparisons_root.mkdir(parents=True, exist_ok=True)
        self.baselines_root.mkdir(parents=True, exist_ok=True)
        self.policy_evals_root.mkdir(parents=True, exist_ok=True)
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

    def _new_run_id(self) -> str:
        stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:8]
        return f"run_{stamp}_{token}"

    def _new_comparison_id(self) -> str:
        stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:8]
        return f"cmp_{stamp}_{token}"

    def _new_policy_eval_id(self) -> str:
        stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        token = uuid.uuid4().hex[:8]
        return f"cpol_{stamp}_{token}"

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

    def _resolve_scene_path(self, path_text: str) -> Path:
        path = Path(path_text).expanduser()
        if not path.is_absolute():
            path = (self.repo_root / path).resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"scene json not found: {path}")
        return path

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

    def _resolve_target_with_optional_prefix(
        self,
        request_payload: Mapping[str, Any],
        run_id_key: str,
        summary_key: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        run_id = str(request_payload.get(run_id_key, "")).strip()
        summary_json = str(request_payload.get(summary_key, "")).strip()

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
                            "comparison_count": len(orchestrator.list_comparisons()),
                            "baseline_count": len(orchestrator.list_baselines()),
                            "policy_eval_count": len(orchestrator.list_policy_evals()),
                        },
                    )
                    return

                if path == "/api/profiles":
                    self._send_json(200, {"profiles": orchestrator.get_profiles()})
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
                    self._send_json(200, {"policy_evals": orchestrator.list_policy_evals()})
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

            if path not in {"/api/runs", "/api/compare", "/api/baselines", "/api/compare/policy"}:
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

            try:
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

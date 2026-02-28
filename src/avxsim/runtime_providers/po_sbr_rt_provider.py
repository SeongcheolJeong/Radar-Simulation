from __future__ import annotations

import importlib
import importlib.util
import math
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from ..constants import C0


def generate_po_sbr_like_paths_from_posbr(context: Mapping[str, Any]) -> Dict[str, Any]:
    n_chirps = int(context.get("n_chirps", 1))
    if n_chirps <= 0:
        raise ValueError("context.n_chirps must be positive")

    fc_hz = float(context.get("fc_hz", 77e9))
    if fc_hz <= 0.0:
        raise ValueError("context.fc_hz must be > 0")
    lam = C0 / fc_hz

    runtime_input = _as_obj(context, "runtime_input", required=False)
    repo_root = _resolve_repo_root(runtime_input=runtime_input)
    geometry_path = _resolve_geometry_path(repo_root=repo_root, runtime_input=runtime_input)

    alpha_deg = float(runtime_input.get("alpha_deg", 180.0))
    phi_deg = float(runtime_input.get("phi_deg", 90.0))
    theta_deg = float(runtime_input.get("theta_deg", 90.0))
    phi_rate_deg_per_s = float(runtime_input.get("phi_rate_deg_per_s", 0.0))
    chirp_interval_s = float(runtime_input.get("chirp_interval_s", 4.0e-5))
    freq_hz = float(runtime_input.get("freq_hz", fc_hz))
    rays_per_lambda = float(runtime_input.get("rays_per_lambda", 3.0))
    bounces = int(runtime_input.get("bounces", 2))
    radial_velocity_mps = float(runtime_input.get("radial_velocity_mps", 0.0))
    doppler_hz = float(2.0 * radial_velocity_mps / lam)
    amp_scale = _parse_complex(runtime_input.get("amp_scale", 1.0), "runtime_input.amp_scale")
    material_tag = str(runtime_input.get("material_tag", "po_sbr_runtime"))
    reflection_order = int(runtime_input.get("reflection_order", max(bounces, 1)))
    if reflection_order < 0:
        raise ValueError("runtime_input.reflection_order must be >= 0")
    min_range_m = max(float(runtime_input.get("min_range_m", 1.0e-6)), 1.0e-6)

    _assert_po_sbr_runtime_prereqs()
    _apply_igl_compat()
    po = _load_po_solver_module(repo_root=repo_root)
    v, f = po.build(str(geometry_path))

    paths_by_chirp: List[List[Dict[str, Any]]] = []
    for chirp_idx in range(n_chirps):
        t_chirp = float(chirp_idx) * chirp_interval_s
        phi_k = float(phi_deg + phi_rate_deg_per_s * t_chirp)
        e_theta, e_phi, r0 = po.simulate(
            float(alpha_deg),
            float(phi_k),
            float(theta_deg),
            float(freq_hz),
            float(rays_per_lambda),
            v,
            f,
            int(bounces),
        )
        amp = amp_scale * (complex(e_theta) + complex(e_phi))
        one_way_range_m = max(float(r0), float(min_range_m))
        tau = float(2.0 * one_way_range_m / C0)
        ux, uy, uz = _unit_direction_from_angles(phi_deg=float(phi_k), theta_deg=float(theta_deg))
        paths_by_chirp.append(
            [
                {
                    "delay_s": tau,
                    "doppler_hz": doppler_hz,
                    "unit_direction": [ux, uy, uz],
                    "amp_complex": {"re": float(amp.real), "im": float(amp.imag)},
                    "path_id": f"po_sbr_runtime_c{int(chirp_idx):04d}",
                    "material_tag": material_tag,
                    "reflection_order": reflection_order,
                }
            ]
        )

    return {"paths_by_chirp": paths_by_chirp}


def _assert_po_sbr_runtime_prereqs() -> None:
    missing: List[str] = []
    for module_name in ("igl", "rtxpy"):
        try:
            importlib.import_module(module_name)
        except Exception:
            missing.append(module_name)
    if len(missing) > 0:
        raise RuntimeError(f"missing required PO-SBR runtime modules: {', '.join(missing)}")


def _apply_igl_compat() -> None:
    igl = importlib.import_module("igl")
    if hasattr(igl, "bounding_box_diagonal"):
        return
    if not hasattr(igl, "bounding_box"):
        return

    # Some libigl wheels expose `bounding_box` but not `bounding_box_diagonal`.
    def _bounding_box_diagonal(v: Any) -> float:
        bv, _ = igl.bounding_box(v)
        mins = bv.min(axis=0)
        maxs = bv.max(axis=0)
        dx = float(maxs[0] - mins[0])
        dy = float(maxs[1] - mins[1])
        dz = float(maxs[2] - mins[2])
        return float(math.sqrt(dx * dx + dy * dy + dz * dz))

    setattr(igl, "bounding_box_diagonal", _bounding_box_diagonal)


def _resolve_repo_root(runtime_input: Mapping[str, Any]) -> Path:
    raw = str(runtime_input.get("po_sbr_repo_root", "external/PO-SBR-Python")).strip()
    if raw == "":
        raise ValueError("runtime_input.po_sbr_repo_root must be non-empty when provided")
    repo_root = Path(raw).expanduser()
    if not repo_root.is_absolute():
        repo_root = Path.cwd() / repo_root
    repo_root = repo_root.resolve()
    if not repo_root.exists():
        raise ValueError(f"PO-SBR repo root not found: {repo_root}")
    return repo_root


def _resolve_geometry_path(repo_root: Path, runtime_input: Mapping[str, Any]) -> Path:
    raw = str(runtime_input.get("geometry_path", "geometries/plate.obj")).strip()
    if raw == "":
        raise ValueError("runtime_input.geometry_path must be non-empty")
    geometry_path = Path(raw).expanduser()
    if not geometry_path.is_absolute():
        geometry_path = repo_root / geometry_path
    geometry_path = geometry_path.resolve()
    if not geometry_path.exists():
        raise ValueError(f"PO-SBR geometry not found: {geometry_path}")
    return geometry_path


def _load_po_solver_module(repo_root: Path) -> ModuleType:
    module_path = repo_root / "POsolver.py"
    if not module_path.exists():
        raise ValueError(f"PO-SBR solver module not found: {module_path}")
    spec = importlib.util.spec_from_file_location("avxsim_po_sbr_solver", str(module_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module spec for: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "build") or not hasattr(module, "simulate"):
        raise RuntimeError("POsolver module must define build() and simulate()")
    _apply_po_solver_compat(module)
    return module


def _apply_po_solver_compat(module: ModuleType) -> None:
    shoot_fn = getattr(module, "shoot_and_record", None)
    if not callable(shoot_fn):
        return
    if bool(getattr(shoot_fn, "__avxsim_numrays_cast_compat__", False)):
        return

    def _shoot_and_record_compat(hits_1: Any, ray_pos: Any, ray_dict: Any, numrays: Any) -> Any:
        return shoot_fn(hits_1, ray_pos, ray_dict, int(numrays))

    setattr(_shoot_and_record_compat, "__avxsim_numrays_cast_compat__", True)
    setattr(module, "shoot_and_record", _shoot_and_record_compat)


def _unit_direction_from_angles(phi_deg: float, theta_deg: float) -> Tuple[float, float, float]:
    phi = math.radians(float(phi_deg))
    theta = math.radians(float(theta_deg))
    return (
        float(math.sin(theta) * math.cos(phi)),
        float(math.sin(theta) * math.sin(phi)),
        float(math.cos(theta)),
    )


def _as_obj(payload: Mapping[str, Any], key: str, required: bool = True) -> Dict[str, Any]:
    value = payload.get(key)
    if value is None and not required:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be object")
    return dict(value)


def _parse_complex(value: Any, key_name: str) -> complex:
    if isinstance(value, Mapping):
        return complex(float(value.get("re", 0.0)), float(value.get("im", 0.0)))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) != 2:
            raise ValueError(f"{key_name} list form must be [re, im]")
        return complex(float(value[0]), float(value[1]))
    return complex(float(value), 0.0)

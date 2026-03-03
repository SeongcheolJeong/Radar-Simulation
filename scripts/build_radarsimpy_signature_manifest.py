#!/usr/bin/env python3
"""Build RadarSimPy Phase-1 signature manifest (wrapper/core/reference)."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, Optional, Sequence


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Build RadarSimPy signature manifest covering wrapper signatures, "
            "canonical upstream signatures, native-core mappings, and optional "
            "reference-runtime signatures."
        )
    )
    p.add_argument("--repo-root", default=".")
    p.add_argument("--output-json", required=True)
    p.add_argument("--strict-ready", action="store_true")
    return p.parse_args()


def _load_module(repo_root: Path, module_name: str) -> ModuleType:
    src_root = (repo_root / "src").resolve()
    if not src_root.exists():
        raise FileNotFoundError(f"missing src root: {src_root}")
    src_text = str(src_root)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
    return importlib.import_module(module_name)


def _tuple_of_str(module: ModuleType, attr: str) -> tuple[str, ...]:
    value = getattr(module, attr, None)
    if not isinstance(value, tuple):
        raise ValueError(f"{attr} must be tuple[str, ...]")
    out: List[str] = []
    for row in value:
        if not isinstance(row, str) or row.strip() == "":
            raise ValueError(f"{attr} contains invalid entry: {row!r}")
        out.append(row)
    return tuple(out)


def _safe_signature(fn: Any) -> Optional[str]:
    if fn is None:
        return None
    try:
        return str(inspect.signature(fn))
    except Exception:
        return None


CANONICAL_SIGNATURES: Mapping[str, str] = {
    # Root API
    "radarsimpy.Transmitter": (
        "(f, t, tx_power=0, pulses=1, prp=None, f_offset=None, pn_f=None, pn_power=None, channels=None)"
    ),
    "radarsimpy.Receiver": (
        "(fs, noise_figure=10, rf_gain=0, load_resistor=500, baseband_gain=0, bb_type='complex', channels=None)"
    ),
    "radarsimpy.Radar": (
        "(transmitter, receiver, frame_time=0, location=(0, 0, 0), speed=(0, 0, 0), "
        "rotation=(0, 0, 0), rotation_rate=(0, 0, 0), seed=None, **kwargs)"
    ),
    "radarsimpy.sim_radar": (
        "(radar, targets, density=1, level=None, interf=None, ray_filter=None, "
        "back_propagating=False, device='gpu', log_path=None, dry_run=False)"
    ),
    "radarsimpy.sim_rcs": (
        "(targets, f, inc_phi, inc_theta, inc_pol=[0, 0, 1], obs_phi=None, obs_theta=None, "
        "obs_pol=None, density=1.0)"
    ),
    # Processing API
    "radarsimpy.processing.range_fft": "(data, rwin=None, n=None)",
    "radarsimpy.processing.doppler_fft": "(data, dwin=None, n=None)",
    "radarsimpy.processing.range_doppler_fft": "(data, rwin=None, dwin=None, rn=None, dn=None)",
    "radarsimpy.processing.cfar_ca_1d": (
        "(data, guard, trailing, pfa=1e-05, axis=0, detector='squarelaw', offset=None)"
    ),
    "radarsimpy.processing.cfar_ca_2d": (
        "(data, guard, trailing, pfa=1e-05, detector='squarelaw', offset=None)"
    ),
    "radarsimpy.processing.cfar_os_1d": (
        "(data, guard, trailing, k, pfa=1e-05, axis=0, detector='squarelaw', offset=None)"
    ),
    "radarsimpy.processing.cfar_os_2d": (
        "(data, guard, trailing, k, pfa=1e-05, detector='squarelaw', offset=None)"
    ),
    "radarsimpy.processing.doa_music": (
        "(covmat, nsig, spacing=0.5, scanangles=range(-90, 91))"
    ),
    "radarsimpy.processing.doa_root_music": "(covmat, nsig, spacing=0.5)",
    "radarsimpy.processing.doa_esprit": "(covmat, nsig, spacing=0.5)",
    "radarsimpy.processing.doa_iaa": "(beam_vect, steering_vect, num_it=15, p_init=None)",
    "radarsimpy.processing.doa_bartlett": "(covmat, spacing=0.5, scanangles=range(-90, 91))",
    "radarsimpy.processing.doa_capon": "(covmat, spacing=0.5, scanangles=range(-90, 91))",
    # Tools API
    "radarsimpy.tools.roc_pd": "(pfa, snr, npulses=1, stype='Coherent')",
    "radarsimpy.tools.roc_snr": "(pfa, pd, npulses=1, stype='Coherent')",
}


NATIVE_CORE_MAP: Mapping[str, str] = {
    "range_fft": "core_range_fft",
    "doppler_fft": "core_doppler_fft",
    "range_doppler_fft": "core_range_doppler_fft",
    "cfar_ca_1d": "core_cfar_ca_1d",
    "cfar_ca_2d": "core_cfar_ca_2d",
    "cfar_os_1d": "core_cfar_os_1d",
    "cfar_os_2d": "core_cfar_os_2d",
    "doa_music": "core_doa_music",
    "doa_root_music": "core_doa_root_music",
    "doa_esprit": "core_doa_esprit",
    "doa_iaa": "core_doa_iaa",
    "doa_bartlett": "core_doa_bartlett",
    "doa_capon": "core_doa_capon",
    "roc_pd": "core_roc_pd",
    "roc_snr": "core_roc_snr",
}


def _try_load_reference_module(wrapper: ModuleType) -> tuple[Optional[ModuleType], Optional[str]]:
    try:
        loader = getattr(wrapper, "load_radarsimpy_module", None)
        if not callable(loader):
            return None, "wrapper_missing_load_radarsimpy_module"
        return loader(), None
    except Exception as exc:  # pragma: no cover - env dependent
        return None, str(exc)


def _resolve_reference_callable(
    rs: ModuleType,
    *,
    category: str,
    symbol: str,
) -> Any:
    if category == "root":
        return getattr(rs, symbol, None)
    if category == "processing":
        sub = getattr(rs, "processing", None)
        if sub is None:
            return None
        return getattr(sub, symbol, None)
    if category == "tools":
        sub = getattr(rs, "tools", None)
        if sub is None:
            return None
        return getattr(sub, symbol, None)
    return None


def _entry(
    *,
    symbol: str,
    qualified_symbol: str,
    category: str,
    wrapper_signature: Optional[str],
    canonical_signature: Optional[str],
    native_core_symbol: Optional[str],
    native_core_signature: Optional[str],
    reference_signature: Optional[str],
    wrapper_exported: bool,
) -> Dict[str, Any]:
    return {
        "symbol": str(symbol),
        "qualified_symbol": str(qualified_symbol),
        "category": str(category),
        "wrapper_signature": wrapper_signature,
        "canonical_signature": canonical_signature,
        "native_core_symbol": native_core_symbol,
        "native_core_signature": native_core_signature,
        "reference_signature": reference_signature,
        "wrapper_exported": bool(wrapper_exported),
        "canonical_defined": bool(canonical_signature is not None),
        "has_native_core": bool(native_core_symbol is not None),
        "reference_signature_available": bool(reference_signature is not None),
    }


def _build_rows(
    *,
    wrapper: ModuleType,
    core_processing: ModuleType,
    core_tools: ModuleType,
    reference_module: Optional[ModuleType],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    root_api = _tuple_of_str(wrapper, "RADARSIMPY_ROOT_API")
    processing_api = _tuple_of_str(wrapper, "RADARSIMPY_PROCESSING_API")
    tools_api = _tuple_of_str(wrapper, "RADARSIMPY_TOOLS_API")

    exported_names = {str(v) for v in list(getattr(wrapper, "__all__", []) or [])}

    def _push(
        names: Sequence[str],
        *,
        category: str,
        qualifier: str,
    ) -> None:
        for symbol in names:
            qual = f"{qualifier}{symbol}"
            wrapper_callable = getattr(wrapper, symbol, None)
            wrapper_sig = _safe_signature(wrapper_callable)
            canonical_sig = CANONICAL_SIGNATURES.get(qual)

            native_symbol = NATIVE_CORE_MAP.get(symbol)
            native_sig: Optional[str] = None
            if native_symbol is not None:
                native_callable = getattr(core_processing, native_symbol, None)
                if native_callable is None:
                    native_callable = getattr(core_tools, native_symbol, None)
                native_sig = _safe_signature(native_callable)

            reference_sig: Optional[str] = None
            if reference_module is not None:
                reference_callable = _resolve_reference_callable(
                    reference_module,
                    category=category,
                    symbol=symbol,
                )
                reference_sig = _safe_signature(reference_callable)

            rows.append(
                _entry(
                    symbol=symbol,
                    qualified_symbol=qual,
                    category=category,
                    wrapper_signature=wrapper_sig,
                    canonical_signature=canonical_sig,
                    native_core_symbol=native_symbol,
                    native_core_signature=native_sig,
                    reference_signature=reference_sig,
                    wrapper_exported=(symbol in exported_names),
                )
            )

    _push(root_api, category="root", qualifier="radarsimpy.")
    _push(processing_api, category="processing", qualifier="radarsimpy.processing.")
    _push(tools_api, category="tools", qualifier="radarsimpy.tools.")
    return rows


def main() -> None:
    args = parse_args()
    repo_root = Path(str(args.repo_root)).expanduser().resolve()

    wrapper = _load_module(repo_root, "avxsim.radarsimpy_api")
    core_processing = _load_module(repo_root, "avxsim.radarsimpy_core_processing")
    core_tools = _load_module(repo_root, "avxsim.radarsimpy_core_tools")

    reference_module, reference_error = _try_load_reference_module(wrapper)
    rows = _build_rows(
        wrapper=wrapper,
        core_processing=core_processing,
        core_tools=core_tools,
        reference_module=reference_module,
    )

    total_count = int(len(rows))
    canonical_defined_count = int(sum(1 for row in rows if bool(row["canonical_defined"])))
    native_core_count = int(sum(1 for row in rows if bool(row["has_native_core"])))
    exported_count = int(sum(1 for row in rows if bool(row["wrapper_exported"])))
    reference_signature_available_count = int(
        sum(1 for row in rows if bool(row["reference_signature_available"]))
    )

    processing_tools_rows = [
        row for row in rows if str(row.get("category")) in {"processing", "tools"}
    ]
    phase1_native_ready = bool(all(bool(row.get("has_native_core")) for row in processing_tools_rows))

    report = {
        "report_name": "radarsimpy_signature_manifest",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "api_index_url": str(getattr(wrapper, "API_INDEX_URL", "")),
        "api_index_version": str(getattr(wrapper, "API_INDEX_VERSION", "")),
        "total_count": total_count,
        "canonical_defined_count": canonical_defined_count,
        "native_core_count": native_core_count,
        "exported_count": exported_count,
        "reference_runtime_available": bool(reference_module is not None),
        "reference_runtime_import_error": reference_error,
        "reference_signature_available_count": reference_signature_available_count,
        "phase1_native_ready": phase1_native_ready,
        "ready": bool(
            canonical_defined_count == total_count
            and phase1_native_ready
        ),
        "entries": rows,
    }

    print("RadarSimPy signature manifest")
    print(f"workspace_root={report['workspace_root']}")
    print(f"api_index_version={report['api_index_version']}")
    print(f"ready={report['ready']}")
    print(
        "counts="
        f"total={report['total_count']}, "
        f"canonical_defined={report['canonical_defined_count']}, "
        f"native_core={report['native_core_count']}, "
        f"exported={report['exported_count']}, "
        f"reference_signatures={report['reference_signature_available_count']}"
    )
    print(f"phase1_native_ready={report['phase1_native_ready']}")
    print(f"reference_runtime_available={report['reference_runtime_available']}")

    output_json = Path(str(args.output_json)).expanduser()
    if not output_json.is_absolute():
        output_json = (repo_root / output_json).resolve()
    else:
        output_json = output_json.resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {output_json}")

    if bool(args.strict_ready) and not bool(report["ready"]):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

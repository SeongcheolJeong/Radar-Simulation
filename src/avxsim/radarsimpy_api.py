from __future__ import annotations

import importlib
import os
from types import ModuleType
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .radarsimpy_core_processing import (
    core_cfar_ca_1d,
    core_cfar_ca_2d,
    core_cfar_os_1d,
    core_cfar_os_2d,
    core_doa_bartlett,
    core_doa_capon,
    core_doa_esprit,
    core_doa_iaa,
    core_doa_music,
    core_doa_root_music,
    core_doppler_fft,
    core_range_doppler_fft,
    core_range_fft,
)
from .radarsimpy_core_model import CoreRadar, CoreReceiver, CoreTransmitter
from .radarsimpy_core_simulator import core_sim_radar, core_sim_rcs
from .radarsimpy_core_tools import core_roc_pd, core_roc_snr

API_INDEX_URL = "https://radarsimx.github.io/radarsimpy/api/index.html"
API_INDEX_VERSION = "15.0.1"
RADARSIMPY_LICENSE_FILE_ENV = "RADARSIMPY_LICENSE_FILE"

RADARSIMPY_ROOT_API: Tuple[str, ...] = (
    "Transmitter",
    "Receiver",
    "Radar",
    "sim_radar",
    "sim_rcs",
)
RADARSIMPY_PROCESSING_API: Tuple[str, ...] = (
    "cfar_ca_1d",
    "cfar_ca_2d",
    "cfar_os_1d",
    "cfar_os_2d",
    "doa_bartlett",
    "doa_capon",
    "doa_esprit",
    "doa_iaa",
    "doa_music",
    "doa_root_music",
    "doppler_fft",
    "range_doppler_fft",
    "range_fft",
)
RADARSIMPY_TOOLS_API: Tuple[str, ...] = (
    "roc_pd",
    "roc_snr",
)
RADARSIMPY_EXCLUDED_API: Tuple[str, ...] = ("sim_lidar",)
RADARSIMPY_SUPPORTED_API: Tuple[str, ...] = (
    *RADARSIMPY_ROOT_API,
    *RADARSIMPY_PROCESSING_API,
    *RADARSIMPY_TOOLS_API,
)
_RADARSIMPY_LICENSE_CONFIGURED_PATH: str | None = None


def _configure_radarsimpy_license(module: ModuleType) -> None:
    global _RADARSIMPY_LICENSE_CONFIGURED_PATH
    license_file = str(os.environ.get(RADARSIMPY_LICENSE_FILE_ENV, "")).strip()
    if license_file == "":
        return
    license_path = Path(license_file).expanduser()
    if not license_path.is_absolute():
        license_path = license_path.resolve()
    else:
        license_path = license_path.resolve()
    license_path_text = str(license_path)
    if license_path_text == _RADARSIMPY_LICENSE_CONFIGURED_PATH:
        return
    if not license_path.exists() or (not license_path.is_file()):
        raise RuntimeError(
            f"{RADARSIMPY_LICENSE_FILE_ENV} points to missing file: {license_path_text}"
        )
    set_license = getattr(module, "set_license", None)
    if set_license is None:
        raise RuntimeError("radarsimpy.set_license is unavailable")
    try:
        set_license(license_path_text)
    except Exception as exc:
        raise RuntimeError(f"failed to configure RadarSimPy license from {license_path_text}: {exc}") from exc
    _RADARSIMPY_LICENSE_CONFIGURED_PATH = license_path_text


def _import_radarsimpy_module() -> ModuleType:
    try:
        module = importlib.import_module("radarsimpy")
        _configure_radarsimpy_license(module)
        return module
    except Exception as exc:
        raise RuntimeError(f"missing required RadarSimPy module: {exc}") from exc


def load_radarsimpy_module() -> ModuleType:
    return _import_radarsimpy_module()


def _resolve_root_attr(name: str) -> Any:
    module = _import_radarsimpy_module()
    value = getattr(module, name, None)
    if value is None:
        raise RuntimeError(f"radarsimpy root API missing: {name}")
    return value


def _resolve_root_attr_or_fallback(name: str, fallback: Any) -> Any:
    try:
        return _resolve_root_attr(name)
    except RuntimeError:
        return fallback


def _resolve_submodule_attr(submodule_name: str, attr_name: str) -> Any:
    module = _import_radarsimpy_module()
    submodule = getattr(module, submodule_name, None)
    if submodule is None:
        raise RuntimeError(f"radarsimpy submodule missing: {submodule_name}")
    value = getattr(submodule, attr_name, None)
    if value is None:
        raise RuntimeError(f"radarsimpy API missing: {submodule_name}.{attr_name}")
    return value


def _pop_first(kwargs: Dict[str, Any], names: Tuple[str, ...], *, default: Any = None) -> Any:
    for name in names:
        if name in kwargs:
            return kwargs.pop(name)
    return default


def _resolve_processing_fn_or_fallback(attr_name: str, fallback: Any) -> Any:
    try:
        return _resolve_submodule_attr("processing", attr_name)
    except RuntimeError:
        return fallback


def _resolve_tools_fn_or_fallback(attr_name: str, fallback: Any) -> Any:
    try:
        return _resolve_submodule_attr("tools", attr_name)
    except RuntimeError:
        return fallback


def inspect_radarsimpy_api_coverage(module: ModuleType | None = None) -> Dict[str, Any]:
    rs = module if module is not None else _import_radarsimpy_module()
    missing: List[str] = []
    available: List[str] = []

    for name in RADARSIMPY_ROOT_API:
        if getattr(rs, name, None) is None:
            missing.append(name)
        else:
            available.append(name)

    processing = getattr(rs, "processing", None)
    if processing is None:
        missing.extend([f"processing.{name}" for name in RADARSIMPY_PROCESSING_API])
    else:
        for name in RADARSIMPY_PROCESSING_API:
            qual = f"processing.{name}"
            if getattr(processing, name, None) is None:
                missing.append(qual)
            else:
                available.append(qual)

    tools = getattr(rs, "tools", None)
    if tools is None:
        missing.extend([f"tools.{name}" for name in RADARSIMPY_TOOLS_API])
    else:
        for name in RADARSIMPY_TOOLS_API:
            qual = f"tools.{name}"
            if getattr(tools, name, None) is None:
                missing.append(qual)
            else:
                available.append(qual)

    return {
        "api_index_url": API_INDEX_URL,
        "api_index_version": API_INDEX_VERSION,
        "supported_api": list(RADARSIMPY_SUPPORTED_API),
        "excluded_api": list(RADARSIMPY_EXCLUDED_API),
        "available": sorted(available),
        "missing": sorted(missing),
        "all_supported_available": len(missing) == 0,
    }


def Transmitter(*args: Any, **kwargs: Any) -> Any:
    cls = _resolve_root_attr_or_fallback("Transmitter", CoreTransmitter)
    return cls(*args, **kwargs)


def Receiver(*args: Any, **kwargs: Any) -> Any:
    cls = _resolve_root_attr_or_fallback("Receiver", CoreReceiver)
    return cls(*args, **kwargs)


def Radar(*args: Any, **kwargs: Any) -> Any:
    cls = _resolve_root_attr_or_fallback("Radar", CoreRadar)
    return cls(*args, **kwargs)


def sim_radar(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_root_attr_or_fallback("sim_radar", core_sim_radar)
    return fn(*args, **kwargs)


def sim_rcs(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_root_attr_or_fallback("sim_rcs", core_sim_rcs)
    return fn(*args, **kwargs)


def cfar_ca_1d(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("cfar_ca_1d", core_cfar_ca_1d)
    return fn(*args, **kwargs)


def cfar_ca_2d(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("cfar_ca_2d", core_cfar_ca_2d)
    return fn(*args, **kwargs)


def cfar_os_1d(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("cfar_os_1d", core_cfar_os_1d)
    return fn(*args, **kwargs)


def cfar_os_2d(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("cfar_os_2d", core_cfar_os_2d)
    return fn(*args, **kwargs)


def doa_bartlett(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("doa_bartlett", core_doa_bartlett)
    return fn(*args, **kwargs)


def doa_capon(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("doa_capon", core_doa_capon)
    return fn(*args, **kwargs)


def doa_esprit(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("doa_esprit", core_doa_esprit)
    return fn(*args, **kwargs)


def doa_iaa(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("doa_iaa", core_doa_iaa)
    return fn(*args, **kwargs)


def doa_music(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("doa_music", core_doa_music)
    return fn(*args, **kwargs)


def doa_root_music(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("doa_root_music", core_doa_root_music)
    return fn(*args, **kwargs)


def doppler_fft(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("doppler_fft", core_doppler_fft)
    if fn is core_doppler_fft:
        if len(args) == 0:
            raise TypeError("doppler_fft missing required positional argument: data")
        data = args[0]
        rem = list(args[1:])
        kw = dict(kwargs)
        # Canonical RadarSimPy positional order: (data, dwin=None, n=None)
        if len(rem) > 0 and not any(k in kw for k in ("window", "win", "doppler_window", "dwin")):
            kw["window"] = rem.pop(0)
        if len(rem) > 0 and not any(k in kw for k in ("n", "nfft", "fft_size", "doppler_n", "dn")):
            kw["n"] = rem.pop(0)
        # Optional extension: positional axis as trailing argument
        if len(rem) > 0 and ("axis" not in kw) and ("doppler_axis" not in kw):
            kw["axis"] = rem.pop(0)
        if len(rem) > 0:
            raise TypeError(f"doppler_fft fallback received too many positional args: {len(rem) + 1}")

        axis = _pop_first(kw, ("axis", "doppler_axis"), default=-2)
        n = _pop_first(kw, ("n", "nfft", "fft_size", "doppler_n", "dn"), default=None)
        window = _pop_first(kw, ("window", "win", "doppler_window", "dwin"), default=None)
        if len(kw) > 0:
            raise TypeError(f"doppler_fft fallback got unexpected kwargs: {sorted(kw.keys())}")
        return core_doppler_fft(data, axis=axis, n=n, window=window)
    return fn(*args, **kwargs)


def range_doppler_fft(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("range_doppler_fft", core_range_doppler_fft)
    if fn is core_range_doppler_fft:
        if len(args) == 0:
            raise TypeError("range_doppler_fft missing required positional argument: data")
        data = args[0]
        rem = list(args[1:])
        kw = dict(kwargs)
        # Canonical RadarSimPy positional order: (data, rwin=None, dwin=None, rn=None, dn=None)
        if len(rem) > 0 and not any(k in kw for k in ("range_window", "range_win", "rwin")):
            kw["range_window"] = rem.pop(0)
        if len(rem) > 0 and not any(k in kw for k in ("doppler_window", "doppler_win", "dwin")):
            kw["doppler_window"] = rem.pop(0)
        if len(rem) > 0 and not any(k in kw for k in ("range_n", "range_nfft", "range_fft_size", "rn")):
            kw["range_n"] = rem.pop(0)
        if len(rem) > 0 and not any(
            k in kw for k in ("doppler_n", "doppler_nfft", "doppler_fft_size", "dn")
        ):
            kw["doppler_n"] = rem.pop(0)
        # Optional extensions: explicit axis overrides
        if len(rem) > 0 and ("range_axis" not in kw):
            kw["range_axis"] = rem.pop(0)
        if len(rem) > 0 and ("doppler_axis" not in kw):
            kw["doppler_axis"] = rem.pop(0)
        if len(rem) > 0:
            raise TypeError(
                f"range_doppler_fft fallback received too many positional args: {len(rem) + 1}"
            )

        range_axis = _pop_first(kw, ("range_axis", "rng_axis"), default=-1)
        doppler_axis = _pop_first(kw, ("doppler_axis", "dop_axis"), default=-2)
        range_n = _pop_first(kw, ("range_n", "range_nfft", "range_fft_size", "rn"), default=None)
        doppler_n = _pop_first(
            kw,
            ("doppler_n", "doppler_nfft", "doppler_fft_size", "dn"),
            default=None,
        )
        range_window = _pop_first(kw, ("range_window", "range_win", "rwin"), default=None)
        doppler_window = _pop_first(kw, ("doppler_window", "doppler_win", "dwin"), default=None)
        if len(kw) > 0:
            raise TypeError(f"range_doppler_fft fallback got unexpected kwargs: {sorted(kw.keys())}")
        return core_range_doppler_fft(
            data,
            range_axis=range_axis,
            doppler_axis=doppler_axis,
            range_n=range_n,
            doppler_n=doppler_n,
            range_window=range_window,
            doppler_window=doppler_window,
        )
    return fn(*args, **kwargs)


def range_fft(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_processing_fn_or_fallback("range_fft", core_range_fft)
    if fn is core_range_fft:
        if len(args) == 0:
            raise TypeError("range_fft missing required positional argument: data")
        data = args[0]
        rem = list(args[1:])
        kw = dict(kwargs)
        # Canonical RadarSimPy positional order: (data, rwin=None, n=None)
        if len(rem) > 0 and not any(k in kw for k in ("window", "win", "range_window", "rwin")):
            kw["window"] = rem.pop(0)
        if len(rem) > 0 and not any(k in kw for k in ("n", "nfft", "fft_size", "range_n", "rn")):
            kw["n"] = rem.pop(0)
        # Optional extension: positional axis as trailing argument
        if len(rem) > 0 and ("axis" not in kw) and ("range_axis" not in kw):
            kw["axis"] = rem.pop(0)
        if len(rem) > 0:
            raise TypeError(f"range_fft fallback received too many positional args: {len(rem) + 1}")

        axis = _pop_first(kw, ("axis", "range_axis", "rng_axis"), default=-1)
        n = _pop_first(kw, ("n", "nfft", "fft_size", "range_n", "rn"), default=None)
        window = _pop_first(kw, ("window", "win", "range_window", "rwin"), default=None)
        if len(kw) > 0:
            raise TypeError(f"range_fft fallback got unexpected kwargs: {sorted(kw.keys())}")
        return core_range_fft(data, axis=axis, n=n, window=window)
    return fn(*args, **kwargs)


def roc_pd(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_tools_fn_or_fallback("roc_pd", core_roc_pd)
    return fn(*args, **kwargs)


def roc_snr(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_tools_fn_or_fallback("roc_snr", core_roc_snr)
    return fn(*args, **kwargs)


__all__ = [
    "API_INDEX_URL",
    "API_INDEX_VERSION",
    "RADARSIMPY_ROOT_API",
    "RADARSIMPY_PROCESSING_API",
    "RADARSIMPY_TOOLS_API",
    "RADARSIMPY_EXCLUDED_API",
    "RADARSIMPY_SUPPORTED_API",
    "load_radarsimpy_module",
    "inspect_radarsimpy_api_coverage",
    "Transmitter",
    "Receiver",
    "Radar",
    "sim_radar",
    "sim_rcs",
    "cfar_ca_1d",
    "cfar_ca_2d",
    "cfar_os_1d",
    "cfar_os_2d",
    "doa_bartlett",
    "doa_capon",
    "doa_esprit",
    "doa_iaa",
    "doa_music",
    "doa_root_music",
    "doppler_fft",
    "range_doppler_fft",
    "range_fft",
    "roc_pd",
    "roc_snr",
]

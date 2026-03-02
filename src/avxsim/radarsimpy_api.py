from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any, Dict, List, Tuple

API_INDEX_URL = "https://radarsimx.github.io/radarsimpy/api/index.html"
API_INDEX_VERSION = "15.0.1"

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


def _import_radarsimpy_module() -> ModuleType:
    try:
        return importlib.import_module("radarsimpy")
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


def _resolve_submodule_attr(submodule_name: str, attr_name: str) -> Any:
    module = _import_radarsimpy_module()
    submodule = getattr(module, submodule_name, None)
    if submodule is None:
        raise RuntimeError(f"radarsimpy submodule missing: {submodule_name}")
    value = getattr(submodule, attr_name, None)
    if value is None:
        raise RuntimeError(f"radarsimpy API missing: {submodule_name}.{attr_name}")
    return value


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
    cls = _resolve_root_attr("Transmitter")
    return cls(*args, **kwargs)


def Receiver(*args: Any, **kwargs: Any) -> Any:
    cls = _resolve_root_attr("Receiver")
    return cls(*args, **kwargs)


def Radar(*args: Any, **kwargs: Any) -> Any:
    cls = _resolve_root_attr("Radar")
    return cls(*args, **kwargs)


def sim_radar(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_root_attr("sim_radar")
    return fn(*args, **kwargs)


def sim_rcs(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_root_attr("sim_rcs")
    return fn(*args, **kwargs)


def cfar_ca_1d(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "cfar_ca_1d")
    return fn(*args, **kwargs)


def cfar_ca_2d(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "cfar_ca_2d")
    return fn(*args, **kwargs)


def cfar_os_1d(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "cfar_os_1d")
    return fn(*args, **kwargs)


def cfar_os_2d(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "cfar_os_2d")
    return fn(*args, **kwargs)


def doa_bartlett(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "doa_bartlett")
    return fn(*args, **kwargs)


def doa_capon(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "doa_capon")
    return fn(*args, **kwargs)


def doa_esprit(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "doa_esprit")
    return fn(*args, **kwargs)


def doa_iaa(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "doa_iaa")
    return fn(*args, **kwargs)


def doa_music(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "doa_music")
    return fn(*args, **kwargs)


def doa_root_music(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "doa_root_music")
    return fn(*args, **kwargs)


def doppler_fft(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "doppler_fft")
    return fn(*args, **kwargs)


def range_doppler_fft(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "range_doppler_fft")
    return fn(*args, **kwargs)


def range_fft(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("processing", "range_fft")
    return fn(*args, **kwargs)


def roc_pd(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("tools", "roc_pd")
    return fn(*args, **kwargs)


def roc_snr(*args: Any, **kwargs: Any) -> Any:
    fn = _resolve_submodule_attr("tools", "roc_snr")
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

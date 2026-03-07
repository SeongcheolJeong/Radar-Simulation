import importlib
from types import ModuleType
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from . import radarsimpy_api as rs_api


def detect_runtime_modules(module_names: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for raw_name in module_names:
        name = str(raw_name).strip()
        if name == "":
            continue
        try:
            if name == "radarsimpy":
                module = rs_api.load_radarsimpy_module()
            else:
                module = importlib.import_module(name)
            out[name] = {
                "available": True,
                "module_name": name,
                "module_version": _extract_module_version(module),
            }
        except Exception as exc:  # pragma: no cover - exercised through caller behavior
            out[name] = {
                "available": False,
                "module_name": name,
                "error": f"{type(exc).__name__}: {exc}",
            }
    return out


def load_runtime_provider_callable(provider_spec: str) -> Callable[[Mapping[str, Any]], Mapping[str, Any]]:
    spec = str(provider_spec).strip()
    if spec == "":
        raise ValueError("runtime_provider must be non-empty")
    if ":" not in spec:
        raise ValueError("runtime_provider must be 'module:function'")
    module_name, func_name = spec.split(":", 1)
    module_name = module_name.strip()
    func_name = func_name.strip()
    if module_name == "" or func_name == "":
        raise ValueError("runtime_provider must be 'module:function'")

    module = importlib.import_module(module_name)
    fn = getattr(module, func_name, None)
    if not callable(fn):
        raise ValueError(f"runtime provider function not callable: {provider_spec}")
    return fn


def invoke_runtime_paths_provider(
    provider_spec: str,
    context: Mapping[str, Any],
    required_modules: Optional[Sequence[str]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    modules = tuple(str(x).strip() for x in (required_modules or ()) if str(x).strip() != "")
    module_report = detect_runtime_modules(modules)
    missing = [name for name, report in module_report.items() if not bool(report.get("available", False))]
    if missing:
        raise RuntimeError(f"required runtime modules unavailable: {', '.join(sorted(missing))}")

    fn = load_runtime_provider_callable(provider_spec)
    payload = fn(dict(context))
    if not isinstance(payload, Mapping):
        raise ValueError("runtime provider must return object payload")
    out_payload = dict(payload)
    runtime_info = {
        "provider_spec": str(provider_spec),
        "required_modules": list(modules),
        "module_report": module_report,
    }
    return out_payload, runtime_info


def _extract_module_version(module: ModuleType) -> Optional[str]:
    for key in ("__version__", "version"):
        value = getattr(module, key, None)
        if value is None:
            continue
        text = str(value).strip()
        if text != "":
            return text
    return None

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


DEFAULT_RUNTIME_PRIORITY: Tuple[str, ...] = (
    "sionna_rt_full_runtime",
    "sionna_rt_mitsuba_runtime",
    "sionna_runtime",
    "po_sbr_runtime",
    "radarsimpy_runtime",
)


def load_runtime_probe_summary_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("runtime probe summary must be object")
    return dict(payload)


def save_runtime_blocker_report_json(report: Mapping[str, Any], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(report), indent=2), encoding="utf-8")


def build_runtime_blocker_report(
    probe_summary: Mapping[str, Any],
    runtime_priority: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    runtime_report = probe_summary.get("runtime_report")
    if not isinstance(runtime_report, Mapping):
        raise ValueError("probe summary missing runtime_report object")

    entries: List[Dict[str, Any]] = []
    for name, raw in runtime_report.items():
        if not isinstance(raw, Mapping):
            continue
        info = dict(raw)
        blockers = [str(x) for x in info.get("blockers", [])]
        rec_actions = _recommend_actions(
            runtime_name=str(name),
            runtime_info=info,
            blockers=blockers,
        )
        entries.append(
            {
                "runtime_name": str(name),
                "status": str(info.get("status", "unknown")),
                "ready": bool(info.get("ready", False)),
                "blockers": blockers,
                "recommended_actions": rec_actions,
            }
        )

    ready_set = {str(e["runtime_name"]) for e in entries if bool(e["ready"])}
    priority = tuple(str(x) for x in (runtime_priority or DEFAULT_RUNTIME_PRIORITY))
    next_runtime = None
    for name in priority:
        if name in ready_set:
            next_runtime = name
            break
    if next_runtime is None:
        for e in entries:
            if bool(e["ready"]):
                next_runtime = str(e["runtime_name"])
                break

    blocked_count = int(sum(1 for e in entries if not bool(e["ready"])))
    ready_count = int(sum(1 for e in entries if bool(e["ready"])))
    return {
        "ready_count": ready_count,
        "blocked_count": blocked_count,
        "next_recommended_runtime": next_runtime,
        "entries": entries,
    }


def _recommend_actions(
    runtime_name: str,
    runtime_info: Mapping[str, Any],
    blockers: Sequence[str],
) -> List[str]:
    actions: List[str] = []
    if len(blockers) == 0:
        actions.append("runtime is ready; proceed to real scene pilot")
        return actions

    if "missing_repo" in blockers:
        candidates = runtime_info.get("repo_candidates", [])
        if isinstance(candidates, Sequence) and not isinstance(candidates, (str, bytes)) and len(candidates) > 0:
            actions.append(f"add/cloned repo candidate under workspace: {candidates[0]}")
        else:
            actions.append("add missing external repository")

    if "missing_required_modules" in blockers:
        modules = runtime_info.get("missing_required_modules", [])
        if isinstance(modules, Sequence) and not isinstance(modules, (str, bytes)) and len(modules) > 0:
            module_text = " ".join(str(x) for x in modules)
            actions.append(f"install missing Python modules: {module_text}")
        else:
            actions.append("install missing Python modules")

    for b in blockers:
        if b.startswith("unsupported_platform:"):
            platform_name = b.split(":", 1)[1]
            supported = runtime_info.get("supported_systems", [])
            actions.append(f"run on supported platform {supported} (current: {platform_name})")

    if "missing_nvidia_runtime" in blockers:
        actions.append("requires NVIDIA GPU runtime (`nvidia-smi` unavailable)")

    # runtime-specific hints
    if runtime_name == "sionna_rt_full_runtime":
        actions.append("ensure Dr.Jit LLVM backend is configured (set DRJIT_LIBLLVM_PATH if needed)")
    if runtime_name == "po_sbr_runtime":
        actions.append("install modified `rtxpy` and libigl bindings from PO-SBR reference docs")
    if runtime_name == "radarsimpy_runtime":
        actions.append("install `radarsimpy` package and keep `external/radarsimpy` reference checkout in sync")

    return actions

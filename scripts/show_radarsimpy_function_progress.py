#!/usr/bin/env python3
"""Show function-level RadarSimPy wrapper migration progress."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Sequence, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Report RadarSimPy wrapper function migration progress "
            "(supported/excluded implementation state)."
        )
    )
    p.add_argument("--repo-root", default=".")
    p.add_argument("--output-json", default="")
    p.add_argument("--strict-ready", action="store_true")
    return p.parse_args()


def _load_wrapper_module(repo_root: Path) -> ModuleType:
    module_path = (repo_root / "src" / "avxsim" / "radarsimpy_api.py").resolve()
    if not module_path.exists():
        raise FileNotFoundError(f"missing wrapper module: {module_path}")
    spec = importlib.util.spec_from_file_location("avxsim_radarsimpy_api_standalone", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to build module spec: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tuple_of_str(module: ModuleType, attr: str) -> Tuple[str, ...]:
    value = getattr(module, attr, None)
    if not isinstance(value, tuple):
        raise ValueError(f"{attr} must be tuple[str, ...]")
    out: List[str] = []
    for row in value:
        if not isinstance(row, str) or row.strip() == "":
            raise ValueError(f"{attr} contains non-string entry: {row!r}")
        out.append(row)
    return tuple(out)


def _entry(
    *,
    symbol: str,
    qualified_symbol: str,
    category: str,
    implemented: bool,
    exported: bool,
) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "qualified_symbol": qualified_symbol,
        "category": category,
        "implemented": bool(implemented),
        "exported": bool(exported),
        "status": "ready" if (implemented and exported) else "blocked",
    }


def _build_supported_entries(
    *,
    names: Sequence[str],
    category: str,
    qualifier: str,
    module: ModuleType,
    exported_names: set[str],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for name in names:
        implemented = callable(getattr(module, name, None))
        exported = name in exported_names
        rows.append(
            _entry(
                symbol=name,
                qualified_symbol=f"{qualifier}{name}",
                category=category,
                implemented=implemented,
                exported=exported,
            )
        )
    return rows


def main() -> None:
    args = parse_args()
    repo_root = Path(str(args.repo_root)).expanduser().resolve()
    wrapper = _load_wrapper_module(repo_root)

    root_api = _tuple_of_str(wrapper, "RADARSIMPY_ROOT_API")
    processing_api = _tuple_of_str(wrapper, "RADARSIMPY_PROCESSING_API")
    tools_api = _tuple_of_str(wrapper, "RADARSIMPY_TOOLS_API")
    excluded_api = _tuple_of_str(wrapper, "RADARSIMPY_EXCLUDED_API")
    supported_api = _tuple_of_str(wrapper, "RADARSIMPY_SUPPORTED_API")

    expected_supported = tuple([*root_api, *processing_api, *tools_api])
    if expected_supported != supported_api:
        raise ValueError(
            "RADARSIMPY_SUPPORTED_API mismatch: "
            f"expected={expected_supported}, actual={supported_api}"
        )

    exported_names = set()
    all_exports = getattr(wrapper, "__all__", None)
    if isinstance(all_exports, list):
        exported_names = {str(v) for v in all_exports}

    supported_entries: List[Dict[str, Any]] = []
    supported_entries.extend(
        _build_supported_entries(
            names=root_api,
            category="root",
            qualifier="radarsimpy.",
            module=wrapper,
            exported_names=exported_names,
        )
    )
    supported_entries.extend(
        _build_supported_entries(
            names=processing_api,
            category="processing",
            qualifier="radarsimpy.processing.",
            module=wrapper,
            exported_names=exported_names,
        )
    )
    supported_entries.extend(
        _build_supported_entries(
            names=tools_api,
            category="tools",
            qualifier="radarsimpy.tools.",
            module=wrapper,
            exported_names=exported_names,
        )
    )

    excluded_entries: List[Dict[str, Any]] = []
    for name in excluded_api:
        implemented = callable(getattr(wrapper, name, None))
        exported = name in exported_names
        excluded_entries.append(
            {
                "symbol": name,
                "qualified_symbol": f"radarsimpy.simulator.{name}",
                "category": "excluded",
                "implemented": bool(implemented),
                "exported": bool(exported),
                "status": "blocked" if (implemented or exported) else "ready",
            }
        )

    missing_supported = [row["symbol"] for row in supported_entries if not row["implemented"]]
    unexported_supported = [row["symbol"] for row in supported_entries if not row["exported"]]
    excluded_violations = [
        row["symbol"] for row in excluded_entries if bool(row["implemented"] or row["exported"])
    ]

    report: Dict[str, Any] = {
        "report_name": "radarsimpy_function_progress",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "api_index_url": str(getattr(wrapper, "API_INDEX_URL", "")),
        "api_index_version": str(getattr(wrapper, "API_INDEX_VERSION", "")),
        "supported_count": int(len(supported_entries)),
        "implemented_supported_count": int(len(supported_entries) - len(missing_supported)),
        "excluded_count": int(len(excluded_entries)),
        "missing_supported": missing_supported,
        "unexported_supported": unexported_supported,
        "excluded_violations": excluded_violations,
        "all_supported_implemented": len(missing_supported) == 0,
        "all_supported_exported": len(unexported_supported) == 0,
        "excluded_policy_ok": len(excluded_violations) == 0,
        "ready": bool(
            len(missing_supported) == 0
            and len(unexported_supported) == 0
            and len(excluded_violations) == 0
        ),
        "supported_entries": supported_entries,
        "excluded_entries": excluded_entries,
    }

    print("RadarSimPy function progress")
    print(f"workspace_root={report['workspace_root']}")
    print(f"api_index_version={report['api_index_version']}")
    print(f"ready={report['ready']}")
    print(
        "supported="
        f"{report['implemented_supported_count']}/{report['supported_count']} implemented, "
        f"missing={len(report['missing_supported'])}, "
        f"unexported={len(report['unexported_supported'])}"
    )
    print(
        f"excluded={report['excluded_count']}, excluded_violations={len(report['excluded_violations'])}"
    )
    for row in supported_entries:
        print(f"- {row['qualified_symbol']}: {row['status']}")
    for row in excluded_entries:
        print(f"- {row['qualified_symbol']}: {row['status']} (excluded)")

    out_raw = str(args.output_json).strip()
    if out_raw != "":
        out_path = Path(out_raw).expanduser()
        if not out_path.is_absolute():
            out_path = (repo_root / out_path).resolve()
        else:
            out_path = out_path.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"wrote {out_path}")

    if bool(args.strict_ready) and not bool(report["ready"]):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

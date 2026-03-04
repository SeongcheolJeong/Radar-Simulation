#!/usr/bin/env python3
"""Run strict RadarSimPy production-release readiness in one command."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

RADARSIMPY_LICENSE_FILE_ENV = "RADARSIMPY_LICENSE_FILE"


def _timestamp_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Resolve RadarSimPy license file and run strict production-tier "
            "readiness checkpoint."
        )
    )
    p.add_argument(
        "--output-json",
        default=f"docs/reports/radarsimpy_production_release_gate_{_timestamp_tag()}.json",
        help="Output summary JSON path.",
    )
    p.add_argument(
        "--checkpoint-output-json",
        default="",
        help="Optional readiness checkpoint JSON output path.",
    )
    p.add_argument(
        "--python-bin",
        default="",
        help="Python interpreter for child checkpoint runner.",
    )
    p.add_argument(
        "--license-file",
        default="",
        help=(
            "Explicit RadarSimPy .lic file path. "
            f"When omitted, {RADARSIMPY_LICENSE_FILE_ENV} and --search-root are used."
        ),
    )
    p.add_argument(
        "--search-root",
        action="append",
        default=[],
        help=(
            "Additional root directory to search for license_RadarSimPy*.lic "
            "(repeatable)."
        ),
    )
    p.add_argument(
        "--search-max-depth",
        type=int,
        default=6,
        help="Maximum recursive depth per search root (default: 6).",
    )
    p.add_argument(
        "--trial-package-root",
        default="",
        help="Optional trial package root forwarded to readiness checkpoint.",
    )
    p.add_argument(
        "--libcompat-dir",
        default="",
        help="Optional libcompat directory forwarded to readiness checkpoint.",
    )
    p.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Return 0 even when production gate status is blocked.",
    )
    return p.parse_args()


def _resolve_path(raw: str, *, repo_root: Path) -> Path:
    p = Path(str(raw)).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (repo_root / p).resolve()


def _resolve_python_bin(raw: str, *, repo_root: Path) -> str:
    text = str(raw).strip()
    if text != "":
        p = Path(text).expanduser()
        if p.exists():
            if p.is_absolute():
                return str(p.resolve())
            return str((repo_root / p).resolve())
        return text

    for candidate in (
        repo_root / ".venv" / "bin" / "python",
        repo_root / ".venv-po-sbr" / "bin" / "python",
    ):
        if candidate.exists():
            return str(candidate)
    return str(sys.executable)


def _os_walk_depth_limited(root: Path, *, max_depth: int) -> Iterable[Path]:
    root_resolved = root.resolve()
    root_depth = len(root_resolved.parts)
    for current, dirs, _ in os.walk(str(root_resolved)):
        current_path = Path(current)
        depth = len(current_path.parts) - root_depth
        if depth >= max_depth:
            dirs[:] = []
        yield current_path


def _search_license_files(root: Path, *, max_depth: int) -> List[Path]:
    out: List[Path] = []
    if (not root.exists()) or (not root.is_dir()):
        return out
    for current in _os_walk_depth_limited(root, max_depth=max(0, int(max_depth))):
        for child in current.iterdir():
            if not child.is_file():
                continue
            name = child.name.lower()
            if (not name.startswith("license_radarsimpy")) or (not name.endswith(".lic")):
                continue
            out.append(child.resolve())
    return out


def _dedupe_preserve(paths: Iterable[Path]) -> List[Path]:
    seen: set[str] = set()
    out: List[Path] = []
    for p in paths:
        key = str(p.resolve())
        if key in seen:
            continue
        seen.add(key)
        out.append(p.resolve())
    return out


def _default_search_roots(repo_root: Path) -> List[Path]:
    home = Path.home().resolve()
    return _dedupe_preserve(
        [
            repo_root,
            repo_root / "external",
            home,
            home / "Downloads",
            home / "Desktop",
        ]
    )


def _pick_best_license(candidates: List[Path]) -> Optional[Path]:
    if len(candidates) == 0:
        return None
    ranked = sorted(
        candidates,
        key=lambda p: (float(p.stat().st_mtime), str(p)),
        reverse=True,
    )
    return ranked[0]


def _discover_license_file(
    *,
    repo_root: Path,
    explicit_license_file: str,
    env: Mapping[str, str],
    search_roots_raw: List[str],
    search_max_depth: int,
) -> Dict[str, Any]:
    discovery: Dict[str, Any] = {
        "selected_path": "",
        "selection_source": "",
        "explicit_arg": "",
        "env_value": "",
        "search_roots": [],
        "search_max_depth": int(search_max_depth),
        "candidates": [],
        "errors": [],
    }

    explicit_text = str(explicit_license_file).strip()
    env_text = str(env.get(RADARSIMPY_LICENSE_FILE_ENV, "")).strip()
    discovery["explicit_arg"] = explicit_text
    discovery["env_value"] = env_text

    if explicit_text != "":
        explicit_path = _resolve_path(explicit_text, repo_root=repo_root)
        if explicit_path.exists() and explicit_path.is_file():
            discovery["selected_path"] = str(explicit_path)
            discovery["selection_source"] = "explicit_arg"
            discovery["candidates"] = [str(explicit_path)]
            return discovery
        discovery["errors"].append(f"explicit license file missing: {explicit_path}")
        return discovery

    if env_text != "":
        env_path = _resolve_path(env_text, repo_root=repo_root)
        if env_path.exists() and env_path.is_file():
            discovery["selected_path"] = str(env_path)
            discovery["selection_source"] = "env_var"
            discovery["candidates"] = [str(env_path)]
            return discovery
        discovery["errors"].append(f"env license file missing: {env_path}")

    search_roots: List[Path] = []
    for raw in search_roots_raw:
        text = str(raw).strip()
        if text == "":
            continue
        search_roots.append(_resolve_path(text, repo_root=repo_root))
    if len(search_roots) == 0:
        search_roots = _default_search_roots(repo_root=repo_root)

    search_roots = _dedupe_preserve(search_roots)
    discovery["search_roots"] = [str(p) for p in search_roots]

    candidates: List[Path] = []
    for root in search_roots:
        try:
            candidates.extend(_search_license_files(root, max_depth=search_max_depth))
        except Exception as exc:
            discovery["errors"].append(f"search failed at {root}: {exc}")
    candidates = _dedupe_preserve(candidates)
    discovery["candidates"] = [str(p) for p in candidates]
    best = _pick_best_license(candidates)
    if best is not None:
        discovery["selected_path"] = str(best)
        discovery["selection_source"] = "search"
    return discovery


def _run_cmd(cmd: List[str], *, cwd: Path, env: Mapping[str, str]) -> Dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "cmd": list(cmd),
        "returncode": int(proc.returncode),
        "pass": bool(proc.returncode == 0),
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-80:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-80:]),
    }


def _load_json_if_exists(path: Path) -> Optional[Dict[str, Any]]:
    if (not path.exists()) or (not path.is_file()):
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return payload


def main() -> None:
    args = parse_args()
    repo_root = Path.cwd().resolve()
    summary_path = _resolve_path(str(args.output_json), repo_root=repo_root)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    checkpoint_output_text = str(args.checkpoint_output_json).strip()
    if checkpoint_output_text == "":
        checkpoint_output = summary_path.parent / f"{summary_path.stem}_readiness_checkpoint.json"
    else:
        checkpoint_output = _resolve_path(checkpoint_output_text, repo_root=repo_root)
    checkpoint_output.parent.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = f"src{os.pathsep}{env['PYTHONPATH']}" if "PYTHONPATH" in env else "src"
    python_bin = _resolve_python_bin(str(args.python_bin), repo_root=repo_root)

    discovery = _discover_license_file(
        repo_root=repo_root,
        explicit_license_file=str(args.license_file),
        env=env,
        search_roots_raw=list(args.search_root),
        search_max_depth=int(args.search_max_depth),
    )
    selected_license = str(discovery.get("selected_path", "")).strip()

    blockers: List[str] = []
    checkpoint_run: Dict[str, Any] = {"skipped": False}
    checkpoint_payload: Dict[str, Any] = {}

    if selected_license == "":
        blockers.append("license_file_missing")
        checkpoint_run = {"skipped": True}
    else:
        checkpoint_cmd = [
            python_bin,
            "scripts/run_radarsimpy_readiness_checkpoint.py",
            "--with-real-runtime",
            "--runtime-license-tier",
            "production",
            "--license-file",
            selected_license,
            "--output-json",
            str(checkpoint_output),
        ]
        trial_package_root = str(args.trial_package_root).strip()
        libcompat_dir = str(args.libcompat_dir).strip()
        if trial_package_root != "":
            checkpoint_cmd.extend(["--trial-package-root", trial_package_root])
        if libcompat_dir != "":
            checkpoint_cmd.extend(["--libcompat-dir", libcompat_dir])
        if bool(args.allow_blocked):
            checkpoint_cmd.append("--allow-blocked")
        checkpoint_run = _run_cmd(checkpoint_cmd, cwd=repo_root, env=env)
        checkpoint_payload = _load_json_if_exists(checkpoint_output) or {}
        if checkpoint_payload.get("overall_status") != "ready":
            blockers.append("readiness_checkpoint_blocked")
        if not bool(checkpoint_run.get("pass", False)):
            blockers.append("readiness_checkpoint_returncode_nonzero")

    blockers = sorted(set(blockers))
    production_gate_status = "ready" if len(blockers) == 0 else "blocked"

    report: Dict[str, Any] = {
        "version": 1,
        "report_name": "radarsimpy_production_release_gate",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "production_gate_status": production_gate_status,
        "allow_blocked": bool(args.allow_blocked),
        "license_discovery": discovery,
        "selected_license_file": selected_license,
        "checkpoint_output_json": str(checkpoint_output.resolve()),
        "checkpoint_overall_status": str(checkpoint_payload.get("overall_status", "")),
        "checkpoint_run": checkpoint_run,
        "blockers": blockers,
    }

    summary_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("RadarSimPy production release gate completed.")
    print(f"  production_gate_status: {production_gate_status}")
    print(f"  selected_license_file: {selected_license or '(none)'}")
    print(f"  checkpoint_output_json: {checkpoint_output}")
    print(f"  output_json: {summary_path}")

    if (production_gate_status != "ready") and (not bool(args.allow_blocked)):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

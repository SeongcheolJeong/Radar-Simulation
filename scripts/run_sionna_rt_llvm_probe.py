#!/usr/bin/env python3
import argparse
import json
import os
import site
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Probe DRJIT LLVM shared-library candidates for sionna.rt import")
    p.add_argument("--output-summary-json", required=True, help="Output summary JSON path")
    p.add_argument(
        "--include-non-macos-xcode-sdks",
        action="store_true",
        help="Also include iOS/tvOS/watchOS/etc Xcode SDK libLLVM candidates (off by default)",
    )
    p.add_argument(
        "--extra-candidate",
        action="append",
        default=[],
        help="Additional libLLVM candidate path (repeatable)",
    )
    return p.parse_args()


def _discover_default_candidates(include_non_macos_xcode_sdks: bool = False) -> List[str]:
    candidates: List[str] = []
    env_path = os.environ.get("DRJIT_LIBLLVM_PATH")
    if env_path:
        candidates.append(env_path)

    # llvmlite often ships libllvmlite.dylib, which can still be a useful probe target.
    for site_dir in site.getsitepackages():
        p = Path(site_dir) / "llvmlite" / "binding" / "libllvmlite.dylib"
        if p.exists():
            candidates.append(str(p))

    # Prefer macOS-compatible SDK paths by default to avoid repeated incompatible-platform probes.
    xcode_macos = Path("/Applications/Xcode.app").glob(
        "Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/*/usr/lib/libLLVM.dylib"
    )
    clt_macos = Path("/Library/Developer/CommandLineTools").glob("SDKs/MacOSX*.sdk/usr/lib/libLLVM.dylib")
    candidates.extend(str(p) for p in xcode_macos if p.exists())
    candidates.extend(str(p) for p in clt_macos if p.exists())
    if include_non_macos_xcode_sdks:
        all_xcode = Path("/Applications/Xcode.app").glob(
            "Contents/Developer/Platforms/*/Developer/SDKs/*/usr/lib/libLLVM.dylib"
        )
        candidates.extend(str(p) for p in all_xcode if p.exists())

    # De-dup while preserving order
    dedup: List[str] = []
    seen = set()
    for p in candidates:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        dedup.append(key)
    return dedup


def _run_import_probe(
    python_executable: str,
    candidate_path: Optional[str],
) -> Dict[str, object]:
    env = dict(os.environ)
    if candidate_path is None:
        env.pop("DRJIT_LIBLLVM_PATH", None)
    else:
        env["DRJIT_LIBLLVM_PATH"] = str(candidate_path)

    proc = subprocess.run(
        [
            python_executable,
            "-c",
            "import importlib; import sionna; importlib.import_module('sionna.rt'); print('sionna_rt_import_ok')",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    return {
        "candidate_path": candidate_path,
        "success": bool(proc.returncode == 0),
        "return_code": int(proc.returncode),
        "stdout": str(proc.stdout).strip(),
        "stderr": str(proc.stderr).strip(),
    }


def build_probe_summary(python_executable: str, candidate_paths: Sequence[str]) -> Dict[str, object]:
    results: List[Dict[str, object]] = []

    # Baseline without explicit DRJIT_LIBLLVM_PATH
    results.append(_run_import_probe(python_executable=python_executable, candidate_path=None))

    for path in candidate_paths:
        results.append(_run_import_probe(python_executable=python_executable, candidate_path=str(path)))

    working = [r for r in results if bool(r.get("success"))]
    working_path = working[0].get("candidate_path") if working else None
    return {
        "python_executable": python_executable,
        "candidate_count": int(len(candidate_paths)),
        "probe_count": int(len(results)),
        "success": bool(len(working) > 0),
        "working_libllvm_path": working_path,
        "results": results,
    }


def main() -> None:
    args = parse_args()
    candidates = _discover_default_candidates(
        include_non_macos_xcode_sdks=bool(args.include_non_macos_xcode_sdks)
    )
    for extra in args.extra_candidate:
        text = str(extra).strip()
        if text:
            candidates.append(text)

    dedup: List[str] = []
    seen = set()
    for p in candidates:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        dedup.append(key)
    candidates = dedup

    summary = build_probe_summary(python_executable=sys.executable, candidate_paths=candidates)
    out = Path(args.output_summary_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Sionna RT LLVM probe completed.")
    print(f"  success: {summary['success']}")
    print(f"  working_libllvm_path: {summary['working_libllvm_path']}")
    print(f"  probe_count: {summary['probe_count']}")
    print(f"  output_summary_json: {out}")


if __name__ == "__main__":
    main()

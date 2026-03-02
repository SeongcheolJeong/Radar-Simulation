#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
SEARCH_DIRS = ("src/avxsim", "scripts")
ALLOW_IMPORT_MODULE = {
    Path("src/avxsim/radarsimpy_api.py"),
}


def _iter_py_files() -> Iterable[Path]:
    for rel_dir in SEARCH_DIRS:
        base = ROOT / rel_dir
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            yield path


def _scan_file(path: Path) -> List[Tuple[int, str]]:
    rel = path.resolve().relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tree = ast.parse(text, filename=str(path))
    findings: List[Tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = str(alias.name)
                if name == "radarsimpy" or name.startswith("radarsimpy."):
                    lineno = int(getattr(node, "lineno", 0) or 0)
                    findings.append((lineno, lines[lineno - 1].strip() if lineno > 0 else "import radarsimpy"))
        elif isinstance(node, ast.ImportFrom):
            module = str(getattr(node, "module", "") or "")
            if module == "radarsimpy" or module.startswith("radarsimpy."):
                lineno = int(getattr(node, "lineno", 0) or 0)
                findings.append((lineno, lines[lineno - 1].strip() if lineno > 0 else f"from {module} ..."))
        elif isinstance(node, ast.Call):
            if rel in ALLOW_IMPORT_MODULE:
                continue
            fn_name = None
            if isinstance(node.func, ast.Name):
                fn_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                fn_name = node.func.attr
            if fn_name != "import_module":
                continue
            if len(node.args) <= 0:
                continue
            arg0 = node.args[0]
            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                name = arg0.value.strip()
                if name == "radarsimpy":
                    lineno = int(getattr(node, "lineno", 0) or 0)
                    findings.append((lineno, lines[lineno - 1].strip() if lineno > 0 else "import_module('radarsimpy')"))
    return findings


def run() -> None:
    violations: Dict[Path, List[Tuple[int, str]]] = {}
    for path in _iter_py_files():
        rel = path.resolve().relative_to(ROOT)
        finding = _scan_file(path)
        if finding:
            violations[rel] = finding

    if violations:
        lines: List[str] = ["Found direct RadarSimPy imports outside wrapper entrypoint:"]
        for rel in sorted(violations):
            for lineno, text in violations[rel]:
                lines.append(f"  {rel}:{lineno}: {text}")
        raise AssertionError("\n".join(lines))

    print("validate_radarsimpy_wrapper_entrypoint_guard: pass")


if __name__ == "__main__":
    run()

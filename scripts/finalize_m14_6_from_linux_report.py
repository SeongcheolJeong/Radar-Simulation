#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Dict, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Finalize M14.6 docs/checklists from Linux executed report")
    p.add_argument(
        "--linux-summary-json",
        default="docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json",
        help="Linux strict pilot summary JSON path",
    )
    p.add_argument(
        "--closure-summary-json",
        default="docs/reports/m14_6_closure_readiness_linux.json",
        help="Output closure readiness summary JSON path",
    )
    p.add_argument(
        "--date",
        default=str(date.today()),
        help="Date stamp for final log/outcome entries (YYYY-MM-DD)",
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="Apply markdown updates (without this flag, checker/validator only)",
    )
    p.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path",
    )
    return p.parse_args()


def _run_cmd(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    return subprocess.run(
        [str(Path(sys.executable)), *args],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
    )


def _resolve_path(repo_root: Path, raw_path: str) -> Path:
    p = Path(str(raw_path).strip()).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (repo_root / p).resolve()


def _load_json(path: Path) -> Dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _replace_once_or_already_applied(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise ValueError(f"expected marker not found for {label}")


def _update_markdown_files(
    repo_root: Path,
    linux_summary_json: Path,
    closure_summary_json: Path,
    stamp_date: str,
) -> None:
    exec_plan = repo_root / "docs/01_execution_plan.md"
    replan = repo_root / "docs/88_scene_backend_replan_2026_02_21.md"
    ref_strategy = repo_root / "docs/07_reference_repo_strategy.md"
    validation_log = repo_root / "docs/validation_log.md"

    exec_text = exec_plan.read_text(encoding="utf-8")
    exec_text = _replace_once_or_already_applied(
        exec_text,
        "- [ ] M14.6: `po-sbr` runtime pilot on Linux+NVIDIA environment",
        "- [x] M14.6: `po-sbr` runtime pilot on Linux+NVIDIA environment",
        "execution_plan_m14_6_checkbox",
    )
    immediate_old = (
        "Complete M14.6 on Linux+NVIDIA target by running strict PO-SBR runtime pilot command "
        "(no `--allow-blocked`) and lock `pilot_status=executed` evidence JSON."
    )
    immediate_new = (
        "Start next track: scattering-physics fidelity tuning against measured scenarios "
        "(PO-SBR runtime pilot evidence is now locked)."
    )
    if immediate_old in exec_text:
        exec_text = exec_text.replace(immediate_old, immediate_new, 1)

    outcome_marker = "M14.6 outcome ("
    if outcome_marker not in exec_text:
        exec_text += (
            "\n\n"
            f"M14.6 outcome ({stamp_date}):\n\n"
            "- strict Linux+NVIDIA PO-SBR runtime pilot executed and archived\n"
            f"- executed report: `{linux_summary_json}`\n"
            f"- closure readiness: `{closure_summary_json}` (`ready=true`)\n"
        )
    exec_plan.write_text(exec_text, encoding="utf-8")

    replan_text = replan.read_text(encoding="utf-8")
    replan_text = _replace_once_or_already_applied(
        replan_text,
        "- [ ] M14.6: `po-sbr` runtime pilot (Linux+NVIDIA target)",
        "- [x] M14.6: `po-sbr` runtime pilot (Linux+NVIDIA target)",
        "replan_m14_6_checkbox",
    )
    replan.write_text(replan_text, encoding="utf-8")

    ref_text = ref_strategy.read_text(encoding="utf-8")
    pending_line = (
        "- PO-SBR strict runtime pilot execution on Linux+NVIDIA host "
        "(`pilot_status=executed` evidence pending)"
    )
    done_line = "- PO-SBR strict runtime pilot execution evidence locked on Linux+NVIDIA host"
    ref_text = _replace_once_or_already_applied(
        ref_text,
        pending_line,
        done_line,
        "reference_strategy_m14_6_line",
    )
    ref_strategy.write_text(ref_text, encoding="utf-8")

    log_text = validation_log.read_text(encoding="utf-8")
    final_header = "## PO-SBR Runtime Pilot Closure (M14.6)"
    if final_header not in log_text:
        log_text += (
            "\n\n"
            f"{final_header}\n\n"
            f"- Date: {stamp_date}\n"
            "- Command: "
            f"`PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/finalize_m14_6_from_linux_report.py "
            f"--linux-summary-json {linux_summary_json} --closure-summary-json {closure_summary_json} --apply`\n"
            "- Result: pass\n"
            "- Notes:\n"
            "  - Linux strict runtime pilot report validated (`pilot_status=executed`)\n"
            "  - closure readiness switched to `ready=true`\n"
        )
    validation_log.write_text(log_text, encoding="utf-8")


def _check_ready(repo_root: Path, linux_summary_json: Path, closure_summary_json: Path) -> Tuple[bool, Dict[str, object]]:
    readiness_proc = _run_cmd(
        repo_root=repo_root,
        args=[
            "scripts/run_m14_6_closure_readiness.py",
            "--linux-summary-json",
            str(linux_summary_json),
            "--output-summary-json",
            str(closure_summary_json),
        ],
    )
    if readiness_proc.returncode != 0:
        raise RuntimeError(
            "closure readiness command failed:\n"
            f"stdout:\n{readiness_proc.stdout}\n"
            f"stderr:\n{readiness_proc.stderr}"
        )
    readiness = _load_json(closure_summary_json)
    ready = bool(readiness.get("ready", False))
    return ready, readiness


def _validate_executed_report(repo_root: Path, linux_summary_json: Path) -> None:
    proc = _run_cmd(
        repo_root=repo_root,
        args=[
            "scripts/validate_scene_runtime_po_sbr_executed_report.py",
            "--summary-json",
            str(linux_summary_json),
        ],
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "executed report validator failed:\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    linux_summary_json = _resolve_path(repo_root, str(args.linux_summary_json))
    closure_summary_json = _resolve_path(repo_root, str(args.closure_summary_json))
    stamp_date = str(args.date).strip()

    ready, readiness = _check_ready(
        repo_root=repo_root,
        linux_summary_json=linux_summary_json,
        closure_summary_json=closure_summary_json,
    )
    if not ready:
        print("M14.6 finalize check: not ready")
        print(f"  missing_items: {readiness.get('missing_items')}")
        print(f"  linux_summary_json: {linux_summary_json}")
        print(f"  closure_summary_json: {closure_summary_json}")
        raise SystemExit(2)

    _validate_executed_report(repo_root=repo_root, linux_summary_json=linux_summary_json)
    print("M14.6 finalize check: ready")
    print(f"  linux_summary_json: {linux_summary_json}")
    print(f"  closure_summary_json: {closure_summary_json}")

    if not bool(args.apply):
        print("No doc updates applied (use --apply to finalize markdown/checklists).")
        return

    _update_markdown_files(
        repo_root=repo_root,
        linux_summary_json=linux_summary_json,
        closure_summary_json=closure_summary_json,
        stamp_date=stamp_date,
    )
    print("M14.6 finalize apply: completed")


if __name__ == "__main__":
    main()

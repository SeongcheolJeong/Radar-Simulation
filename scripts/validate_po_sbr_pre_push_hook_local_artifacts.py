#!/usr/bin/env python3
"""Validate pre-push hook local-artifact mode does not modify tracked reports."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List


TRACKED_REPORTS = [
    "docs/reports/po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json",
    "docs/reports/po_sbr_operator_handoff_closure_2026_03_01.json",
    "docs/reports/po_sbr_post_change_gate_2026_03_01.json",
    "docs/reports/po_sbr_progress_snapshot_2026_03_01.json",
]

HOOK_REPORTS = {
    "post_change_gate": ".git/po_sbr_post_change_gate_hook_latest.json",
    "merged_checkpoint": ".git/po_sbr_physical_full_track_merged_checkpoint_hook_latest.json",
    "operator_handoff_closure": ".git/po_sbr_operator_handoff_closure_hook_latest.json",
    "avx_developer_gate": ".git/po_sbr_avx_developer_gate_hook_latest.json",
    "avx_developer_gate_matrix": ".git/avx_export_benchmark_matrix_hook_latest/summary.json",
    "progress_snapshot": ".git/po_sbr_progress_snapshot_hook_latest.json",
}


def _run(repo_root: Path, args: List[str]) -> str:
    out = subprocess.check_output(args, cwd=str(repo_root), text=True)
    return out.strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load_json(path: Path) -> Dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _simulate_hook(
    repo_root: Path,
    hook_path: Path,
    stdin_line: str,
    extra_env: Dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(hook_path)],
        cwd=str(repo_root),
        input=stdin_line,
        text=True,
        capture_output=True,
        env={**os.environ, **extra_env},
        check=False,
    )


def _require_contains(text: str, token: str, label: str, proc: subprocess.CompletedProcess[str]) -> None:
    if token not in text:
        raise RuntimeError(
            f"{label} missing expected log token: {token}\n"
            f"stdout={proc.stdout}\n"
            f"stderr={proc.stderr}"
        )


def _require_absent(text: str, token: str, label: str, proc: subprocess.CompletedProcess[str]) -> None:
    if token in text:
        raise RuntimeError(
            f"{label} unexpectedly contained log token: {token}\n"
            f"stdout={proc.stdout}\n"
            f"stderr={proc.stderr}"
        )


def _assert_progress_skipped(path: Path, label: str) -> None:
    payload = _load_json(path)
    if str(payload.get("report_name", "")) != "po_sbr_progress_snapshot":
        raise RuntimeError(f"{label} progress artifact report_name mismatch")
    if str(payload.get("hook_progress_snapshot_status", "")) != "skipped":
        raise RuntimeError(f"{label} progress artifact status is not skipped")
    if payload.get("overall_ready", "not-null") is not None:
        raise RuntimeError(f"{label} progress artifact overall_ready must be null")


def _assert_progress_ready(path: Path, label: str) -> None:
    payload = _load_json(path)
    if str(payload.get("report_name", "")) != "po_sbr_progress_snapshot":
        raise RuntimeError(f"{label} progress artifact report_name mismatch")
    if not bool(payload.get("overall_ready", False)):
        raise RuntimeError(f"{label} progress artifact overall_ready is not true")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    hook_path = repo_root / ".githooks/pre-push"
    if not hook_path.exists():
        raise FileNotFoundError(f"missing pre-push hook: {hook_path}")

    tracked_paths = [repo_root / rel for rel in TRACKED_REPORTS]
    for path in tracked_paths:
        if not path.exists():
            raise FileNotFoundError(f"missing tracked report: {path}")

    before = {str(path): _sha256(path) for path in tracked_paths}

    # Seed hook checkpoint input so hook self-test can run without re-generating
    # full-track artifacts in sandbox-restricted environments.
    merged_src = repo_root / TRACKED_REPORTS[0]
    merged_dst = repo_root / HOOK_REPORTS["merged_checkpoint"]
    merged_dst.parent.mkdir(parents=True, exist_ok=True)
    merged_dst.write_text(merged_src.read_text(encoding="utf-8"), encoding="utf-8")

    branch = _run(repo_root, ["git", "branch", "--show-current"])
    head = _run(repo_root, ["git", "rev-parse", "HEAD"])
    base = _run(repo_root, ["git", "rev-parse", "HEAD~1"])
    stdin_line = (
        f"refs/heads/{branch} {head} "
        f"refs/heads/{branch} {base}\n"
    )

    common_env = {
        "PO_SBR_SKIP_WEB_E2E_VALIDATOR": "1",
        "PO_SBR_SKIP_MERGED_FULL_TRACK_VERIFIER": "1",
    }

    # Case A: both-skip path should emit both skip logs and skipped progress artifact.
    progress_path = repo_root / HOOK_REPORTS["progress_snapshot"]
    if progress_path.exists():
        progress_path.unlink()
    proc_skip_both = _simulate_hook(
        repo_root=repo_root,
        hook_path=hook_path,
        stdin_line=stdin_line,
        extra_env={
            **common_env,
            "PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR": "1",
            "PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR": "1",
            "PO_SBR_SKIP_PROGRESS_SNAPSHOT": "1",
        },
    )
    if proc_skip_both.returncode != 0:
        raise RuntimeError(
            "pre-push hook both-skip simulation failed:\n"
            f"return_code={proc_skip_both.returncode}\n"
            f"stdout={proc_skip_both.stdout}\n"
            f"stderr={proc_skip_both.stderr}"
        )
    stdout_skip_both = proc_skip_both.stdout or ""
    _require_contains(
        stdout_skip_both,
        "skip post-change deterministic validator (PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR=1)",
        "pre-push both-skip",
        proc_skip_both,
    )
    _require_contains(
        stdout_skip_both,
        "skip strict progress snapshot (PO_SBR_SKIP_PROGRESS_SNAPSHOT=1)",
        "pre-push both-skip",
        proc_skip_both,
    )
    _require_contains(
        stdout_skip_both,
        "skip operator-closure report deterministic validator (PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR=1)",
        "pre-push both-skip",
        proc_skip_both,
    )
    _require_contains(
        stdout_skip_both,
        "[pre-push] strict progress snapshot skipped artifact:",
        "pre-push both-skip",
        proc_skip_both,
    )
    _require_absent(
        stdout_skip_both,
        "[pre-push] validate post-change deterministic gate",
        "pre-push both-skip",
        proc_skip_both,
    )
    _require_absent(
        stdout_skip_both,
        "[pre-push] validate operator-closure report deterministic runner",
        "pre-push both-skip",
        proc_skip_both,
    )
    _require_absent(
        stdout_skip_both,
        "[pre-push] generate strict progress snapshot",
        "pre-push both-skip",
        proc_skip_both,
    )
    if not progress_path.exists():
        raise RuntimeError(
            "pre-push hook both-skip did not generate strict progress skipped artifact:\n"
            f"{progress_path}"
        )
    _assert_progress_skipped(progress_path, "pre-push both-skip")

    # Case B: post-change-skip only should still generate strict progress snapshot artifact.
    if progress_path.exists():
        progress_path.unlink()
    proc_skip_post_only = _simulate_hook(
        repo_root=repo_root,
        hook_path=hook_path,
        stdin_line=stdin_line,
        extra_env={
            **common_env,
            "PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR": "1",
        },
    )
    if proc_skip_post_only.returncode != 0:
        raise RuntimeError(
            "pre-push hook post-change-skip simulation failed:\n"
            f"return_code={proc_skip_post_only.returncode}\n"
            f"stdout={proc_skip_post_only.stdout}\n"
            f"stderr={proc_skip_post_only.stderr}"
        )
    stdout_skip_post_only = proc_skip_post_only.stdout or ""
    _require_contains(
        stdout_skip_post_only,
        "skip post-change deterministic validator (PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR=1)",
        "pre-push post-change-skip",
        proc_skip_post_only,
    )
    _require_contains(
        stdout_skip_post_only,
        "[pre-push] generate strict progress snapshot",
        "pre-push post-change-skip",
        proc_skip_post_only,
    )
    _require_contains(
        stdout_skip_post_only,
        "[pre-push] validate operator-closure report deterministic runner",
        "pre-push post-change-skip",
        proc_skip_post_only,
    )
    _require_contains(
        stdout_skip_post_only,
        "validate_run_po_sbr_operator_handoff_closure_report: pass",
        "pre-push post-change-skip",
        proc_skip_post_only,
    )
    _require_contains(
        stdout_skip_post_only,
        "[pre-push] strict progress snapshot:",
        "pre-push post-change-skip",
        proc_skip_post_only,
    )
    _require_absent(
        stdout_skip_post_only,
        "[pre-push] validate post-change deterministic gate",
        "pre-push post-change-skip",
        proc_skip_post_only,
    )
    _require_absent(
        stdout_skip_post_only,
        "skip strict progress snapshot (PO_SBR_SKIP_PROGRESS_SNAPSHOT=1)",
        "pre-push post-change-skip",
        proc_skip_post_only,
    )
    _require_absent(
        stdout_skip_post_only,
        "skip operator-closure report deterministic validator (PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR=1)",
        "pre-push post-change-skip",
        proc_skip_post_only,
    )
    if not progress_path.exists():
        raise RuntimeError(
            "pre-push hook post-change-skip did not generate strict progress artifact:\n"
            f"{progress_path}"
        )
    _assert_progress_ready(progress_path, "pre-push post-change-skip")

    # Case C: progress-skip only should still execute post-change deterministic validator.
    if progress_path.exists():
        progress_path.unlink()
    proc_skip_progress_only = _simulate_hook(
        repo_root=repo_root,
        hook_path=hook_path,
        stdin_line=stdin_line,
        extra_env={
            **common_env,
            "PO_SBR_SKIP_PROGRESS_SNAPSHOT": "1",
        },
    )
    if proc_skip_progress_only.returncode != 0:
        raise RuntimeError(
            "pre-push hook progress-skip simulation failed:\n"
            f"return_code={proc_skip_progress_only.returncode}\n"
            f"stdout={proc_skip_progress_only.stdout}\n"
            f"stderr={proc_skip_progress_only.stderr}"
        )
    stdout_skip_progress_only = proc_skip_progress_only.stdout or ""
    _require_contains(
        stdout_skip_progress_only,
        "[pre-push] validate post-change deterministic gate",
        "pre-push progress-skip",
        proc_skip_progress_only,
    )
    _require_contains(
        stdout_skip_progress_only,
        "[pre-push] validate operator-closure report deterministic runner",
        "pre-push progress-skip",
        proc_skip_progress_only,
    )
    _require_contains(
        stdout_skip_progress_only,
        "validate_run_po_sbr_operator_handoff_closure_report: pass",
        "pre-push progress-skip",
        proc_skip_progress_only,
    )
    _require_contains(
        stdout_skip_progress_only,
        "skip strict progress snapshot (PO_SBR_SKIP_PROGRESS_SNAPSHOT=1)",
        "pre-push progress-skip",
        proc_skip_progress_only,
    )
    _require_contains(
        stdout_skip_progress_only,
        "[pre-push] strict progress snapshot skipped artifact:",
        "pre-push progress-skip",
        proc_skip_progress_only,
    )
    _require_absent(
        stdout_skip_progress_only,
        "[pre-push] generate strict progress snapshot",
        "pre-push progress-skip",
        proc_skip_progress_only,
    )
    _require_absent(
        stdout_skip_progress_only,
        "skip post-change deterministic validator (PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR=1)",
        "pre-push progress-skip",
        proc_skip_progress_only,
    )
    _require_absent(
        stdout_skip_progress_only,
        "skip operator-closure report deterministic validator (PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR=1)",
        "pre-push progress-skip",
        proc_skip_progress_only,
    )
    if not progress_path.exists():
        raise RuntimeError(
            "pre-push hook progress-skip did not generate strict progress skipped artifact:\n"
            f"{progress_path}"
        )
    _assert_progress_skipped(progress_path, "pre-push progress-skip")

    # Case D: closure-report-skip only should still execute post-change validator and strict progress snapshot.
    if progress_path.exists():
        progress_path.unlink()
    proc_skip_closure_only = _simulate_hook(
        repo_root=repo_root,
        hook_path=hook_path,
        stdin_line=stdin_line,
        extra_env={
            **common_env,
            "PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR": "1",
        },
    )
    if proc_skip_closure_only.returncode != 0:
        raise RuntimeError(
            "pre-push hook closure-report-skip simulation failed:\n"
            f"return_code={proc_skip_closure_only.returncode}\n"
            f"stdout={proc_skip_closure_only.stdout}\n"
            f"stderr={proc_skip_closure_only.stderr}"
        )
    stdout_skip_closure_only = proc_skip_closure_only.stdout or ""
    _require_contains(
        stdout_skip_closure_only,
        "[pre-push] validate post-change deterministic gate",
        "pre-push closure-report-skip",
        proc_skip_closure_only,
    )
    _require_contains(
        stdout_skip_closure_only,
        "skip operator-closure report deterministic validator (PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR=1)",
        "pre-push closure-report-skip",
        proc_skip_closure_only,
    )
    _require_contains(
        stdout_skip_closure_only,
        "[pre-push] generate strict progress snapshot",
        "pre-push closure-report-skip",
        proc_skip_closure_only,
    )
    _require_contains(
        stdout_skip_closure_only,
        "[pre-push] strict progress snapshot:",
        "pre-push closure-report-skip",
        proc_skip_closure_only,
    )
    _require_absent(
        stdout_skip_closure_only,
        "[pre-push] validate operator-closure report deterministic runner",
        "pre-push closure-report-skip",
        proc_skip_closure_only,
    )
    _require_absent(
        stdout_skip_closure_only,
        "validate_run_po_sbr_operator_handoff_closure_report: pass",
        "pre-push closure-report-skip",
        proc_skip_closure_only,
    )
    _require_absent(
        stdout_skip_closure_only,
        "skip post-change deterministic validator (PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR=1)",
        "pre-push closure-report-skip",
        proc_skip_closure_only,
    )
    _require_absent(
        stdout_skip_closure_only,
        "skip strict progress snapshot (PO_SBR_SKIP_PROGRESS_SNAPSHOT=1)",
        "pre-push closure-report-skip",
        proc_skip_closure_only,
    )
    if not progress_path.exists():
        raise RuntimeError(
            "pre-push hook closure-report-skip did not generate strict progress artifact:\n"
            f"{progress_path}"
        )
    _assert_progress_ready(progress_path, "pre-push closure-report-skip")

    # Case E: default-mode path should execute deterministic validators and emit strict progress artifact.
    if progress_path.exists():
        progress_path.unlink()
    proc_default = _simulate_hook(
        repo_root=repo_root,
        hook_path=hook_path,
        stdin_line=stdin_line,
        extra_env=common_env,
    )
    if proc_default.returncode != 0:
        raise RuntimeError(
            "pre-push hook default-mode simulation failed:\n"
            f"return_code={proc_default.returncode}\n"
            f"stdout={proc_default.stdout}\n"
            f"stderr={proc_default.stderr}"
        )
    stdout_default = proc_default.stdout or ""
    _require_contains(
        stdout_default,
        "[pre-push] validate post-change deterministic gate",
        "pre-push default-mode",
        proc_default,
    )
    _require_contains(
        stdout_default,
        "[pre-push] validate operator-closure report deterministic runner",
        "pre-push default-mode",
        proc_default,
    )
    _require_contains(
        stdout_default,
        "validate_run_po_sbr_operator_handoff_closure_report: pass",
        "pre-push default-mode",
        proc_default,
    )
    _require_contains(
        stdout_default,
        "[pre-push] generate strict progress snapshot",
        "pre-push default-mode",
        proc_default,
    )
    _require_contains(
        stdout_default,
        "[pre-push] strict progress snapshot:",
        "pre-push default-mode",
        proc_default,
    )
    _require_absent(
        stdout_default,
        "skip post-change deterministic validator (PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR=1)",
        "pre-push default-mode",
        proc_default,
    )
    _require_absent(
        stdout_default,
        "skip strict progress snapshot (PO_SBR_SKIP_PROGRESS_SNAPSHOT=1)",
        "pre-push default-mode",
        proc_default,
    )
    _require_absent(
        stdout_default,
        "skip operator-closure report deterministic validator (PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR=1)",
        "pre-push default-mode",
        proc_default,
    )
    if not progress_path.exists():
        raise RuntimeError(
            "pre-push hook default-mode did not generate strict progress artifact:\n"
            f"{progress_path}"
        )
    _assert_progress_ready(progress_path, "pre-push default-mode")

    after = {str(path): _sha256(path) for path in tracked_paths}
    changed = [
        path for path in sorted(before.keys())
        if before[path] != after[path]
    ]
    if changed:
        joined = "\n".join(changed)
        raise RuntimeError(
            "tracked reports were modified by hook run:\n"
            f"{joined}"
        )

    post_change_path = repo_root / HOOK_REPORTS["post_change_gate"]
    merged_path = repo_root / HOOK_REPORTS["merged_checkpoint"]
    closure_path = repo_root / HOOK_REPORTS["operator_handoff_closure"]
    avx_gate_path = repo_root / HOOK_REPORTS["avx_developer_gate"]
    avx_gate_matrix_path = repo_root / HOOK_REPORTS["avx_developer_gate_matrix"]
    for path in (
        post_change_path,
        merged_path,
        closure_path,
        avx_gate_path,
        avx_gate_matrix_path,
        progress_path,
    ):
        if not path.exists():
            raise FileNotFoundError(f"missing hook artifact: {path}")

    post_change = _load_json(post_change_path)
    merged = _load_json(merged_path)
    closure = _load_json(closure_path)
    avx_gate = _load_json(avx_gate_path)
    avx_gate_matrix = _load_json(avx_gate_matrix_path)
    progress = _load_json(progress_path)

    if str(post_change.get("overall_status", "")) != "ready":
        raise RuntimeError("hook post-change gate overall_status is not ready")
    if str(post_change.get("closure_status", "")) not in {"pass", "skipped"}:
        raise RuntimeError("hook post-change gate closure_status is not pass/skipped")
    if not bool(merged.get("ready", False)):
        raise RuntimeError("hook merged checkpoint ready=false")
    if str(closure.get("overall_status", "")) != "ready":
        raise RuntimeError("hook closure overall_status is not ready")
    em_policy = closure.get("em_solver_packaging_policy")
    if not isinstance(em_policy, dict):
        raise RuntimeError("hook closure em_solver_packaging_policy missing")
    if str(em_policy.get("validator_status", "")) not in {"pass", "skipped"}:
        raise RuntimeError("hook closure em_solver_packaging_policy.validator_status is not pass/skipped")
    em_policy_json = Path(str(em_policy.get("policy_json", "")).strip()).expanduser().resolve()
    em_reference_locks_md = (
        Path(str(em_policy.get("reference_locks_md", "")).strip()).expanduser().resolve()
    )
    if not em_policy_json.exists():
        raise RuntimeError(f"hook closure EM policy json missing: {em_policy_json}")
    if not em_reference_locks_md.exists():
        raise RuntimeError(f"hook closure EM reference-locks markdown missing: {em_reference_locks_md}")
    if str(avx_gate.get("developer_gate_status", "")) != "ready":
        raise RuntimeError("hook avx developer gate status is not ready")
    if str(avx_gate_matrix.get("report_name", "")) != "avx_export_benchmark_matrix_summary":
        raise RuntimeError("hook avx matrix report_name mismatch")
    counts = avx_gate_matrix.get("counts")
    if not isinstance(counts, dict):
        raise RuntimeError("hook avx matrix counts missing")
    if int(counts.get("physics_worse_count", 0)) != 0:
        raise RuntimeError("hook avx matrix physics_worse_count is not zero")
    if str(progress.get("report_name", "")) != "po_sbr_progress_snapshot":
        raise RuntimeError("hook progress snapshot report_name mismatch")
    if not bool(progress.get("overall_ready", False)):
        raise RuntimeError("hook progress snapshot overall_ready is not true")

    print("validate_po_sbr_pre_push_hook_local_artifacts: pass")
    print(f"  simulated_branch: {branch}")
    print(f"  simulated_head: {head}")
    print(f"  simulated_base: {base}")
    print(f"  hook_post_change_json: {post_change_path}")
    print(f"  hook_merged_checkpoint_json: {merged_path}")
    print(f"  hook_closure_json: {closure_path}")
    print(f"  hook_avx_developer_gate_json: {avx_gate_path}")
    print(f"  hook_avx_developer_gate_matrix_json: {avx_gate_matrix_path}")
    print(f"  hook_progress_snapshot_json: {progress_path}")
    print("  hook_skip_mode_matrix_verified: true")
    print("  hook_closure_report_skip_only_verified: true")
    print("  hook_skip_mode_verified: true")
    print("  tracked_report_changes: 0")


if __name__ == "__main__":
    main()

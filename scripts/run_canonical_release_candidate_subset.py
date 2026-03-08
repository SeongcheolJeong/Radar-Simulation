#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run the canonical release-candidate validation subset and emit one summary JSON."
        )
    )
    p.add_argument(
        "--output-json",
        default="docs/reports/canonical_release_candidate_subset_latest.json",
        help="Summary JSON path.",
    )
    p.add_argument(
        "--python-bin",
        default="",
        help="Optional Python binary to use for Python-based steps.",
    )
    p.add_argument(
        "--with-sionna",
        action="store_true",
        help="Include the optional HF-1 Sionna-style RT parity step.",
    )
    p.add_argument(
        "--playwright-browsers-path",
        default="/tmp/pw-browsers",
        help="Playwright browser path for FE-1.",
    )
    p.add_argument(
        "--allow-failures",
        action="store_true",
        help="Return zero even when one or more steps fail.",
    )
    return p.parse_args()


def _resolve_output_json(raw: str, repo_root: Path) -> Path:
    p = Path(str(raw).strip() or "docs/reports/canonical_release_candidate_subset_latest.json").expanduser()
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    else:
        p = p.resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _resolve_python_bin(raw: str, repo_root: Path) -> str:
    text = str(raw).strip()
    if text:
        p = Path(text).expanduser()
        if p.exists():
            return str(p.resolve())
        return text
    candidate = repo_root / ".venv" / "bin" / "python"
    if candidate.exists():
        return str(candidate)
    return str(sys.executable)


def _run(cmd: List[str], *, cwd: Path, env: Mapping[str, str]) -> Dict[str, Any]:
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
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-120:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-120:]),
    }


def _step(
    *,
    step_id: str,
    description: str,
    cmd: List[str],
    cwd: Path,
    env: Mapping[str, str],
    refreshed_evidence: List[str],
) -> Dict[str, Any]:
    run = _run(cmd, cwd=cwd, env=env)
    return {
        "step_id": step_id,
        "description": description,
        "run": run,
        "refreshed_evidence": list(refreshed_evidence),
    }


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    out_json = _resolve_output_json(args.output_json, repo_root=repo_root)
    py = _resolve_python_bin(args.python_bin, repo_root=repo_root)

    base_env = dict(os.environ)
    base_env["PYTHONPATH"] = f"src{os.pathsep}{base_env['PYTHONPATH']}" if "PYTHONPATH" in base_env else "src"

    steps: List[Dict[str, Any]] = []

    steps.append(
        _step(
            step_id="FE-1A",
            description="frontend/backend API orchestrator health",
            cmd=[py, "scripts/validate_web_e2e_orchestrator_api.py"],
            cwd=repo_root,
            env=base_env,
            refreshed_evidence=["docs/reports/frontend_quickstart_v1.json"],
        )
    )

    fe_env = dict(base_env)
    fe_env["PLAYWRIGHT_BROWSERS_PATH"] = str(args.playwright_browsers_path)
    steps.append(
        _step(
            step_id="FE-1B",
            description="Graph Lab browser/operator E2E",
            cmd=[
                py,
                "scripts/validate_graph_lab_playwright_e2e.py",
                "--require-playwright",
                "--output-json",
                "docs/reports/graph_lab_playwright_e2e_latest.json",
            ],
            cwd=repo_root,
            env=fe_env,
            refreshed_evidence=[
                "docs/reports/graph_lab_playwright_e2e_latest.json",
                "docs/reports/graph_lab_playwright_snapshots/latest/",
            ],
        )
    )

    steps.append(
        _step(
            step_id="FE-2",
            description="frontend runtime payload -> provider info contract",
            cmd=[
                py,
                "scripts/validate_frontend_runtime_payload_provider_info_optional.py",
                "--require-runtime",
                "--output-json",
                "docs/reports/frontend_runtime_payload_provider_info_optional_latest.json",
            ],
            cwd=repo_root,
            env=base_env,
            refreshed_evidence=[
                "docs/reports/frontend_runtime_payload_provider_info_optional_latest.json",
            ],
        )
    )

    steps.append(
        _step(
            step_id="RS-1",
            description="trial-runtime layered parity suite",
            cmd=[
                py,
                "scripts/run_radarsimpy_layered_parity_suite.py",
                "--output-json",
                "docs/reports/radarsimpy_layered_parity_suite_trial_latest.json",
                "--trial-output-json",
                "docs/reports/radarsimpy_layered_parity_trial_latest.json",
                "--require-runtime-trial",
            ],
            cwd=repo_root,
            env=base_env,
            refreshed_evidence=[
                "docs/reports/radarsimpy_layered_parity_suite_trial_latest.json",
                "docs/reports/radarsimpy_layered_parity_trial_latest.json",
            ],
        )
    )

    if bool(args.with_sionna):
        steps.append(
            _step(
                step_id="HF-1",
                description="Sionna-style RT parity report",
                cmd=[
                    py,
                    "scripts/run_scene_backend_parity_sionna_rt.py",
                    "--output-json",
                    "docs/reports/scene_backend_parity_sionna_rt_latest.json",
                ],
                cwd=repo_root,
                env=base_env,
                refreshed_evidence=[
                    "docs/reports/scene_backend_parity_sionna_rt_latest.json",
                ],
            )
        )

    steps.append(
        _step(
            step_id="HF-2A",
            description="PO-SBR parity report",
            cmd=[
                py,
                "scripts/run_scene_backend_parity_po_sbr_rt.py",
                "--output-json",
                "docs/reports/scene_backend_parity_po_sbr_rt_latest.json",
            ],
            cwd=repo_root,
            env=base_env,
            refreshed_evidence=[
                "docs/reports/scene_backend_parity_po_sbr_rt_latest.json",
            ],
        )
    )

    steps.append(
        _step(
            step_id="HF-2B",
            description="PO-SBR strict post-change gate",
            cmd=[py, "scripts/run_po_sbr_post_change_gate.py", "--strict"],
            cwd=repo_root,
            env=base_env,
            refreshed_evidence=["docs/reports/po_sbr_post_change_gate_*.json"],
        )
    )

    steps.append(
        _step(
            step_id="HF-2C",
            description="PO-SBR strict progress snapshot",
            cmd=[
                py,
                "scripts/show_po_sbr_progress.py",
                "--strict-ready",
                "--output-json",
                "docs/reports/po_sbr_progress_snapshot_release_candidate_latest.json",
            ],
            cwd=repo_root,
            env=base_env,
            refreshed_evidence=[
                "docs/reports/po_sbr_progress_snapshot_release_candidate_latest.json",
            ],
        )
    )

    steps.append(
        _step(
            step_id="RS-2",
            description="paid RadarSimPy production closure",
            cmd=["bash", "scripts/run_radarsimpy_paid_6m_gate_ci.sh"],
            cwd=repo_root,
            env=base_env,
            refreshed_evidence=[
                "docs/reports/radarsimpy_production_release_gate_paid_6m.json",
                "docs/reports/radarsimpy_readiness_checkpoint_paid_6m.json",
                "docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json",
                "docs/reports/frontend_runtime_payload_provider_info_paid_6m.json",
            ],
        )
    )

    pass_count = sum(1 for row in steps if bool((row.get("run") or {}).get("pass", False)))
    fail_count = len(steps) - pass_count
    payload = {
        "report_name": "canonical_release_candidate_subset",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "with_sionna": bool(args.with_sionna),
        "step_count": len(steps),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass": bool(fail_count == 0),
        "steps": steps,
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("run_canonical_release_candidate_subset: done")
    print(f"pass={payload['pass']}")
    print(f"step_count={payload['step_count']}")
    print(f"output_json={out_json}")
    if (not payload["pass"]) and (not bool(args.allow_failures)):
        sys.exit(2)


if __name__ == "__main__":
    main()

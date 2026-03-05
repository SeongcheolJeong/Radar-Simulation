#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping


def _resolve_path(raw: str, repo_root: Path) -> Path:
    p = Path(str(raw)).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (repo_root / p).resolve()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json root must be object: {path}")
    return payload


def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _build_templates(status: Mapping[str, Any], docs: Mapping[str, str]) -> Dict[str, Any]:
    prod = "ready" if bool(status.get("production_gate_ready")) else "blocked"
    chk = "ready" if bool(status.get("readiness_ready")) else "blocked"
    par = "pass" if bool(status.get("parity_pass")) else "fail"
    e2e = "pass" if bool(status.get("frontend_e2e_pass")) else "fail"
    retention_apply = bool(status.get("retention_audit_apply", False))
    retention_deleted = int(status.get("retention_audit_deleted_count", 0) or 0)
    retention_failed = int(status.get("retention_audit_failed_delete_count", 0) or 0)
    release_date = str(status.get("release_date", ""))
    commit = str(status.get("head_commit_short", ""))

    slack_en = "\n".join(
        [
            f"[Release Update] RadarSimPy Runtime + Frontend Multiplexing ({release_date})",
            "",
            "Key updates:",
            "- Runtime path supports multiplexing-aware execution: tdm / bpm / custom",
            "- Graph Lab frontend exposes BPM/custom controls + presets",
            "- Dedicated LGIT output adapter integrated (lgit_customized_output.npz)",
            "- Paid production validation flow available via CI template",
            "",
            "Validation status:",
            f"- Production gate: {prod}",
            f"- Readiness checkpoint: {chk}",
            f"- Simulator parity: {par}",
            f"- Graph Lab Playwright E2E: {e2e}",
            f"- Report retention audit: apply={retention_apply} deleted={retention_deleted} failed={retention_failed}",
            "",
            f"Commit: {commit or '-'}",
            f"One-pager EN: {docs['onepager_en']}",
            f"One-pager KO: {docs['onepager_ko']}",
            f"Details: {docs['release_notes']}",
        ]
    )

    slack_ko = "\n".join(
        [
            f"[릴리즈 업데이트] RadarSimPy 런타임 + 프론트엔드 멀티플렉싱 ({release_date})",
            "",
            "주요 변경:",
            "- 런타임 멀티플렉싱 인지 실행 지원: tdm / bpm / custom",
            "- Graph Lab BPM/custom 제어 및 프리셋 노출",
            "- LGIT 전용 출력 어댑터 통합 (lgit_customized_output.npz)",
            "- 유료 프로덕션 검증 플로우 CI 템플릿 제공",
            "",
            "검증 상태:",
            f"- Production gate: {prod}",
            f"- Readiness checkpoint: {chk}",
            f"- Simulator parity: {par}",
            f"- Graph Lab Playwright E2E: {e2e}",
            f"- 리포트 보존 감사: apply={retention_apply} deleted={retention_deleted} failed={retention_failed}",
            "",
            f"커밋: {commit or '-'}",
            f"1페이지 요약(EN): {docs['onepager_en']}",
            f"1페이지 요약(KO): {docs['onepager_ko']}",
            f"상세: {docs['release_notes']}",
        ]
    )

    email_subject_en = f"[Release] RadarSimPy Runtime + Frontend Multiplexing ({release_date})"
    email_subject_ko = f"[릴리즈] RadarSimPy 런타임 + 프론트엔드 멀티플렉싱 ({release_date})"

    email_body_en = "\n".join(
        [
            "Hello team,",
            "",
            "Release highlights:",
            "1) Runtime multiplexing: tdm / bpm / custom",
            "2) Frontend controls + validation for BPM/custom",
            "3) LGIT output adapter integration",
            "4) Paid gate CI template",
            "",
            "Validation:",
            f"- production gate: {prod}",
            f"- readiness checkpoint: {chk}",
            f"- simulator parity: {par}",
            f"- frontend e2e: {e2e}",
            f"- retention audit: apply={retention_apply}, deleted={retention_deleted}, failed={retention_failed}",
            "",
            f"Commit: {commit or '-'}",
            f"Details: {docs['release_notes']}",
            f"One-pager EN: {docs['onepager_en']}",
            f"One-pager KO: {docs['onepager_ko']}",
            "",
            "Best regards,",
            "Radar Simulation Team",
        ]
    )

    email_body_ko = "\n".join(
        [
            "안녕하세요.",
            "",
            "릴리즈 요약:",
            "1) 런타임 멀티플렉싱: tdm / bpm / custom",
            "2) 프론트엔드 BPM/custom 제어 및 입력 검증",
            "3) LGIT 출력 어댑터 통합",
            "4) 유료 게이트 CI 템플릿 제공",
            "",
            "검증 결과:",
            f"- production gate: {prod}",
            f"- readiness checkpoint: {chk}",
            f"- simulator parity: {par}",
            f"- frontend e2e: {e2e}",
            f"- 보존 감사: apply={retention_apply}, deleted={retention_deleted}, failed={retention_failed}",
            "",
            f"커밋: {commit or '-'}",
            f"상세: {docs['release_notes']}",
            f"1페이지 요약(EN): {docs['onepager_en']}",
            f"1페이지 요약(KO): {docs['onepager_ko']}",
            "",
            "감사합니다.",
            "Radar Simulation Team",
        ]
    )

    return {
        "slack_en": slack_en,
        "slack_ko": slack_ko,
        "email_subject_en": email_subject_en,
        "email_subject_ko": email_subject_ko,
        "email_body_en": email_body_en,
        "email_body_ko": email_body_ko,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Build release announcement pack from report artifacts.")
    p.add_argument("--production-gate-json", default="docs/reports/radarsimpy_production_release_gate_paid_6m.json")
    p.add_argument("--readiness-json", default="docs/reports/radarsimpy_readiness_checkpoint_paid_6m.json")
    p.add_argument("--parity-json", default="docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json")
    p.add_argument("--frontend-e2e-json", default="docs/reports/graph_lab_playwright_e2e_latest.json")
    p.add_argument("--retention-audit-json", default="docs/reports/radarsimpy_report_retention_audit_latest.json")
    p.add_argument("--output-json", default="docs/reports/release_announcement_pack_latest.json")
    p.add_argument("--output-md", default="docs/reports/release_announcement_pack_latest.md")
    p.add_argument("--release-date", default="2026-03-05")
    args = p.parse_args()

    repo_root = Path.cwd().resolve()
    prod_path = _resolve_path(args.production_gate_json, repo_root)
    chk_path = _resolve_path(args.readiness_json, repo_root)
    par_path = _resolve_path(args.parity_json, repo_root)
    e2e_path = _resolve_path(args.frontend_e2e_json, repo_root)
    retention_path = _resolve_path(args.retention_audit_json, repo_root)
    out_json = _resolve_path(args.output_json, repo_root)
    out_md = _resolve_path(args.output_md, repo_root)

    prod = _load_json(prod_path)
    chk = _load_json(chk_path)
    par = _load_json(par_path)
    e2e = _load_json(e2e_path)
    retention = _load_json(retention_path)

    status = {
        "release_date": str(args.release_date),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "head_commit_short": _git(repo_root, "rev-parse", "--short", "HEAD"),
        "head_commit": _git(repo_root, "rev-parse", "HEAD"),
        "branch": _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
        "production_gate_ready": str(prod.get("production_gate_status", "")).strip().lower() == "ready",
        "readiness_ready": str(chk.get("overall_status", "")).strip().lower() == "ready",
        "parity_pass": bool(par.get("pass", False)),
        "frontend_e2e_pass": bool(
            bool(e2e.get("e2e_pass", False))
            and str(e2e.get("status", "")).strip().lower() in ("pass", "passed")
        ),
        "retention_audit_apply": bool(retention.get("apply", False)),
        "retention_audit_deleted_count": int(
            (retention.get("action") or {}).get("deleted_count", 0) or 0
        ),
        "retention_audit_failed_delete_count": int(
            (retention.get("action") or {}).get("failed_delete_count", 0) or 0
        ),
        "retention_audit_prunable_count": int(
            (retention.get("summary") or {}).get("prunable_count", 0) or 0
        ),
    }
    status["overall_ready"] = bool(
        status["production_gate_ready"]
        and status["readiness_ready"]
        and status["parity_pass"]
        and status["frontend_e2e_pass"]
    )

    docs = {
        "release_notes": "docs/279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md",
        "onepager_en": "docs/280_release_one_pager_radarsimpy_2026_03_05.md",
        "onepager_ko": "docs/281_release_one_pager_radarsimpy_2026_03_05_ko.md",
        "templates": "docs/282_release_announcement_templates_2026_03_05.md",
    }
    templates = _build_templates(status, docs)

    payload: Dict[str, Any] = {
        "version": "release_announcement_pack_v1",
        "status": status,
        "sources": {
            "production_gate_json": str(prod_path),
            "readiness_json": str(chk_path),
            "parity_json": str(par_path),
            "frontend_e2e_json": str(e2e_path),
            "retention_audit_json": str(retention_path),
        },
        "docs": docs,
        "templates": templates,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_lines = [
        "# Release Announcement Pack",
        "",
        f"- release_date: {status['release_date']}",
        f"- overall_ready: {status['overall_ready']}",
        f"- branch: {status['branch'] or '-'}",
        f"- head_commit: {status['head_commit_short'] or '-'}",
        "",
        "## Status",
        "",
        f"- production_gate_ready: {status['production_gate_ready']}",
        f"- readiness_ready: {status['readiness_ready']}",
        f"- parity_pass: {status['parity_pass']}",
        f"- frontend_e2e_pass: {status['frontend_e2e_pass']}",
        f"- retention_audit_apply: {status['retention_audit_apply']}",
        f"- retention_audit_deleted_count: {status['retention_audit_deleted_count']}",
        f"- retention_audit_failed_delete_count: {status['retention_audit_failed_delete_count']}",
        f"- retention_audit_prunable_count: {status['retention_audit_prunable_count']}",
        "",
        "## Slack EN",
        "",
        "```text",
        templates["slack_en"],
        "```",
        "",
        "## Slack KO",
        "",
        "```text",
        templates["slack_ko"],
        "```",
        "",
        "## Email Subject EN",
        "",
        f"`{templates['email_subject_en']}`",
        "",
        "## Email Subject KO",
        "",
        f"`{templates['email_subject_ko']}`",
        "",
    ]
    out_md.write_text("\n".join(md_lines), encoding="utf-8")

    print("build_release_announcement_pack: done")
    print(f"  overall_ready: {status['overall_ready']}")
    print(f"  output_json: {out_json}")
    print(f"  output_md: {out_md}")


if __name__ == "__main__":
    main()

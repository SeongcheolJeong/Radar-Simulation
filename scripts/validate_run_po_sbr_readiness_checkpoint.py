#!/usr/bin/env python3
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _write_radar_npz(path: Path, rd: np.ndarray, ra: np.ndarray, tag: str) -> None:
    np.savez(path, fx_dop_win=rd, fx_ang=ra, metadata_json=json.dumps({"tag": tag}))


def _write_adc_npz(path: Path, adc: np.ndarray) -> None:
    np.savez(path, adc=adc, metadata_json=json.dumps({"shape": list(adc.shape)}))


def _write_path_json(path: Path) -> None:
    rows = []
    for chirp_idx in range(4):
        rows.append(
            [
                {
                    "delay_s": 2.0 * 25.0 / 299_792_458.0,
                    "doppler_hz": 0.0,
                    "unit_direction": [1.0, 0.0, 0.0],
                    "amp_complex": {"re": 1.0e-3, "im": 0.0},
                    "path_id": f"path_{chirp_idx}",
                    "material_tag": "metal",
                    "reflection_order": 1,
                }
            ]
        )
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def _mk_profile(root: Path, profile: str, rd: np.ndarray, ra: np.ndarray) -> None:
    for backend in ("analytic_targets", "po_sbr_rt", "sionna_rt"):
        out = root / profile / "golden_outputs" / backend / "pipeline_outputs"
        out.mkdir(parents=True, exist_ok=True)
        _write_radar_npz(out / "radar_map.npz", rd=rd, ra=ra, tag=f"{profile}:{backend}")
        _write_path_json(out / "path_list.json")
        _write_adc_npz(out / "adc_cube.npz", np.ones((32, 4, 2, 2), dtype=np.complex64))


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )


def _run_checkpoint_case(
    repo_root: Path,
    env: dict,
    date_stamp: str,
    closure_json: Path,
    avx_gate_json: Path,
    avx_gate_matrix_json: Path,
) -> tuple[str, dict, dict, dict, dict]:
    proc = subprocess.run(
        ["bash", "scripts/run_po_sbr_readiness_checkpoint.sh", date_stamp],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "run_po_sbr_readiness_checkpoint.sh failed\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
        )

    out = proc.stdout or ""
    m_post = re.search(r"post_change_report=(.+)$", out, flags=re.MULTILINE)
    m_progress = re.search(r"progress_report=(.+)$", out, flags=re.MULTILINE)
    if not m_post or not m_progress:
        raise AssertionError(f"missing output paths in checkpoint output:\n{out}")

    post_path = Path(m_post.group(1).strip())
    progress_path = Path(m_progress.group(1).strip())
    if not post_path.is_absolute():
        post_path = (repo_root / post_path).resolve()
    else:
        post_path = post_path.resolve()
    if not progress_path.is_absolute():
        progress_path = (repo_root / progress_path).resolve()
    else:
        progress_path = progress_path.resolve()

    if not post_path.exists():
        raise FileNotFoundError(f"post-change report missing: {post_path}")
    if not progress_path.exists():
        raise FileNotFoundError(f"progress report missing: {progress_path}")
    if not closure_json.exists():
        raise FileNotFoundError(f"closure report missing: {closure_json}")
    if not avx_gate_json.exists():
        raise FileNotFoundError(f"avx gate report missing: {avx_gate_json}")
    if not avx_gate_matrix_json.exists():
        raise FileNotFoundError(f"avx gate matrix report missing: {avx_gate_matrix_json}")

    post_payload = _load_json(post_path)
    progress_payload = _load_json(progress_path)
    closure_payload = _load_json(closure_json)
    avx_payload = _load_json(avx_gate_json)
    return out, post_payload, progress_payload, closure_payload, avx_payload


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    merged_checkpoint = (
        repo_root / "docs" / "reports" / "po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json"
    ).resolve()
    if not merged_checkpoint.exists():
        raise FileNotFoundError(f"missing merged checkpoint: {merged_checkpoint}")

    with tempfile.TemporaryDirectory(prefix="validate_run_po_sbr_readiness_checkpoint_") as td:
        root = Path(td)
        matrix_root = root / "matrix"
        closure_json_default = root / "closure_default.json"
        closure_json_skip = root / "closure_skip.json"
        avx_gate_json = root / "avx_gate.json"
        avx_gate_matrix_json = root / "avx_gate_matrix" / "summary.json"
        em_policy_json = (repo_root / "docs" / "em_solver_packaging_policy.json").resolve()
        em_reference_locks_md = (repo_root / "external" / "reference-locks.md").resolve()

        rd = np.full((16, 64), 1.0e-12, dtype=np.float64)
        ra = np.full((12, 64), 1.0e-12, dtype=np.float64)
        rd[5, 27] = 2.0
        ra[6, 27] = 1.5
        _mk_profile(matrix_root, "profile_a", rd=rd, ra=ra)

        date_stamp = "2026_03_02"
        post_change_json = (repo_root / "docs" / "reports" / f"po_sbr_post_change_gate_{date_stamp}.json").resolve()
        progress_json = (repo_root / "docs" / "reports" / f"po_sbr_progress_snapshot_{date_stamp}.json").resolve()

        env_base = dict(os.environ)
        env_base["PO_SBR_SKIP_WEB_E2E_VALIDATOR"] = "1"
        env_base["PO_SBR_SKIP_MERGED_FULL_TRACK_VERIFIER"] = "1"
        env_base["PO_SBR_MERGED_CHECKPOINT_JSON_OVERRIDE"] = str(merged_checkpoint)
        env_base["PO_SBR_CLOSURE_JSON_OVERRIDE"] = str(closure_json_default)
        env_base["PO_SBR_AVX_DEVELOPER_GATE_MATRIX_ROOT_OVERRIDE"] = str(matrix_root)
        env_base["PO_SBR_AVX_DEVELOPER_GATE_SUMMARY_JSON_OVERRIDE"] = str(avx_gate_json)
        env_base["PO_SBR_AVX_DEVELOPER_GATE_MATRIX_SUMMARY_JSON_OVERRIDE"] = str(avx_gate_matrix_json)
        env_base["PO_SBR_AVX_DEVELOPER_GATE_DISABLE_AUTO_TUNE"] = "1"
        env_base["PO_SBR_AVX_DEVELOPER_GATE_ALLOW_FUNCTION_NONBETTER"] = "1"
        env_base["PO_SBR_AVX_DEVELOPER_GATE_MIN_PHYSICS_BETTER_COUNT"] = "0"
        env_base["PO_SBR_EM_POLICY_JSON_OVERRIDE"] = str(em_policy_json)
        env_base["PO_SBR_EM_REFERENCE_LOCKS_MD_OVERRIDE"] = str(em_reference_locks_md)
        if not em_policy_json.exists():
            raise FileNotFoundError(f"missing EM policy json: {em_policy_json}")
        if not em_reference_locks_md.exists():
            raise FileNotFoundError(f"missing EM reference-locks markdown: {em_reference_locks_md}")

        hooks_before_proc = _run_git(repo_root, "config", "--get", "core.hooksPath")
        hooks_before = hooks_before_proc.stdout.strip() if hooks_before_proc.returncode == 0 else None
        set_proc = _run_git(repo_root, "config", "core.hooksPath", ".githooks")
        if set_proc.returncode != 0:
            raise RuntimeError(
                "failed to set core.hooksPath for validator run:\n"
                f"stdout:\n{set_proc.stdout}\n"
                f"stderr:\n{set_proc.stderr}\n"
            )

        try:
            out_default, post_payload_default, progress_payload_default, closure_payload_default, avx_payload_default = _run_checkpoint_case(
                repo_root=repo_root,
                env=env_base,
                date_stamp=date_stamp,
                closure_json=closure_json_default,
                avx_gate_json=avx_gate_json,
                avx_gate_matrix_json=avx_gate_matrix_json,
            )

            env_skip = dict(env_base)
            env_skip["PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR"] = "1"
            env_skip["PO_SBR_SKIP_PROGRESS_SNAPSHOT_VALIDATOR"] = "1"
            env_skip["PO_SBR_SKIP_HOOK_SELFTEST"] = "1"
            env_skip["PO_SBR_SKIP_EM_POLICY_VALIDATOR"] = "1"
            env_skip["PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR"] = "1"
            env_skip["PO_SBR_CLOSURE_JSON_OVERRIDE"] = str(closure_json_skip)
            out_skip, post_payload_skip, progress_payload_skip, closure_payload_skip, avx_payload_skip = _run_checkpoint_case(
                repo_root=repo_root,
                env=env_skip,
                date_stamp=date_stamp,
                closure_json=closure_json_skip,
                avx_gate_json=avx_gate_json,
                avx_gate_matrix_json=avx_gate_matrix_json,
            )
        finally:
            if hooks_before is None:
                _run_git(repo_root, "config", "--unset", "core.hooksPath")
            else:
                _run_git(repo_root, "config", "core.hooksPath", hooks_before)

        if "skip merged full-track verifier (PO_SBR_SKIP_MERGED_FULL_TRACK_VERIFIER=1)" not in out_default:
            raise AssertionError("expected merged-verifier skip log line missing")
        if "validate post-change deterministic gate" not in out_default:
            raise AssertionError("expected post-change deterministic validator log line missing")
        if "validate operator-closure report deterministic runner" not in out_default:
            raise AssertionError("expected operator-closure report deterministic validator log line missing")
        if "validate_run_po_sbr_operator_handoff_closure_report: pass" not in out_default:
            raise AssertionError("expected operator-closure report deterministic validator pass marker missing")
        if "validate progress snapshot deterministic runner" not in out_default:
            raise AssertionError("expected progress snapshot deterministic validator log line missing")
        if "validate pre-push local-artifact mode" not in out_default:
            raise AssertionError("expected pre-push local-artifact validator execution log line missing")
        if "[closure] validate operator handoff closure report" not in out_default:
            raise AssertionError("expected closure report validator log line missing")
        if "validate_po_sbr_operator_handoff_closure_report: pass" not in out_default:
            raise AssertionError("expected closure report validator pass marker missing")
        if "[closure] validate EM solver packaging policy" not in out_default:
            raise AssertionError("expected closure EM policy validator log line missing")
        if "validate_em_solver_packaging_policy: pass" not in out_default:
            raise AssertionError("expected closure EM policy validator pass marker missing")
        if "hook_skip_mode_matrix_verified: true" not in out_default:
            raise AssertionError("expected pre-push selftest skip-mode matrix marker missing")
        if "hook_closure_report_skip_only_verified: true" not in out_default:
            raise AssertionError("expected pre-push closure-report-skip-only marker missing")
        if "tracked_report_changes: 0" not in out_default:
            raise AssertionError("expected pre-push selftest tracked_report_changes marker missing")

        if "skip post-change deterministic validator (PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR=1)" not in out_skip:
            raise AssertionError("expected post-change deterministic skip log line missing")
        if "skip progress snapshot deterministic validator (PO_SBR_SKIP_PROGRESS_SNAPSHOT_VALIDATOR=1)" not in out_skip:
            raise AssertionError("expected progress snapshot deterministic skip log line missing")
        if (
            "skip operator-closure report deterministic validator (PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR=1)"
            not in out_skip
        ):
            raise AssertionError("expected operator-closure report deterministic skip log line missing")
        if "skip pre-push local-artifact validator (PO_SBR_SKIP_HOOK_SELFTEST=1)" not in out_skip:
            raise AssertionError("expected pre-push local-artifact validator skip log line missing")
        if (
            "skip EM solver packaging policy validator (PO_SBR_SKIP_EM_POLICY_VALIDATOR=1)"
            not in out_skip
        ):
            raise AssertionError("expected closure EM policy validator skip log line missing")
        if "[closure] validate operator handoff closure report" not in out_skip:
            raise AssertionError("expected closure report validator log line missing in skip branch")
        if "validate_po_sbr_operator_handoff_closure_report: pass" not in out_skip:
            raise AssertionError("expected closure report validator pass marker missing in skip branch")
        if "validate_run_po_sbr_operator_handoff_closure_report: pass" in out_skip:
            raise AssertionError(
                "operator-closure report deterministic validator pass marker unexpectedly present in skip branch"
            )
        if "validate_em_solver_packaging_policy: pass" in out_skip:
            raise AssertionError("closure EM policy validator pass marker unexpectedly present in skip branch")
        if "hook_skip_mode_matrix_verified: true" in out_skip:
            raise AssertionError("pre-push selftest marker unexpectedly present in hook-selftest-skip branch")
        if "hook_closure_report_skip_only_verified: true" in out_skip:
            raise AssertionError(
                "pre-push closure-report-skip-only marker unexpectedly present in hook-selftest-skip branch"
            )

        assert str(post_payload_default.get("overall_status", "")) == "ready"
        assert str(progress_payload_default.get("overall_ready", "")) in {"True", "true"} or bool(
            progress_payload_default.get("overall_ready", False)
        )
        assert str(closure_payload_default.get("overall_status", "")) == "ready"
        assert str(avx_payload_default.get("developer_gate_status", "")) == "ready"
        em_policy_default = closure_payload_default.get("em_solver_packaging_policy") or {}
        assert str(em_policy_default.get("validator_status", "")) == "pass"
        em_policy_default_path = Path(str(em_policy_default.get("policy_json", "")).strip()).expanduser().resolve()
        em_reference_default_path = (
            Path(str(em_policy_default.get("reference_locks_md", "")).strip()).expanduser().resolve()
        )
        if not em_policy_default_path.exists():
            raise FileNotFoundError(f"default closure EM policy json missing: {em_policy_default_path}")
        if not em_reference_default_path.exists():
            raise FileNotFoundError(
                f"default closure EM reference-locks markdown missing: {em_reference_default_path}"
            )

        assert str(post_payload_skip.get("overall_status", "")) == "ready"
        assert str(progress_payload_skip.get("overall_ready", "")) in {"True", "true"} or bool(
            progress_payload_skip.get("overall_ready", False)
        )
        assert str(closure_payload_skip.get("overall_status", "")) == "ready"
        assert str(avx_payload_skip.get("developer_gate_status", "")) == "ready"
        em_policy_skip = closure_payload_skip.get("em_solver_packaging_policy") or {}
        assert str(em_policy_skip.get("validator_status", "")) == "skipped"
        em_policy_skip_path = Path(str(em_policy_skip.get("policy_json", "")).strip()).expanduser().resolve()
        em_reference_skip_path = (
            Path(str(em_policy_skip.get("reference_locks_md", "")).strip()).expanduser().resolve()
        )
        if not em_policy_skip_path.exists():
            raise FileNotFoundError(f"skip closure EM policy json missing: {em_policy_skip_path}")
        if not em_reference_skip_path.exists():
            raise FileNotFoundError(
                f"skip closure EM reference-locks markdown missing: {em_reference_skip_path}"
            )
        if closure_json_default == closure_json_skip:
            raise AssertionError("default/skip closure outputs must use distinct paths")

    print("validate_run_po_sbr_readiness_checkpoint: pass")


if __name__ == "__main__":
    run()

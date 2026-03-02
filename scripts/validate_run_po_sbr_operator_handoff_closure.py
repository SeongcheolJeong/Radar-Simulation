#!/usr/bin/env python3
import json
import os
import subprocess
import sys
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


def _mk_profile(
    root: Path,
    profile: str,
    truth_rd: np.ndarray,
    truth_ra: np.ndarray,
    cand_rd: np.ndarray,
    cand_ra: np.ndarray,
    ref_rd: np.ndarray,
    ref_ra: np.ndarray,
) -> None:
    for backend, rd, ra in (
        ("analytic_targets", truth_rd, truth_ra),
        ("po_sbr_rt", cand_rd, cand_ra),
        ("sionna_rt", ref_rd, ref_ra),
    ):
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


def _run_closure_case(repo_root: Path, env: dict, closure_json: Path) -> tuple[str, dict]:
    env_case = dict(env)
    env_case["PO_SBR_CLOSURE_JSON_OVERRIDE"] = str(closure_json)
    proc = subprocess.run(
        ["bash", "scripts/verify_po_sbr_operator_handoff_closure.sh", str(closure_json)],
        cwd=str(repo_root),
        env=env_case,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "verify_po_sbr_operator_handoff_closure.sh failed\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
        )
    if not closure_json.exists():
        raise FileNotFoundError(f"closure output missing: {closure_json}")
    return proc.stdout or "", _load_json(closure_json)


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    # Use the canonical merged checkpoint as stable input while skipping expensive/full verifiers.
    merged_checkpoint = (
        repo_root / "docs" / "reports" / "po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json"
    ).resolve()
    if not merged_checkpoint.exists():
        raise FileNotFoundError(f"missing merged checkpoint: {merged_checkpoint}")

    with tempfile.TemporaryDirectory(prefix="validate_run_po_sbr_operator_handoff_closure_") as td:
        root = Path(td)
        matrix_root = root / "matrix"
        avx_gate_json = root / "avx_gate.json"
        avx_gate_matrix_json = root / "avx_gate_matrix" / "summary.json"
        closure_json_default = root / "closure_default.json"
        closure_json_skip = root / "closure_skip.json"
        em_policy_json = (repo_root / "docs" / "em_solver_packaging_policy.json").resolve()
        em_reference_locks_md = (repo_root / "external" / "reference-locks.md").resolve()

        rd_truth = np.full((16, 64), 1.0e-12, dtype=np.float64)
        ra_truth = np.full((12, 64), 1.0e-12, dtype=np.float64)
        rd_truth[5, 27] = 2.0
        ra_truth[6, 27] = 1.5

        # Candidate/reference/truth equal: deterministic ready baseline for closure wiring validation.
        _mk_profile(
            root=matrix_root,
            profile="profile_a",
            truth_rd=rd_truth,
            truth_ra=ra_truth,
            cand_rd=rd_truth.copy(),
            cand_ra=ra_truth.copy(),
            ref_rd=rd_truth.copy(),
            ref_ra=ra_truth.copy(),
        )

        env = dict(os.environ)
        env["PO_SBR_MERGED_CHECKPOINT_JSON_OVERRIDE"] = str(merged_checkpoint)
        env["PO_SBR_AVX_DEVELOPER_GATE_SUMMARY_JSON_OVERRIDE"] = str(avx_gate_json)
        env["PO_SBR_AVX_DEVELOPER_GATE_MATRIX_SUMMARY_JSON_OVERRIDE"] = str(avx_gate_matrix_json)
        env["PO_SBR_AVX_DEVELOPER_GATE_MATRIX_ROOT_OVERRIDE"] = str(matrix_root)
        env["PO_SBR_AVX_DEVELOPER_GATE_DISABLE_AUTO_TUNE"] = "1"
        env["PO_SBR_AVX_DEVELOPER_GATE_ALLOW_FUNCTION_NONBETTER"] = "1"
        env["PO_SBR_AVX_DEVELOPER_GATE_MIN_PHYSICS_BETTER_COUNT"] = "0"
        env["PO_SBR_SKIP_WEB_E2E_VALIDATOR"] = "1"
        env["PO_SBR_SKIP_MERGED_FULL_TRACK_VERIFIER"] = "1"
        env["PO_SBR_EM_POLICY_JSON_OVERRIDE"] = str(em_policy_json)
        env["PO_SBR_EM_REFERENCE_LOCKS_MD_OVERRIDE"] = str(em_reference_locks_md)

        if not em_policy_json.exists():
            raise FileNotFoundError(f"missing EM policy json: {em_policy_json}")
        if not em_reference_locks_md.exists():
            raise FileNotFoundError(f"missing EM reference locks: {em_reference_locks_md}")

        out_default, closure_default = _run_closure_case(
            repo_root=repo_root,
            env=env,
            closure_json=closure_json_default,
        )
        if "[closure] validate operator handoff closure report" not in out_default:
            raise AssertionError("closure report validator log line missing in default closure run")
        if "validate_po_sbr_operator_handoff_closure_report: pass" not in out_default:
            raise AssertionError("closure report validator pass marker missing in default closure run")
        if "[closure] validate EM solver packaging policy" not in out_default:
            raise AssertionError("EM policy validator log line missing in default closure run")
        if "validate_em_solver_packaging_policy: pass" not in out_default:
            raise AssertionError("EM policy validator pass marker missing in default closure run")

        env_skip = dict(env)
        env_skip["PO_SBR_SKIP_EM_POLICY_VALIDATOR"] = "1"
        out_skip, closure_skip = _run_closure_case(
            repo_root=repo_root,
            env=env_skip,
            closure_json=closure_json_skip,
        )
        if "[closure] validate operator handoff closure report" not in out_skip:
            raise AssertionError("closure report validator log line missing in closure skip run")
        if "validate_po_sbr_operator_handoff_closure_report: pass" not in out_skip:
            raise AssertionError("closure report validator pass marker missing in closure skip run")
        if (
            "[closure] skip EM solver packaging policy validator (PO_SBR_SKIP_EM_POLICY_VALIDATOR=1)"
            not in out_skip
        ):
            raise AssertionError("EM policy validator skip log line missing in closure skip run")
        if "validate_em_solver_packaging_policy: pass" in out_skip:
            raise AssertionError("EM policy validator pass marker unexpectedly present in skip run")

        if not avx_gate_json.exists():
            raise FileNotFoundError(f"avx gate output missing: {avx_gate_json}")
        if not avx_gate_matrix_json.exists():
            raise FileNotFoundError(f"avx gate matrix output missing: {avx_gate_matrix_json}")

        for label, closure in (
            ("default", closure_default),
            ("skip", closure_skip),
        ):
            assert str(closure.get("report_name", "")) == "po_sbr_operator_handoff_closure"
            assert str(closure.get("overall_status", "")) == "ready"

            audit = closure.get("frontend_timeline_import_audit") or {}
            merged = closure.get("merged_full_track") or {}
            avx_gate = closure.get("avx_developer_gate") or {}
            em_policy = closure.get("em_solver_packaging_policy") or {}
            assert str(audit.get("validator_status", "")) == "pass"
            assert str(audit.get("api_regression_status", "")) in {"pass", "skipped"}
            assert str(merged.get("validation_status", "")) in {"pass", "skipped"}
            assert bool(merged.get("ready", False))
            assert str(avx_gate.get("status", "")) == "ready"
            assert int(avx_gate.get("physics_worse_count", 1)) == 0
            em_status = str(em_policy.get("validator_status", "")).strip()
            if label == "default":
                assert em_status == "pass"
            else:
                assert em_status == "skipped"
            em_policy_path = Path(str(em_policy.get("policy_json", "")).strip()).expanduser().resolve()
            em_reference_path = (
                Path(str(em_policy.get("reference_locks_md", "")).strip()).expanduser().resolve()
            )
            if not em_policy_path.exists():
                raise FileNotFoundError(f"{label} closure EM policy json missing: {em_policy_path}")
            if not em_reference_path.exists():
                raise FileNotFoundError(f"{label} closure EM reference-locks missing: {em_reference_path}")
        if closure_json_default == closure_json_skip:
            raise AssertionError("closure default/skip outputs must use distinct paths")

    print("validate_run_po_sbr_operator_handoff_closure: pass")


if __name__ == "__main__":
    run()

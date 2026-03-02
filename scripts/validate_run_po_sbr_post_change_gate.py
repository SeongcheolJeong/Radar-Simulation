#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    gate_script = repo_root / "scripts" / "run_po_sbr_post_change_gate.py"
    spec = importlib.util.spec_from_file_location("run_po_sbr_post_change_gate", gate_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load gate script module: {gate_script}")
    gate_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate_mod)

    # Coverage: ensure gating patterns include hook and deterministic validator paths.
    if not gate_mod._is_runtime_affecting(".githooks/pre-push"):
        raise AssertionError("runtime-affecting detection must include .githooks/pre-push")
    if not gate_mod._is_runtime_affecting("scripts/show_po_sbr_progress.py"):
        raise AssertionError("runtime-affecting detection must include show_po_sbr_progress.py")
    if not gate_mod._is_runtime_affecting("scripts/validate_run_po_sbr_readiness_checkpoint.py"):
        raise AssertionError("runtime-affecting detection must include validate_run_po_sbr_*")
    if not gate_mod._is_runtime_affecting("scripts/validate_run_avx_export_benchmark.py"):
        raise AssertionError("runtime-affecting detection must include validate_run_avx_*")
    if not gate_mod._is_runtime_affecting("scripts/validate_em_solver_packaging_policy.py"):
        raise AssertionError("runtime-affecting detection must include validate_em_solver_packaging_policy.py")
    if not gate_mod._is_runtime_affecting("docs/em_solver_packaging_policy.json"):
        raise AssertionError("runtime-affecting detection must include docs/em_solver_packaging_policy.json")
    if not gate_mod._is_runtime_affecting("external/reference-locks.md"):
        raise AssertionError("runtime-affecting detection must include external/reference-locks.md")
    if gate_mod._is_runtime_affecting("docs/validation_log.md"):
        raise AssertionError("runtime-affecting detection must keep docs/* non-runtime")

    with tempfile.TemporaryDirectory(prefix="validate_run_po_sbr_post_change_gate_") as td:
        root = Path(td)
        out_skip = root / "post_change_skip.json"
        out_force_pass = root / "post_change_force_pass.json"
        out_force_fail = root / "post_change_force_fail.json"

        closure_pass = root / "closure_pass.sh"
        closure_pass.write_text("#!/usr/bin/env bash\nset -euo pipefail\necho closure_pass\n", encoding="utf-8")
        closure_pass.chmod(0o755)

        closure_fail = root / "closure_fail.sh"
        closure_fail.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\necho closure_fail\nexit 2\n",
            encoding="utf-8",
        )
        closure_fail.chmod(0o755)

        # Case 1: No changes => closure not required => strict should pass with skipped status.
        proc_skip = _run(
            [
                str(Path(sys.executable)),
                "scripts/run_po_sbr_post_change_gate.py",
                "--base-ref",
                "HEAD",
                "--head-ref",
                "HEAD",
                "--strict",
                "--output-json",
                str(out_skip),
            ],
            cwd=repo_root,
        )
        if proc_skip.returncode != 0:
            raise AssertionError(
                "skip case failed\n"
                f"stdout:\n{proc_skip.stdout}\n"
                f"stderr:\n{proc_skip.stderr}\n"
            )
        payload_skip = _load_json(out_skip)
        assert payload_skip.get("closure_required") is False
        assert str(payload_skip.get("closure_status", "")) == "skipped"
        assert str(payload_skip.get("overall_status", "")) == "ready"

        # Case 2: Force-run + pass closure => strict passes.
        proc_force_pass = _run(
            [
                str(Path(sys.executable)),
                "scripts/run_po_sbr_post_change_gate.py",
                "--base-ref",
                "HEAD",
                "--head-ref",
                "HEAD",
                "--force-run",
                "--strict",
                "--closure-script",
                str(closure_pass),
                "--output-json",
                str(out_force_pass),
            ],
            cwd=repo_root,
        )
        if proc_force_pass.returncode != 0:
            raise AssertionError(
                "force-pass case failed\n"
                f"stdout:\n{proc_force_pass.stdout}\n"
                f"stderr:\n{proc_force_pass.stderr}\n"
            )
        payload_force_pass = _load_json(out_force_pass)
        assert payload_force_pass.get("closure_required") is True
        assert payload_force_pass.get("forced") is True
        assert str(payload_force_pass.get("closure_status", "")) == "pass"
        assert str(payload_force_pass.get("overall_status", "")) == "ready"

        # Case 3: Force-run + failing closure => non-strict returns 0 but blocked status.
        proc_force_fail_non_strict = _run(
            [
                str(Path(sys.executable)),
                "scripts/run_po_sbr_post_change_gate.py",
                "--base-ref",
                "HEAD",
                "--head-ref",
                "HEAD",
                "--force-run",
                "--closure-script",
                str(closure_fail),
                "--output-json",
                str(out_force_fail),
            ],
            cwd=repo_root,
        )
        if proc_force_fail_non_strict.returncode != 0:
            raise AssertionError(
                "force-fail non-strict case should return 0\n"
                f"stdout:\n{proc_force_fail_non_strict.stdout}\n"
                f"stderr:\n{proc_force_fail_non_strict.stderr}\n"
            )
        payload_force_fail = _load_json(out_force_fail)
        assert payload_force_fail.get("closure_required") is True
        assert str(payload_force_fail.get("closure_status", "")) == "fail"
        assert str(payload_force_fail.get("overall_status", "")) == "blocked"

        # Case 4: Force-run + failing closure + strict => non-zero exit.
        proc_force_fail_strict = _run(
            [
                str(Path(sys.executable)),
                "scripts/run_po_sbr_post_change_gate.py",
                "--base-ref",
                "HEAD",
                "--head-ref",
                "HEAD",
                "--force-run",
                "--strict",
                "--closure-script",
                str(closure_fail),
                "--output-json",
                str(root / "post_change_force_fail_strict.json"),
            ],
            cwd=repo_root,
        )
        if proc_force_fail_strict.returncode == 0:
            raise AssertionError("force-fail strict case should return non-zero")

    print("validate_run_po_sbr_post_change_gate: pass")


if __name__ == "__main__":
    run()

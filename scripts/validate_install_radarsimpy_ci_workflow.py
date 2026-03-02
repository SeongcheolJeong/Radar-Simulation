#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "install_radarsimpy_ci_workflow.py"

    with tempfile.TemporaryDirectory(prefix="validate_install_radarsimpy_ci_") as td:
        root = Path(td)
        template_path = root / "template.workflow.yml"
        output_path = root / ".github" / "workflows" / "radarsimpy-integration-smoke.yml"

        template_text = (
            "name: Example\n"
            "on:\n"
            "  push:\n"
            "jobs:\n"
            "  test:\n"
            "    runs-on: ubuntu-latest\n"
        )
        template_path.write_text(template_text, encoding="utf-8")

        env = dict(os.environ)

        # install mode should materialize the output.
        proc_install = subprocess.run(
            [
                str(Path(sys.executable)),
                str(script_path),
                "--template",
                str(template_path),
                "--output",
                str(output_path),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy CI workflow template install completed." in proc_install.stdout, proc_install.stdout
        assert output_path.exists()
        assert output_path.read_text(encoding="utf-8") == template_text

        # check mode should pass when synced.
        proc_check_ok = subprocess.run(
            [
                str(Path(sys.executable)),
                str(script_path),
                "--template",
                str(template_path),
                "--output",
                str(output_path),
                "--check",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy CI workflow template check completed." in proc_check_ok.stdout, proc_check_ok.stdout
        assert "synced: True" in proc_check_ok.stdout, proc_check_ok.stdout

        # corrupt output and verify check mode fails with rc=2.
        output_path.write_text(template_text + "# drift\n", encoding="utf-8")
        proc_check_fail = subprocess.run(
            [
                str(Path(sys.executable)),
                str(script_path),
                "--template",
                str(template_path),
                "--output",
                str(output_path),
                "--check",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_check_fail.returncode == 2, proc_check_fail.returncode
        assert "synced: False" in proc_check_fail.stdout, proc_check_fail.stdout

    print("validate_install_radarsimpy_ci_workflow: pass")


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def _pick_python_bin(repo_root: Path) -> str:
    venv_python = repo_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return str(Path(sys.executable))


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    python_bin = _pick_python_bin(repo_root=repo_root)

    with tempfile.TemporaryDirectory(prefix="validate_radarsimpy_order_gate_") as td:
        root = Path(td)
        order_assets = root / "assets"
        order_assets.mkdir(parents=True, exist_ok=True)

        zip_path = order_assets / "Ubuntu24_x86_64_CPU.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("Ubuntu24_x86_64_CPU/license_RadarSimPy_fixture.lic", "fixture-license")

        order_html = root / "order.html"
        order_html.write_text(
            (
                "<html><body>"
                "<a href=\"file://"
                + str(zip_path)
                + "\" class=\"woocommerce-MyAccount-downloads-file button alt\">"
                "Ubuntu24_x86_64_CPU.zip</a>"
                "</body></html>"
            ),
            encoding="utf-8",
        )

        out_root = root / "out"
        out_json = root / "summary.json"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        proc = subprocess.run(
            [
                python_bin,
                "scripts/run_radarsimpy_production_gate_from_order.py",
                "--order-html-file",
                str(order_html),
                "--download-label",
                "Ubuntu24_x86_64_CPU.zip",
                "--output-root",
                str(out_root),
                "--output-json",
                str(out_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                "run_radarsimpy_production_gate_from_order failed\n"
                f"stdout:\n{proc.stdout}\n"
                f"stderr:\n{proc.stderr}\n"
            )

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload.get("status") == "ready"
        assert int(payload.get("order_download_row_count", -1)) == 1
        assert int(payload.get("downloaded_count", -1)) == 1
        lic = payload.get("selected_license_file")
        assert isinstance(lic, str) and lic.endswith(".lic")
        assert Path(lic).exists(), lic
        assert payload.get("run_production_gate") is False
        assert payload.get("production_gate_run", {}).get("skipped") is True

    print("validate_run_radarsimpy_production_gate_from_order: pass")


if __name__ == "__main__":
    run()

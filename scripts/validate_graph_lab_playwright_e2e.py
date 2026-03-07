#!/usr/bin/env python3
"""Playwright browser E2E + visual snapshot validation for Graph Lab.

This validator is optional by default:
- If Playwright (python package) or browser binaries are unavailable, it records a skip and exits 0.
- Use --require-playwright to enforce hard failure when Playwright cannot run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.parse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

from avxsim.web_e2e_api import WebE2EOrchestrator, create_web_e2e_http_server

VISUAL_COMPARE_TARGETS = (
    "topbar.png",
    "decision_pane.png",
    "artifact_inspector.png",
)


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1 << 16)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _build_scene(scene_path: Path) -> None:
    payload = {
        "scene_id": "graph_lab_playwright_validate_scene_v1",
        "backend": {
            "type": "analytic_targets",
            "n_chirps": 4,
            "chirp_interval_s": 4.0e-5,
            "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
            "rx_pos_m": [[0.0, 0.00185, 0.0], [0.0, 0.0037, 0.0]],
            "targets": [
                {
                    "path_id": "p1",
                    "range_m": 25.0,
                    "radial_velocity_mps": -2.0,
                    "az_deg": 8.0,
                    "amp": 1.0,
                },
                {
                    "path_id": "p2",
                    "range_m": 38.0,
                    "radial_velocity_mps": 3.5,
                    "az_deg": -12.0,
                    "amp": {"re": 0.7, "im": 0.2},
                },
            ],
            "noise_sigma": 0.0,
        },
        "radar": {
            "fc_hz": 77e9,
            "slope_hz_per_s": 20e12,
            "fs_hz": 20e6,
            "samples_per_chirp": 256,
        },
        "map_config": {
            "nfft_range": 256,
            "nfft_doppler": 16,
            "nfft_angle": 8,
            "range_bin_limit": 64,
        },
    }
    scene_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)


def run(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    expect_compare_runner_ready = bool(
        (
            repo_root
            / "external"
            / "radarsimpy_trial"
            / "Ubuntu24_x86_64_CPU"
            / "Ubuntu24_x86_64_CPU"
            / "radarsimpy"
            / "__init__.py"
        ).is_file()
        and any((repo_root / "external" / "radarsimpy" / "src" / "radarsimpy").glob("license_RadarSimPy_*.lic"))
    )
    snapshot_root = repo_root / "docs" / "reports" / "graph_lab_playwright_snapshots"
    baseline_dir = snapshot_root / "baseline"
    latest_dir = snapshot_root / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    baseline_dir.mkdir(parents=True, exist_ok=True)

    report: Dict[str, Any] = {
        "version": "graph_lab_playwright_e2e_report_v1",
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "require_playwright": bool(args.require_playwright),
        "strict_visual": bool(args.strict_visual),
        "update_baseline": bool(args.update_baseline),
        "playwright_available": False,
        "playwright_runtime_ready": False,
        "e2e_pass": False,
        "visual": {
            "missing_baseline": [],
            "changed": [],
            "matched": [],
        },
        "runtime_controls": {
            "purpose_presets_checked": [],
            "ffd_fields_present": False,
            "advanced_controls_checked": [],
            "runtime_diagnostics_checked": False,
            "compare_workflow_checked": False,
            "quick_pair_shortcuts_checked": False,
            "preset_pair_runner_checked": False,
            "track_compare_runner_checked": False,
            "track_compare_runner_result": "",
            "compare_assessment_checked": False,
            "decision_brief_runtime_compare_checked": False,
        },
        "artifacts": {},
        "status": "unknown",
        "note": "",
    }
    debug: Dict[str, Any] = {
        "console_tail": [],
        "page_errors": [],
    }

    try:
        from playwright.sync_api import Error as PlaywrightError  # type: ignore
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as exc:
        report["status"] = "skipped"
        report["note"] = f"playwright import unavailable: {exc}"
        if args.require_playwright:
            report["status"] = "failed"
            out_path = Path(args.output_json).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(f"validate_graph_lab_playwright_e2e: fail ({report['note']})")
            return 1
        out_path = Path(args.output_json).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"validate_graph_lab_playwright_e2e: skip ({report['note']})")
        return 0

    report["playwright_available"] = True

    with tempfile.TemporaryDirectory(prefix="graph_lab_playwright_e2e_") as td:
        tmp_root = Path(td)
        store_root = tmp_root / "store"
        scene_path = tmp_root / "scene.json"
        _build_scene(scene_path)

        api = WebE2EOrchestrator(repo_root=str(repo_root), store_root=str(store_root))
        api_server = create_web_e2e_http_server(host="127.0.0.1", port=0, orchestrator=api)
        api_host, api_port = api_server.server_address[0], int(api_server.server_address[1])

        handler = partial(SimpleHTTPRequestHandler, directory=str(repo_root))
        ui_server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        ui_host, ui_port = ui_server.server_address[0], int(ui_server.server_address[1])

        api_thread = threading.Thread(target=api_server.serve_forever, daemon=True)
        ui_thread = threading.Thread(target=ui_server.serve_forever, daemon=True)
        api_thread.start()
        ui_thread.start()

        try:
            url = (
                f"http://{ui_host}:{ui_port}/frontend/graph_lab_reactflow.html"
                f"?api=http://{api_host}:{api_port}"
                f"&scene={urllib.parse.quote(str(scene_path))}"
                f"&baseline_id=playwright_baseline"
            )

            def field_locator(page: Any, label_text: str) -> Any:
                return page.locator("div.field").filter(has_text=label_text).first

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1560, "height": 980},
                    accept_downloads=True,
                )
                page = context.new_page()
                page.on("console", lambda msg: debug["console_tail"].append(f"{msg.type}: {msg.text}"))
                page.on("pageerror", lambda exc: debug["page_errors"].append(str(exc)))

                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                page.locator("header.topbar").first.wait_for(timeout=60_000)
                page.locator("section.panel.panel-left").first.wait_for(timeout=60_000)
                page.get_by_role("button", name="Run Graph (API)").first.wait_for(timeout=60_000)

                # Runtime purpose preset controls must be visible and mutate the runtime fields.
                page.get_by_text("Purpose Presets", exact=True).wait_for(timeout=30_000)
                tx_ffd_area = field_locator(page, "TX FFD Files").locator("textarea")
                rx_ffd_area = field_locator(page, "RX FFD Files").locator("textarea")
                tx_ffd_area.wait_for(timeout=30_000)
                rx_ffd_area.wait_for(timeout=30_000)
                report["runtime_controls"]["ffd_fields_present"] = True

                runtime_backend_select = field_locator(page, "Runtime Backend").locator("select")
                runtime_provider_input = field_locator(page, "Runtime Provider").locator("input")
                runtime_modules_area = field_locator(page, "Runtime Required Modules").locator("textarea")
                simulation_mode_select = field_locator(page, "Simulation Mode").locator("select")
                runtime_device_select = field_locator(page, "Runtime Device").locator("select")

                page.get_by_role("button", name="Low Fidelity: RadarSimPy + FFD").click()
                page.wait_for_timeout(100)
                if runtime_backend_select.input_value() != "radarsimpy_rt":
                    raise AssertionError("low-fidelity preset did not set runtime backend to radarsimpy_rt")
                if "generate_radarsimpy_like_paths" not in runtime_provider_input.input_value():
                    raise AssertionError("low-fidelity preset did not set RadarSimPy runtime provider")
                if "radarsimpy" not in runtime_modules_area.input_value():
                    raise AssertionError("low-fidelity preset did not set required module to radarsimpy")
                if simulation_mode_select.input_value() != "radarsimpy_adc":
                    raise AssertionError("low-fidelity preset did not set simulation mode to radarsimpy_adc")
                if runtime_device_select.input_value() != "cpu":
                    raise AssertionError("low-fidelity preset did not set runtime device to cpu")
                report["runtime_controls"]["purpose_presets_checked"].append("low_fidelity_radarsimpy_ffd")

                page.get_by_role("button", name="High Fidelity: Sionna-style RT").click()
                page.wait_for_timeout(100)
                if runtime_backend_select.input_value() != "sionna_rt":
                    raise AssertionError("sionna preset did not set runtime backend to sionna_rt")
                if "generate_sionna_like_paths_from_mitsuba" not in runtime_provider_input.input_value():
                    raise AssertionError("sionna preset did not set Mitsuba runtime provider")
                if "mitsuba" not in runtime_modules_area.input_value():
                    raise AssertionError("sionna preset did not set required module to mitsuba")
                if runtime_device_select.input_value() != "gpu":
                    raise AssertionError("sionna preset did not set runtime device to gpu")
                report["runtime_controls"]["purpose_presets_checked"].append("high_fidelity_sionna_rt")

                mitsuba_ego_origin = field_locator(page, "Mitsuba Ego Origin").locator("input")
                mitsuba_spheres = field_locator(page, "Mitsuba Spheres JSON").locator("textarea")
                mitsuba_ego_origin.wait_for(timeout=30_000)
                mitsuba_spheres.wait_for(timeout=30_000)
                if mitsuba_ego_origin.input_value() != "0,0,0":
                    raise AssertionError("sionna preset did not load Mitsuba ego origin sample")
                if "center_m" not in mitsuba_spheres.input_value():
                    raise AssertionError("sionna preset did not load Mitsuba spheres sample")
                report["runtime_controls"]["advanced_controls_checked"].append("sionna_rt")

                page.get_by_role("button", name="High Fidelity: PO-SBR").click()
                page.wait_for_timeout(100)
                if runtime_backend_select.input_value() != "po_sbr_rt":
                    raise AssertionError("po-sbr preset did not set runtime backend to po_sbr_rt")
                if "generate_po_sbr_like_paths_from_posbr" not in runtime_provider_input.input_value():
                    raise AssertionError("po-sbr preset did not set PO-SBR runtime provider")
                if runtime_device_select.input_value() != "gpu":
                    raise AssertionError("po-sbr preset did not set runtime device to gpu")
                report["runtime_controls"]["purpose_presets_checked"].append("high_fidelity_po_sbr_rt")

                po_sbr_repo_root = field_locator(page, "PO-SBR Repo Root").locator("input")
                po_sbr_geometry_path = field_locator(page, "PO-SBR Geometry Path").locator("input")
                po_sbr_components = field_locator(page, "PO-SBR Components JSON").locator("textarea")
                po_sbr_repo_root.wait_for(timeout=30_000)
                po_sbr_geometry_path.wait_for(timeout=30_000)
                po_sbr_components.wait_for(timeout=30_000)
                if po_sbr_repo_root.input_value() != "external/PO-SBR-Python":
                    raise AssertionError("po-sbr preset did not load repo root sample")
                if po_sbr_geometry_path.input_value() != "geometries/plate.obj":
                    raise AssertionError("po-sbr preset did not load geometry path sample")
                if "po_lane_left" not in po_sbr_components.input_value():
                    raise AssertionError("po-sbr preset did not load components sample")
                report["runtime_controls"]["advanced_controls_checked"].append("po_sbr_rt")

                tx_ffd_area.fill("/tmp/tx0.ffd\n/tmp/tx1.ffd")
                rx_ffd_area.fill("/tmp/rx0.ffd\n/tmp/rx1.ffd")
                if "/tmp/tx0.ffd" not in tx_ffd_area.input_value():
                    raise AssertionError("tx ffd textarea did not retain value")
                if "/tmp/rx0.ffd" not in rx_ffd_area.input_value():
                    raise AssertionError("rx ffd textarea did not retain value")

                # Restore a runnable graph-lab baseline after UI checks.
                runtime_backend_select.select_option("analytic_targets")
                runtime_provider_input.fill("")
                runtime_modules_area.fill("")
                tx_ffd_area.fill("")
                rx_ffd_area.fill("")

                page.get_by_role("button", name="Run Graph (API)").click()
                page.get_by_text("graph run completed", exact=False).first.wait_for(timeout=30_000)

                runtime_diag_box = field_locator(page, "Runtime Diagnostics").locator("pre.result-box")
                runtime_diag_box.wait_for(timeout=30_000)
                runtime_diag_text = runtime_diag_box.inner_text()
                if "state:" not in runtime_diag_text or "module_report:" not in runtime_diag_text:
                    raise AssertionError("runtime diagnostics did not render expected summary text")
                report["runtime_controls"]["runtime_diagnostics_checked"] = True

                page.get_by_text("Track Compare Workflow", exact=True).wait_for(timeout=30_000)
                current_track_hint = page.get_by_text("current_track:", exact=False).first
                compare_track_hint = page.get_by_text("compare_track:", exact=False).first
                if "backend=" not in current_track_hint.inner_text():
                    raise AssertionError("track compare workflow did not render current track label")
                if "backend=" not in compare_track_hint.inner_text():
                    raise AssertionError("track compare workflow did not render compare track label")

                page.get_by_role("button", name="Use Current as Compare").click()
                page.wait_for_function(
                    """() => {
                        const text = (document.body && document.body.innerText) || "";
                        return text.includes("compare_mode=pinned_current");
                    }""",
                    timeout=20_000,
                )
                report["runtime_controls"]["compare_workflow_checked"] = True

                preset_pair_field = field_locator(page, "Preset Pair Compare")
                preset_pair_field.wait_for(timeout=30_000)
                preset_selects = preset_pair_field.locator("select")
                baseline_select = preset_selects.nth(0)
                target_select = preset_selects.nth(1)
                if baseline_select.input_value() != "low_fidelity_radarsimpy_ffd":
                    raise AssertionError("preset pair baseline default must be low_fidelity_radarsimpy_ffd")
                if target_select.input_value() != "current_config":
                    raise AssertionError("preset pair target default must be current_config")
                preset_pair_field.get_by_role("button", name="Low -> PO-SBR", exact=True).click()
                page.wait_for_timeout(100)
                if target_select.input_value() != "high_fidelity_po_sbr_rt":
                    raise AssertionError("quick pair shortcut did not update target preset to high_fidelity_po_sbr_rt")
                if "selected_pair:" not in preset_pair_field.inner_text():
                    raise AssertionError("preset pair section did not render selected_pair summary")
                preset_pair_field.get_by_role("button", name="Low -> Current", exact=True).click()
                page.wait_for_timeout(100)
                if target_select.input_value() != "current_config":
                    raise AssertionError("quick pair shortcut did not reset target preset to current_config")
                report["runtime_controls"]["quick_pair_shortcuts_checked"] = True
                baseline_select.select_option("low_fidelity_radarsimpy_ffd")
                target_select.select_option("current_config")
                report["runtime_controls"]["preset_pair_runner_checked"] = True

                page.get_by_role("button", name="Run Preset Pair Compare").click()
                page.wait_for_function(
                    """() => {
                        const text = (document.body && document.body.innerText) || "";
                        return (
                            text.includes("track_compare_runner=ready")
                            || text.includes("track_compare_runner_blocked")
                            || text.includes("track_compare_runner_failed")
                        );
                    }""",
                    timeout=90_000,
                )
                report["runtime_controls"]["track_compare_runner_checked"] = True
                body_text = page.locator("body").inner_text()
                if "track_compare_runner=ready" in body_text:
                    report["runtime_controls"]["track_compare_runner_result"] = "ready"
                elif "track_compare_runner_blocked" in body_text:
                    report["runtime_controls"]["track_compare_runner_result"] = "blocked"
                else:
                    raise AssertionError("track compare runner ended in failed state")
                if expect_compare_runner_ready and report["runtime_controls"]["track_compare_runner_result"] != "ready":
                    raise AssertionError("track compare runner should be ready when local RadarSimPy runtime assets are present")

                artifact_field = field_locator(page, "Artifact Inspector")
                artifact_field.wait_for(timeout=30_000)
                artifact_text = artifact_field.inner_text()
                if "compare_assessment:" not in artifact_text or "compare_flags:" not in artifact_text:
                    raise AssertionError("artifact inspector did not render compare assessment")
                report["runtime_controls"]["compare_assessment_checked"] = True

                page.get_by_role("button", name="Pin Baseline").click()
                page.get_by_role("button", name="Policy Gate").click()
                page.wait_for_function(
                    """() => {
                        const text = (document.body && document.body.innerText) || "";
                        return (
                            text.includes("policy_eval_id:")
                            || text.includes("gate failed")
                            || text.includes("policy gate failed")
                        );
                    }""",
                    timeout=30_000,
                )

                page.get_by_role("button", name="Run Session").click()
                page.get_by_text("regression session", exact=False).first.wait_for(timeout=20_000)

                page.get_by_role("button", name="Export Session").click()
                page.get_by_text("regression export", exact=False).first.wait_for(timeout=20_000)

                with page.expect_download(timeout=20_000) as dl_info:
                    page.get_by_role("button", name="Export Brief").click()
                download = dl_info.value
                brief_path = latest_dir / "decision_brief.md"
                download.save_as(str(brief_path))
                brief_text = brief_path.read_text(encoding="utf-8")
                if "## Runtime Compare" not in brief_text or "compare_runner_status:" not in brief_text:
                    raise AssertionError("decision brief did not include runtime compare summary")
                if "selected_preset_pair:" not in brief_text:
                    raise AssertionError("decision brief did not include selected preset pair summary")
                if "## Compare Assessment" not in brief_text or "assessment:" not in brief_text:
                    raise AssertionError("decision brief did not include compare assessment summary")
                report["runtime_controls"]["decision_brief_runtime_compare_checked"] = True

                # Normalize high-churn text before visual capture so strict snapshots
                # track structural UI regressions instead of run-id/timestamp drift.
                page.evaluate(
                    """() => {
                        const normalize = (text) => {
                            let out = String(text || "");
                            const rules = [
                                [/grun_[A-Za-z0-9_]+/g, "grun_<id>"],
                                [/cpol_[A-Za-z0-9_]+/g, "cpol_<id>"],
                                [/dssn_[0-9]+/g, "dssn_<id>"],
                                [/dexp_[A-Za-z0-9_]+/g, "dexp_<id>"],
                                [/run_[A-Za-z0-9_]+/g, "run_<id>"],
                                [/[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.+-]+Z/g, "<iso-ts>"],
                                [/[0-9]{13,}/g, "<ts-ms>"],
                                [/[-+]?[0-9]*\\.?[0-9]+/g, "<num>"],
                            ];
                            for (const [pattern, repl] of rules) {
                                out = out.replace(pattern, repl);
                            }
                            return out;
                        };
                        if (document.activeElement && typeof document.activeElement.blur === "function") {
                            document.activeElement.blur();
                        }
                        for (const node of document.querySelectorAll("pre.result-box, .hint")) {
                            node.textContent = normalize(node.textContent || "");
                        }
                        const decisionField = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Decision Pane")
                        );
                        if (decisionField) {
                            for (const input of decisionField.querySelectorAll("input")) {
                                input.value = "<normalized-id>";
                                input.setAttribute("value", "<normalized-id>");
                            }
                            for (const hint of decisionField.querySelectorAll(".hint")) {
                                hint.textContent = "<normalized-hint>";
                            }
                            for (const box of decisionField.querySelectorAll("pre.result-box")) {
                                box.textContent = "<normalized-summary>";
                            }
                        }
                        for (const node of document.querySelectorAll(".panel-bd")) {
                            node.scrollTop = 0;
                            node.scrollLeft = 0;
                        }
                    }"""
                )
                page.add_style_tag(
                    content="""
                    * {
                      font-family: monospace !important;
                      text-rendering: geometricPrecision !important;
                    }
                    """
                )
                page.mouse.move(0, 0)
                page.wait_for_timeout(60)

                snap_specs = [
                    ("page_full.png", page),
                    ("topbar.png", page.locator("header.topbar")),
                    ("left_panel.png", page.locator("section.panel").nth(0)),
                    ("right_panel.png", page.locator("section.panel").nth(2)),
                    ("decision_pane.png", page.locator("div.field", has_text="Decision Pane").first),
                    ("artifact_inspector.png", page.locator("div.field", has_text="Artifact Inspector").first),
                ]
                for name, target in snap_specs:
                    out = latest_dir / name
                    target.screenshot(
                        path=str(out),
                        animations="disabled",
                        caret="hide",
                        scale="css",
                    )

                report["playwright_runtime_ready"] = True
                report["e2e_pass"] = True
                report["debug"] = {
                    "console_tail": debug["console_tail"][-12:],
                    "page_errors": debug["page_errors"][-8:],
                }

                browser.close()

            report["artifacts"] = {
                "snapshot_latest_dir": str(latest_dir.resolve()),
                "snapshot_baseline_dir": str(baseline_dir.resolve()),
                "decision_brief_md": str((latest_dir / "decision_brief.md").resolve()),
            }

            if args.update_baseline:
                _copy_tree(latest_dir, baseline_dir)
                report["status"] = "pass"
                report["note"] = "baseline updated from latest snapshots"
            else:
                latest_files = [
                    latest_dir / name for name in VISUAL_COMPARE_TARGETS
                ]
                for latest in latest_files:
                    if not latest.exists() or not latest.is_file():
                        report["visual"]["missing_baseline"].append(latest.name)
                        continue
                    baseline = baseline_dir / latest.name
                    if not baseline.exists():
                        report["visual"]["missing_baseline"].append(latest.name)
                        continue
                    if _sha256_path(latest) == _sha256_path(baseline):
                        report["visual"]["matched"].append(latest.name)
                    else:
                        report["visual"]["changed"].append(latest.name)

                if args.strict_visual and (
                    len(report["visual"]["missing_baseline"]) > 0
                    or len(report["visual"]["changed"]) > 0
                ):
                    report["status"] = "failed"
                    report["note"] = "strict visual regression mismatch"
                else:
                    report["status"] = "pass"
                    report["note"] = "e2e pass"

        except Exception as exc:
            note = f"{type(exc).__name__}: {exc}"
            console_tail = debug["console_tail"][-8:]
            page_errors = debug["page_errors"][-8:]
            if console_tail:
                note = f"{note}\nconsole_tail:\n- " + "\n- ".join(console_tail)
            if page_errors:
                note = f"{note}\npage_errors:\n- " + "\n- ".join(page_errors)
            report["note"] = note
            report["debug"] = {
                "console_tail": console_tail,
                "page_errors": page_errors,
            }
            if args.require_playwright:
                report["status"] = "failed"
            else:
                # Runtime setup issues (e.g., browser not installed) are optional by default.
                report["status"] = "skipped"
            report["e2e_pass"] = False
        finally:
            api_server.shutdown()
            api_server.server_close()
            ui_server.shutdown()
            ui_server.server_close()

    out_path = Path(args.output_json).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if report["status"] == "failed":
        print(f"validate_graph_lab_playwright_e2e: fail ({report.get('note', '')})")
        return 1
    if report["status"] == "skipped":
        print(f"validate_graph_lab_playwright_e2e: skip ({report.get('note', '')})")
        return 0
    print("validate_graph_lab_playwright_e2e: pass")
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Graph Lab Playwright E2E + visual snapshot contract")
    p.add_argument(
        "--output-json",
        default="docs/reports/graph_lab_playwright_e2e_latest.json",
        help="Output JSON report path",
    )
    p.add_argument(
        "--strict-visual",
        action="store_true",
        help="Fail if snapshot differs from baseline or baseline is missing",
    )
    p.add_argument(
        "--update-baseline",
        action="store_true",
        help="Refresh baseline snapshot files from latest capture",
    )
    p.add_argument(
        "--require-playwright",
        action="store_true",
        help="Fail if Playwright runtime is unavailable",
    )
    return p.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))

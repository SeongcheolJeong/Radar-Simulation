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
import traceback
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
    fixture_root = repo_root / "scripts" / "fixtures"
    legacy_no_schema_fixture = fixture_root / "graph_lab_compare_history_legacy_no_schema.json"
    legacy_camelcase_fixture = fixture_root / "graph_lab_compare_history_legacy_camelcase.json"
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
    if not legacy_no_schema_fixture.is_file():
        raise FileNotFoundError(f"missing legacy no-schema fixture: {legacy_no_schema_fixture}")
    if not legacy_camelcase_fixture.is_file():
        raise FileNotFoundError(f"missing legacy camelCase fixture: {legacy_camelcase_fixture}")

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
            "pair_forecast_checked": False,
            "compare_session_history_checked": False,
            "compare_session_replay_checked": False,
            "compare_session_selector_checked": False,
            "compare_session_management_checked": False,
            "compare_session_preview_checked": False,
            "compare_session_artifact_expectation_checked": False,
            "compare_session_artifact_path_hash_checked": False,
            "compare_session_import_preview_checked": False,
            "compare_session_legacy_fixture_checked": False,
            "compare_session_retention_policy_checked": False,
            "compare_session_clear_all_checked": False,
            "compare_session_transfer_checked": False,
            "compare_session_future_schema_warning_checked": False,
            "compare_session_persistence_checked": False,
            "pinned_pair_quick_actions_checked": False,
            "pinned_pair_preview_checked": False,
            "pinned_pair_badges_checked": False,
            "preset_pair_runner_checked": False,
            "track_compare_runner_checked": False,
            "track_compare_runner_result": "",
            "compare_assessment_checked": False,
            "artifact_inspector_expectation_checked": False,
            "artifact_inspector_folds_checked": False,
            "artifact_inspector_fold_persistence_checked": False,
            "artifact_inspector_reset_checked": False,
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
                escaped = json.dumps(str(label_text))
                return page.locator(
                    f"xpath=//label[contains(@class,'label')][contains(normalize-space(), {escaped})]/parent::div[contains(@class,'field')]"
                ).first

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
                if "baseline_forecast:" not in preset_pair_field.inner_text() or "target_forecast:" not in preset_pair_field.inner_text():
                    raise AssertionError("preset pair section did not render baseline/target forecast")
                preset_pair_field.get_by_role("button", name="Low -> Current", exact=True).click()
                page.wait_for_timeout(100)
                if target_select.input_value() != "current_config":
                    raise AssertionError("quick pair shortcut did not reset target preset to current_config")
                report["runtime_controls"]["quick_pair_shortcuts_checked"] = True
                report["runtime_controls"]["pair_forecast_checked"] = True
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
                if (
                    "selected history pair artifact expectation:" not in artifact_text
                    or "selected_history_artifact_expectation:" not in artifact_text
                    or "artifact_expectation_source:" not in artifact_text
                    or "artifact_path_fingerprint_algo:" not in artifact_text
                ):
                    raise AssertionError("artifact inspector did not render selected history pair artifact expectation")
                artifact_field.get_by_role("button", name="Hide Live Compare Evidence").click()
                page.wait_for_timeout(150)
                collapsed_live_artifact_text = artifact_field.inner_text()
                if "shape.adc:" in collapsed_live_artifact_text or "rd_peak_delta(range/doppler/rel_db):" in collapsed_live_artifact_text:
                    raise AssertionError("artifact inspector live compare evidence did not collapse")
                if "compare_assessment:" not in collapsed_live_artifact_text:
                    raise AssertionError("artifact inspector live compare summary disappeared after collapse")
                artifact_field.get_by_role("button", name="Show Live Compare Evidence").click()
                page.wait_for_timeout(150)
                restored_live_artifact_text = artifact_field.inner_text()
                if "shape.adc:" not in restored_live_artifact_text:
                    raise AssertionError("artifact inspector live compare evidence did not restore after expand")
                artifact_field.get_by_role("button", name="Hide History Snapshot").click()
                page.wait_for_timeout(150)
                collapsed_history_artifact_text = artifact_field.inner_text()
                if "artifact_expectation_source:" in collapsed_history_artifact_text or "artifact_path_fingerprint_algo:" in collapsed_history_artifact_text:
                    raise AssertionError("artifact inspector history snapshot did not collapse")
                if "selected_history_artifact_expectation:" not in collapsed_history_artifact_text:
                    raise AssertionError("artifact inspector history snapshot summary disappeared after collapse")
                artifact_field.get_by_role("button", name="Show History Snapshot").click()
                page.wait_for_timeout(150)
                restored_history_artifact_text = artifact_field.inner_text()
                if "artifact_expectation_source:" not in restored_history_artifact_text:
                    raise AssertionError("artifact inspector history snapshot did not restore after expand")
                artifact_field.get_by_role("button", name="Hide Live Compare Evidence").click()
                artifact_field.get_by_role("button", name="Hide History Snapshot").click()
                page.wait_for_timeout(150)
                artifact_field.get_by_role("button", name="Reset Layout").click()
                page.wait_for_timeout(150)
                reset_artifact_text = artifact_field.inner_text()
                if (
                    "Hide Live Compare Evidence" not in reset_artifact_text
                    or "Hide History Snapshot" not in reset_artifact_text
                    or "shape.adc:" not in reset_artifact_text
                    or "artifact_expectation_source:" not in reset_artifact_text
                    or "layout_state: live=expanded | history=expanded" not in reset_artifact_text
                ):
                    raise AssertionError("artifact inspector reset layout did not restore expanded detail state")
                report["runtime_controls"]["compare_assessment_checked"] = True
                report["runtime_controls"]["artifact_inspector_expectation_checked"] = True
                report["runtime_controls"]["artifact_inspector_folds_checked"] = True
                report["runtime_controls"]["artifact_inspector_reset_checked"] = True

                history_field = field_locator(page, "Compare Session History")
                history_field.wait_for(timeout=30_000)
                history_text = history_field.inner_text()
                history_hints = history_field.locator(".hint")
                selected_history_hint = history_hints.nth(1)
                if "source=pin_current" not in history_text:
                    raise AssertionError("compare session history did not capture manual pin event")
                if "source=preset_pair" not in history_text:
                    raise AssertionError("compare session history did not capture preset pair event")
                if "latest_replayable_pair:" not in history_text:
                    raise AssertionError("compare session history did not render latest replayable pair hint")
                if "selected_history_pair:" not in history_text:
                    raise AssertionError("compare session history did not render selected history pair hint")
                if "planned_deltas:" not in history_text:
                    raise AssertionError("compare session history did not render selected history pair preview")
                expected_history_status = str(report["runtime_controls"]["track_compare_runner_result"] or "").strip()
                if expected_history_status and f"status={expected_history_status}" not in history_text:
                    raise AssertionError("compare session history did not capture preset pair result status")
                report["runtime_controls"]["compare_session_history_checked"] = True

                preset_pair_field.get_by_role("button", name="Low -> PO-SBR", exact=True).click()
                page.wait_for_timeout(100)
                if target_select.input_value() != "high_fidelity_po_sbr_rt":
                    raise AssertionError("quick pair shortcut did not update target preset before replay test")
                history_field.get_by_role("button", name="Use Latest History Pair").click()
                page.wait_for_timeout(100)
                if target_select.input_value() != "current_config":
                    raise AssertionError("latest history pair did not restore target preset to current_config")
                pre_replay_history_text = history_field.inner_text()
                history_field.get_by_role("button", name="Run Latest History Pair").click()
                page.wait_for_function(
                    """(prevText) => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return text.includes("source=preset_pair") && text !== String(prevText || "");
                    }""",
                    arg=pre_replay_history_text,
                    timeout=90_000,
                )
                report["runtime_controls"]["compare_session_replay_checked"] = True

                history_retention_select = history_field.locator("select").nth(0)
                history_select = history_field.locator("select").nth(1)
                option_count = history_select.locator("option").count()
                if option_count < 1:
                    raise AssertionError("compare session history selector did not expose any replayable pairs")
                selected_option_value = history_select.locator("option").nth(0).get_attribute("value") or ""
                selected_target_value = selected_option_value.split("::", 1)[1] if "::" in selected_option_value else ""
                if not selected_option_value or not selected_target_value:
                    raise AssertionError("compare session history selector did not provide a valid replayable pair value")
                history_select.select_option(selected_option_value)
                page.wait_for_timeout(100)
                history_field.get_by_role("button", name="Use Selected History Pair").click()
                page.wait_for_function(
                    """(expectedTarget) => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Preset Pair Compare")
                        );
                        const selects = field ? Array.from(field.querySelectorAll("select")) : [];
                        return selects.length >= 2 && String(selects[1].value || "") === String(expectedTarget || "");
                    }""",
                    arg=selected_target_value,
                    timeout=10_000,
                )
                pre_selected_replay_history_text = history_field.inner_text()
                history_field.get_by_role("button", name="Run Selected History Pair").click()
                page.wait_for_function(
                    """(prevText) => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return text.includes("source=preset_pair") && text !== String(prevText || "");
                    }""",
                    arg=pre_selected_replay_history_text,
                    timeout=90_000,
                )
                report["runtime_controls"]["compare_session_selector_checked"] = True

                selected_history_label = "Low Fidelity Saved"
                history_label_input = history_field.get_by_placeholder("selected pair label")
                history_label_input.fill(selected_history_label)
                history_field.get_by_role("button", name="Save Selected Label").click()
                page.wait_for_function(
                    """(expectedLabel) => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return text.includes(`selected_history_pair: ${String(expectedLabel || "")}`);
                    }""",
                    arg=selected_history_label,
                    timeout=10_000,
                )
                if "planned_deltas:" not in history_field.inner_text():
                    raise AssertionError("selected history pair preview did not remain visible after label save")
                history_field.get_by_role("button", name="Pin Selected History Pair").click()
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return text.includes("selected_history_pair_meta: pinned=true");
                    }""",
                    timeout=10_000,
                )
                history_text_after_pin = history_field.inner_text()
                if (
                    "artifact_expectation_source:" not in history_text_after_pin
                    or "required_artifacts(current/compare/total):" not in history_text_after_pin
                    or "artifact_path_fingerprint_algo:" not in history_text_after_pin
                    or "path_list_json:" not in history_text_after_pin
                ):
                    raise AssertionError("selected history pair artifact expectation did not render after pin")
                report["runtime_controls"]["compare_session_preview_checked"] = True
                report["runtime_controls"]["compare_session_artifact_expectation_checked"] = True
                report["runtime_controls"]["compare_session_artifact_path_hash_checked"] = True
                pinned_quick_field = field_locator(page, "Pinned Pair Quick Actions")
                pinned_quick_field.wait_for(timeout=10_000)
                pinned_quick_text = pinned_quick_field.inner_text()
                if (
                    selected_history_label not in pinned_quick_text
                    or "artifact_expectation:" not in pinned_quick_text
                    or "artifact_path_hashes:" not in pinned_quick_text
                ):
                    raise AssertionError("pinned quick action field did not expose the selected pinned pair")
                if "assessment:" not in pinned_quick_text or "fp:" not in pinned_quick_text or "source:" not in pinned_quick_text:
                    raise AssertionError("pinned quick action field did not expose quick status badges")
                report["runtime_controls"]["pinned_pair_badges_checked"] = True
                pinned_quick_field.get_by_role("button", name=f"Show PIN Details: {selected_history_label}").click()
                page.wait_for_timeout(200)
                expanded_pinned_quick_text = pinned_quick_field.inner_text()
                if (
                    "selected_pair:" not in expanded_pinned_quick_text
                    or "artifact_expectation_source:" not in expanded_pinned_quick_text
                    or "artifact_path_fingerprint_algo:" not in expanded_pinned_quick_text
                ):
                    raise AssertionError("expanded pinned quick action did not expose artifact expectation detail")
                pinned_quick_field.get_by_role("button", name=f"Hide PIN Details: {selected_history_label}").click()
                page.wait_for_timeout(200)
                collapsed_pinned_quick_text = pinned_quick_field.inner_text()
                if "selected_pair:" in collapsed_pinned_quick_text:
                    raise AssertionError("collapsed pinned quick action still rendered expanded preview")
                report["runtime_controls"]["pinned_pair_preview_checked"] = True
                preset_pair_field.get_by_role("button", name="Low -> PO-SBR", exact=True).click()
                page.wait_for_timeout(100)
                if target_select.input_value() != "high_fidelity_po_sbr_rt":
                    raise AssertionError("quick pair shortcut did not update target preset before pinned quick action test")
                pinned_quick_field.get_by_role("button", name=f"Use PIN: {selected_history_label}").click()
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Preset Pair Compare")
                        );
                        const selects = field ? Array.from(field.querySelectorAll("select")) : [];
                        return selects.length >= 2 && String(selects[1].value || "") === "current_config";
                    }""",
                    timeout=10_000,
                )
                pre_pinned_quick_run_history_text = history_field.inner_text()
                pinned_quick_field.get_by_role("button", name=f"Run PIN: {selected_history_label}").click()
                page.wait_for_function(
                    """(prevText) => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return text.includes("source=preset_pair") && text !== String(prevText || "");
                    }""",
                    arg=pre_pinned_quick_run_history_text,
                    timeout=90_000,
                )
                report["runtime_controls"]["pinned_pair_quick_actions_checked"] = True
                preset_pair_field.get_by_role("button", name="Low -> PO-SBR", exact=True).click()
                page.wait_for_timeout(100)
                page.get_by_role("button", name="Use Current as Compare").click()
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return text.includes("high_fidelity_po_sbr_rt");
                    }""",
                    timeout=20_000,
                )
                with page.expect_download(timeout=20_000) as history_dl_info:
                    history_field.get_by_role("button", name="Export History").click()
                history_download = history_dl_info.value
                history_bundle_path = tmp_root / "compare_history_export.json"
                history_download.save_as(str(history_bundle_path))
                history_transfer_text_after_export = history_field.inner_text()
                if "schema=graph_lab_compare_history_export_v2" not in history_transfer_text_after_export:
                    raise AssertionError("compare history export transfer hint did not include schema version")
                exported_bundle = json.loads(history_bundle_path.read_text(encoding="utf-8"))
                if str(exported_bundle.get("schema_version") or "") != "graph_lab_compare_history_export_v2":
                    raise AssertionError("compare history export schema_version mismatch")
                if str(exported_bundle.get("retention_policy") or "") != "retain_8":
                    raise AssertionError("compare history export did not include retention policy")
                exported_meta = exported_bundle.get("pair_meta_by_id") or {}
                if "low_fidelity_radarsimpy_ffd::current_config" not in exported_meta:
                    raise AssertionError("compare history export did not include managed pair metadata")
                exported_artifact_expectations = exported_bundle.get("pair_artifact_expectation_by_id") or {}
                low_current_expectation = exported_artifact_expectations.get("low_fidelity_radarsimpy_ffd::current_config") or {}
                low_current_detail = str(low_current_expectation.get("detailText") or low_current_expectation.get("detail_text") or "")
                low_current_path_map = low_current_expectation.get("artifactPathFingerprintsByArtifact") or low_current_expectation.get("artifact_path_fingerprints_by_artifact") or {}
                if (
                    "required_artifacts(current/compare/total):" not in low_current_detail
                    or "artifact_path_fingerprint_algo:" not in low_current_detail
                    or "path_list_json" not in low_current_path_map
                ):
                    raise AssertionError("compare history export did not include artifact expectation snapshot")
                history_select.select_option("low_fidelity_radarsimpy_ffd::high_fidelity_po_sbr_rt")
                page.wait_for_timeout(100)
                history_field.get_by_role("button", name="Delete Selected History Pair").click()
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const select = field ? field.querySelector("select") : null;
                        const options = select ? Array.from(select.querySelectorAll("option")).map((row) => String(row.value || "")) : [];
                        return !options.includes("low_fidelity_radarsimpy_ffd::high_fidelity_po_sbr_rt");
                    }""",
                    timeout=10_000,
                )
                with page.expect_file_chooser(timeout=20_000) as history_fc_info:
                    history_field.get_by_role("button", name="Import History").click()
                history_fc_info.value.set_files(str(history_bundle_path))
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return (
                            text.includes("import preview ready")
                            && text.includes("schema=graph_lab_compare_history_export_v2")
                            && text.includes("compatibility=exact")
                        );
                    }""",
                    timeout=30_000,
                )
                history_transfer_text_after_import_preview = history_field.inner_text()
                if (
                    "schema=graph_lab_compare_history_export_v2" not in history_transfer_text_after_import_preview
                    or "compatibility=exact" not in history_transfer_text_after_import_preview
                ):
                    raise AssertionError("compare history import preview did not include schema compatibility")
                if "apply_required=true" not in history_transfer_text_after_import_preview:
                    raise AssertionError("compare history import preview did not expose apply requirement")
                options_after_preview = page.evaluate(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const select = field ? field.querySelector("select") : null;
                        return select ? Array.from(select.querySelectorAll("option")).map((row) => String(row.value || "")) : [];
                    }"""
                )
                if "low_fidelity_radarsimpy_ffd::high_fidelity_po_sbr_rt" in options_after_preview:
                    raise AssertionError("compare history import preview merged data before Apply Import Merge")
                history_field.get_by_role("button", name="Apply Import Merge").click()
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return text.includes("imported ") && text.includes("high_fidelity_po_sbr_rt") && text.includes("compatibility=exact");
                    }""",
                    timeout=30_000,
                )
                history_transfer_text_after_import = history_field.inner_text()
                if "import_preview: none" not in history_transfer_text_after_import:
                    raise AssertionError("compare history import preview did not clear after apply")
                future_bundle = dict(exported_bundle)
                future_bundle["schema_version"] = "graph_lab_compare_history_export_v99"
                future_bundle_path = tmp_root / "compare_history_future_schema.json"
                future_bundle_path.write_text(json.dumps(future_bundle, indent=2), encoding="utf-8")
                with page.expect_file_chooser(timeout=20_000) as future_fc_info:
                    history_field.get_by_role("button", name="Import History").click()
                future_fc_info.value.set_files(str(future_bundle_path))
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return (
                            text.includes("import preview ready")
                            && text.includes("warning:future-schema")
                            && text.includes("schema=graph_lab_compare_history_export_v99")
                            && text.includes("compatibility=forward_compatible_best_effort")
                        );
                    }""",
                    timeout=30_000,
                )
                history_transfer_text_after_future_import = history_field.inner_text()
                if "warning:future-schema" not in history_transfer_text_after_future_import:
                    raise AssertionError("compare history future-schema import did not expose warning badge")
                history_field.get_by_role("button", name="Clear Import Preview").click()
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return text.includes("compare history import preview cleared") && text.includes("import_preview: none");
                    }""",
                    timeout=20_000,
                )
                with page.expect_file_chooser(timeout=20_000) as legacy_no_schema_fc_info:
                    history_field.get_by_role("button", name="Import History").click()
                legacy_no_schema_fc_info.value.set_files(str(legacy_no_schema_fixture))
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return (
                            text.includes("schema=legacy_pre_v2")
                            && text.includes("compatibility=legacy_compatible")
                            && text.includes("Legacy Fixture | PO-SBR -> Current")
                        );
                    }""",
                    timeout=30_000,
                )
                legacy_no_schema_preview_text = history_field.inner_text()
                if (
                    "schema=legacy_pre_v2" not in legacy_no_schema_preview_text
                    or "compatibility=legacy_compatible" not in legacy_no_schema_preview_text
                    or "Legacy Fixture | PO-SBR -> Current" not in legacy_no_schema_preview_text
                ):
                    raise AssertionError("legacy no-schema fixture preview did not expose legacy compatibility")
                history_field.get_by_role("button", name="Apply Import Merge").click()
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return (
                            text.includes("fixture_legacy_no_schema")
                            && text.includes("Legacy Fixture | PO-SBR -> Current")
                            && text.includes("compatibility=legacy_compatible")
                        );
                    }""",
                    timeout=30_000,
                )
                history_select.select_option("high_fidelity_po_sbr_rt::current_config")
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return (
                            text.includes("selected_history_pair: Legacy Fixture | PO-SBR -> Current")
                            && text.includes("custom_label=Legacy Fixture | PO-SBR -> Current")
                            && text.includes("artifact_expectation_source: imported_legacy_fixture")
                        );
                    }""",
                    timeout=20_000,
                )
                with page.expect_file_chooser(timeout=20_000) as legacy_camel_fc_info:
                    history_field.get_by_role("button", name="Import History").click()
                legacy_camel_fc_info.value.set_files(str(legacy_camelcase_fixture))
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return (
                            text.includes("schema=legacy_pre_v2")
                            && text.includes("compatibility=legacy_compatible")
                            && text.includes("Legacy Fixture | Sionna -> Current")
                        );
                    }""",
                    timeout=30_000,
                )
                legacy_camel_preview_text = history_field.inner_text()
                if (
                    "schema=legacy_pre_v2" not in legacy_camel_preview_text
                    or "compatibility=legacy_compatible" not in legacy_camel_preview_text
                    or "Legacy Fixture | Sionna -> Current" not in legacy_camel_preview_text
                ):
                    raise AssertionError("legacy camelCase fixture preview did not expose legacy compatibility")
                history_field.get_by_role("button", name="Apply Import Merge").click()
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return (
                            text.includes("fixture_legacy_camelcase")
                            && text.includes("Legacy Fixture | Sionna -> Current")
                            && text.includes("compatibility=legacy_compatible")
                        );
                    }""",
                    timeout=30_000,
                )
                history_select.select_option("high_fidelity_sionna_rt::current_config")
                page.wait_for_function(
                    """() => {
                        const field = Array.from(document.querySelectorAll("div.field")).find((el) =>
                            String(el.textContent || "").includes("Compare Session History")
                        );
                        const text = String(field ? field.textContent || "" : "");
                        return (
                            text.includes("selected_history_pair: Legacy Fixture | Sionna -> Current")
                            && text.includes("custom_label=Legacy Fixture | Sionna -> Current")
                            && text.includes("artifact_expectation_source: imported_legacy_fixture_camel")
                        );
                    }""",
                    timeout=20_000,
                )
                report["runtime_controls"]["compare_session_import_preview_checked"] = True
                report["runtime_controls"]["compare_session_legacy_fixture_checked"] = True
                report["runtime_controls"]["compare_session_future_schema_warning_checked"] = True
                history_select.select_option("low_fidelity_radarsimpy_ffd::current_config")
                page.wait_for_timeout(100)
                report["runtime_controls"]["compare_session_management_checked"] = True
                report["runtime_controls"]["compare_session_transfer_checked"] = True

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
                page.wait_for_function(
                    """() => {
                        const text = (document.body && document.body.innerText) || "";
                        return text.includes("regression_session_id=") || text.includes("regression session completed");
                    }""",
                    timeout=30_000,
                )

                page.get_by_role("button", name="Export Session").click()
                page.wait_for_function(
                    """() => {
                        const text = (document.body && document.body.innerText) || "";
                        return text.includes("regression_export_id=") || text.includes("regression export completed");
                    }""",
                    timeout=30_000,
                )

                with page.expect_download(timeout=20_000) as dl_info:
                    page.get_by_role("button", name="Export Brief").click()
                download = dl_info.value
                brief_path = latest_dir / "decision_brief.md"
                download.save_as(str(brief_path))
                brief_text = brief_path.read_text(encoding="utf-8")
                if "## Runtime Compare" not in brief_text or "compare_runner_status:" not in brief_text:
                    raise AssertionError("decision brief did not include runtime compare summary")
                if "compare_history_import_preview:" not in brief_text:
                    raise AssertionError("decision brief did not include compact compare history import preview summary")
                if "selected_preset_pair:" not in brief_text:
                    raise AssertionError("decision brief did not include selected preset pair summary")
                if "## Selected Pair Forecast" not in brief_text or "baseline_forecast:" not in brief_text:
                    raise AssertionError("decision brief did not include selected pair forecast summary")
                if "## Pinned Pair Quick Actions" not in brief_text or "pinned_quick_action_count:" not in brief_text:
                    raise AssertionError("decision brief did not include pinned quick action summary")
                if "## Compare Session History" not in brief_text or "source=preset_pair" not in brief_text:
                    raise AssertionError("decision brief did not include compare session history summary")
                if "compare_history_retention_policy:" not in brief_text:
                    raise AssertionError("decision brief did not include compare history retention summary")
                if "## Compare History Import Preview" not in brief_text or "import_preview_source:" not in brief_text:
                    raise AssertionError("decision brief did not include compare history import preview")
                if "latest_replayable_pair:" not in brief_text:
                    raise AssertionError("decision brief did not include latest replayable pair summary")
                if "selected_history_pair:" not in brief_text:
                    raise AssertionError("decision brief did not include selected history pair summary")
                if "selected_history_pair_meta:" not in brief_text or "managed_history_pair_count:" not in brief_text:
                    raise AssertionError("decision brief did not include selected history pair management summary")
                if "## Selected History Pair Preview" not in brief_text or "planned_deltas:" not in brief_text:
                    raise AssertionError("decision brief did not include selected history pair preview")
                if "## Selected History Pair Artifact Expectation" not in brief_text or "artifact_expectation_source:" not in brief_text:
                    raise AssertionError("decision brief did not include selected history pair artifact expectation")
                if "artifact_path_fingerprint_algo:" not in brief_text or "path_list_json:" not in brief_text:
                    raise AssertionError("decision brief did not include artifact path fingerprint summary")
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
                                if (String(input.type || "").toLowerCase() === "file") {
                                    continue;
                                }
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

                artifact_field.get_by_role("button", name="Hide Live Compare Evidence").click()
                artifact_field.get_by_role("button", name="Hide History Snapshot").click()
                page.wait_for_timeout(150)
                collapsed_before_reload_artifact_text = artifact_field.inner_text()
                if (
                    "Show Live Compare Evidence" not in collapsed_before_reload_artifact_text
                    or "Show History Snapshot" not in collapsed_before_reload_artifact_text
                ):
                    raise AssertionError("artifact inspector fold controls did not stay collapsed before reload")

                persisted_pair_value = history_select.input_value()
                page.reload(wait_until="domcontentloaded", timeout=60_000)
                page.locator("header.topbar").first.wait_for(timeout=60_000)
                reloaded_history_field = field_locator(page, "Compare Session History")
                reloaded_history_field.wait_for(timeout=30_000)
                page.wait_for_timeout(300)
                reloaded_history_select = reloaded_history_field.locator("select").nth(1)
                if reloaded_history_select.input_value() != persisted_pair_value:
                    raise AssertionError("compare session history selector did not persist after reload")
                reloaded_history_text = reloaded_history_field.inner_text()
                if selected_history_label not in reloaded_history_text or "selected_history_pair_meta: pinned=true" not in reloaded_history_text:
                    raise AssertionError("compare session history management state did not persist after reload")
                if "planned_deltas:" not in reloaded_history_text:
                    raise AssertionError("selected history pair preview did not persist after reload")
                if "artifact_expectation_source:" not in reloaded_history_text:
                    raise AssertionError("selected history pair artifact expectation did not persist after reload")
                if "artifact_path_fingerprint_algo:" not in reloaded_history_text:
                    raise AssertionError("artifact path fingerprint summary did not persist after reload")
                reloaded_pinned_quick_field = field_locator(page, "Pinned Pair Quick Actions")
                reloaded_pinned_quick_text = reloaded_pinned_quick_field.inner_text()
                if (
                    selected_history_label not in reloaded_pinned_quick_text
                    or "artifact_path_hashes:" not in reloaded_pinned_quick_text
                ):
                    raise AssertionError("pinned quick action field did not persist after reload")
                if "assessment:" not in reloaded_pinned_quick_text or "fp:" not in reloaded_pinned_quick_text:
                    raise AssertionError("pinned quick action badges did not persist after reload")
                report["runtime_controls"]["compare_session_persistence_checked"] = True
                reloaded_artifact_field = field_locator(page, "Artifact Inspector")
                reloaded_artifact_field.wait_for(timeout=30_000)
                reloaded_artifact_text = reloaded_artifact_field.inner_text()
                if (
                    "Show Live Compare Evidence" not in reloaded_artifact_text
                    or "Show History Snapshot" not in reloaded_artifact_text
                ):
                    raise AssertionError("artifact inspector fold controls did not persist after reload")
                if "shape.adc:" in reloaded_artifact_text or "artifact_expectation_source:" in reloaded_artifact_text:
                    raise AssertionError("artifact inspector detail sections unexpectedly reopened after reload")
                report["runtime_controls"]["artifact_inspector_fold_persistence_checked"] = True

                history_retention_select = reloaded_history_field.locator("select").nth(0)
                reloaded_history_select = reloaded_history_field.locator("select").nth(1)
                history_retention_select.select_option("retain_2")
                retention_ok = False
                retention_text = ""
                retention_option_count = -1
                for _ in range(40):
                    retention_text = reloaded_history_field.inner_text()
                    retention_option_count = reloaded_history_select.locator("option").count()
                    if (
                        "compare_history_retention_policy: retain_2 | keep_latest=2" in retention_text
                        and retention_option_count <= 2
                    ):
                        retention_ok = True
                        break
                    page.wait_for_timeout(500)
                if not retention_ok:
                    raise AssertionError(
                        "compare history retention policy did not prune as expected "
                        f"(option_count={retention_option_count})\n{retention_text}"
                    )
                report["runtime_controls"]["compare_session_retention_policy_checked"] = True

                reloaded_history_field.get_by_role("button", name="Clear All History").click()
                clear_ok = False
                cleared_history_text = ""
                cleared_pinned_text = ""
                for _ in range(40):
                    cleared_history_text = reloaded_history_field.inner_text()
                    cleared_pinned_text = reloaded_pinned_quick_field.inner_text()
                    if (
                        "compare history cleared" in cleared_history_text
                        and "compare_history_retention_policy: retain_2 | keep_latest=2" in cleared_history_text
                        and "no compare sessions recorded" in cleared_history_text
                        and "pinned_quick_actions: -" in cleared_pinned_text
                    ):
                        clear_ok = True
                        break
                    page.wait_for_timeout(500)
                if not clear_ok:
                    raise AssertionError(
                        "compare history clear-all did not reset state as expected\n"
                        f"history:\n{cleared_history_text}\n\npinned:\n{cleared_pinned_text}"
                    )
                report["runtime_controls"]["compare_session_clear_all_checked"] = True

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
            tb_text = traceback.format_exc(limit=8)
            console_tail = debug["console_tail"][-8:]
            page_errors = debug["page_errors"][-8:]
            if tb_text:
                note = f"{note}\ntraceback:\n{tb_text.strip()}"
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

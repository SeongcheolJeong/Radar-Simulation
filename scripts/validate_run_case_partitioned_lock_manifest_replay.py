#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

import numpy as np

from avxsim.adc_pack_builder import build_measured_pack_from_adc_npz
from avxsim.measured_replay import run_measured_replay_plan, save_measured_replay_summary_json


def _make_adc(shape: tuple, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    s, c, t, r = shape
    ys = np.arange(s, dtype=np.float64)[:, None, None, None]
    yc = np.arange(c, dtype=np.float64)[None, :, None, None]
    sig = np.exp(1j * 2.0 * np.pi * (ys / max(s, 1))) * np.exp(
        1j * 2.0 * np.pi * (yc / max(c, 1))
    )
    noise = 0.03 * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    return (sig + noise).astype(np.complex64)


def _build_source_pack(pack_root: Path, scenario_id: str, seeds: List[int]) -> Dict[str, str]:
    adc_src_root = pack_root.parent / f"{pack_root.name}_adc_src"
    adc_src_root.mkdir(parents=True, exist_ok=True)
    adc_files = []
    for i, seed in enumerate(seeds):
        adc_file = adc_src_root / f"f{i:02d}.npz"
        np.savez_compressed(adc_file, adc=_make_adc((64, 32, 2, 4), seed=seed))
        adc_files.append(str(adc_file))

    summary = build_measured_pack_from_adc_npz(
        adc_npz_files=adc_files,
        output_pack_root=str(pack_root),
        scenario_id=scenario_id,
        adc_order="sctr",
        adc_key="adc",
        reference_index=0,
        nfft_range=64,
        nfft_doppler=32,
        nfft_angle=16,
        range_bin_limit=32,
    )
    return summary


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_case_partition_manifest_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        run_root = root / "source_run"
        packs_root = run_root / "packs"
        pack_a = packs_root / "pack_case_a"
        pack_b = packs_root / "pack_case_b"

        _build_source_pack(pack_a, "case_a_scene", seeds=[1, 2, 3])
        _build_source_pack(pack_b, "case_b_scene", seeds=[4, 5, 6])

        baseline_plan = [
            {
                "pack_id": pack_a.name,
                "replay_manifest_json": str(pack_a / "replay_manifest.json"),
                "output_subdir": pack_a.name,
            },
            {
                "pack_id": pack_b.name,
                "replay_manifest_json": str(pack_b / "replay_manifest.json"),
                "output_subdir": pack_b.name,
            },
        ]
        baseline_summary = run_measured_replay_plan(
            packs=baseline_plan,
            output_root=str(run_root / "measured_replay_outputs"),
            default_lock_policy={"min_pass_rate": 1.0, "max_case_fail_count": 0},
        )
        save_measured_replay_summary_json(
            str(run_root / "measured_replay_summary.json"),
            baseline_summary,
        )

        fit_json = root / "fit_reflection.json"
        fit_json.write_text(
            json.dumps(
                {
                    "version": 1,
                    "fit": {
                        "model": "reflection",
                        "best_params": {
                            "range_power_exponent": 0.5,
                            "gain_scale": 1.0,
                        },
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        case_partition_summary = root / "case_partitioned_summary.json"
        case_partition_summary.write_text(
            json.dumps(
                {
                    "version": 1,
                    "case_family_map": {
                        "case_a": "fam_a",
                        "case_b": "fam_b",
                    },
                    "final": {
                        "strategy": "mixed_family_partitioned_lock",
                        "selection_mode": "fit_partitioned_with_baseline_fallback",
                        "selected_fit_by_family": {
                            "fam_a": str(fit_json),
                            "fam_b": None,
                        },
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        out_root = root / "case_partitioned_run"
        out_summary_json = out_root / "summary.json"
        proc = subprocess.run(
            [
                "python3",
                "scripts/run_case_partitioned_lock_manifest_replay.py",
                "--case-partitioned-summary-json",
                str(case_partition_summary),
                "--case",
                f"case_a={pack_a}",
                "--case",
                f"case_b={pack_b}",
                "--allow-unlocked",
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_summary_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Case-partitioned lock manifest + replay verification completed." in proc.stdout

        summary = json.loads(out_summary_json.read_text(encoding="utf-8"))
        assert summary["case_count"] == 2
        assert summary["strategy"] == "mixed_family_partitioned_lock"

        rows = {str(x["label"]): x for x in summary["cases"]}
        assert rows["case_a"]["materialization_mode"] == "fit_aware_rebuilt_pack"
        assert rows["case_b"]["materialization_mode"] == "baseline_source_pack"
        assert Path(str(rows["case_a"]["selected_fit_json"])).resolve() == fit_json.resolve()
        assert rows["case_b"]["selected_fit_json"] is None

        manifest_json = Path(summary["case_level_lock_manifest_json"])
        plan_json = Path(summary["measured_replay_plan_json"])
        replay_summary_json = Path(summary["measured_replay_summary_json"])
        assert manifest_json.exists()
        assert plan_json.exists()
        assert replay_summary_json.exists()

        plan_payload = json.loads(plan_json.read_text(encoding="utf-8"))
        assert len(plan_payload["packs"]) == 2
        pack_ids = {str(x["pack_id"]) for x in plan_payload["packs"]}
        assert pack_ids == {"case_a", "case_b"}

    print("validate_run_case_partitioned_lock_manifest_replay: pass")


if __name__ == "__main__":
    run()

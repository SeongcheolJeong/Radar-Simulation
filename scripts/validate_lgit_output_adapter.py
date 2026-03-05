#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np

from avxsim.lgit_output_adapter import (
    build_lgit_customized_payload,
    save_lgit_customized_output_npz,
)


def main() -> None:
    rng = np.random.default_rng(7)
    adc = (
        rng.standard_normal((32, 8, 2, 2))
        + 1j * rng.standard_normal((32, 8, 2, 2))
    ).astype(np.complex128)
    tx_schedule = [0, 1, 0, 1, 0, 1, 0, 1]

    payload = build_lgit_customized_payload(
        adc_sctr=adc,
        tx_schedule=tx_schedule,
        multiplexing_mode="bpm",
        metadata={"scene_id": "unit_case"},
    )
    assert set(payload.keys()) == {
        "adc_virtual_scv",
        "range_doppler_power_drc",
        "tx_pair_doppler_power_pdr",
        "tx_pairs",
        "metadata_json",
    }

    meta = json.loads(str(payload["metadata_json"]))
    assert meta["version"] == "lgit_customized_output_v1"
    assert meta["multiplexing_mode"] == "bpm"
    assert meta["adc_shape_sctr"] == [32, 8, 2, 2]
    assert meta["tx_schedule"] == tx_schedule

    adc_virtual = np.asarray(payload["adc_virtual_scv"])
    rd_power = np.asarray(payload["range_doppler_power_drc"])
    pair_power = np.asarray(payload["tx_pair_doppler_power_pdr"])
    tx_pairs = np.asarray(payload["tx_pairs"])

    assert adc_virtual.shape == (32, 8, 4), adc_virtual.shape
    assert rd_power.shape == (8, 16, 4), rd_power.shape
    assert pair_power.shape == (2, 8, 16), pair_power.shape
    assert tx_pairs.shape == (2, 2), tx_pairs.shape

    with tempfile.TemporaryDirectory(prefix="validate_lgit_output_adapter_") as td:
        out_npz = Path(td) / "lgit_customized_output.npz"
        summary = save_lgit_customized_output_npz(
            output_npz=out_npz,
            adc_sctr=adc,
            tx_schedule=tx_schedule,
            multiplexing_mode="bpm",
            metadata={"scene_id": "unit_case"},
        )
        assert out_npz.exists() and out_npz.is_file()
        assert summary["version"] == "lgit_customized_output_v1"
        assert summary["adc_virtual_shape"] == [32, 8, 4]
        assert summary["range_doppler_power_shape"] == [8, 16, 4]
        assert summary["tx_pair_doppler_power_shape"] == [2, 8, 16]

        with np.load(str(out_npz), allow_pickle=False) as loaded:
            assert loaded["adc_virtual_scv"].shape == (32, 8, 4)
            assert loaded["range_doppler_power_drc"].shape == (8, 16, 4)
            assert loaded["tx_pair_doppler_power_pdr"].shape == (2, 8, 16)
            assert loaded["tx_pairs"].shape == (2, 2)
            loaded_meta = json.loads(str(loaded["metadata_json"]))
            assert loaded_meta["version"] == "lgit_customized_output_v1"

    print("validate_lgit_output_adapter: pass")


if __name__ == "__main__":
    main()


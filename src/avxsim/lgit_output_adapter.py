from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import numpy as np


def build_lgit_customized_payload(
    *,
    adc_sctr: np.ndarray,
    tx_schedule: Sequence[int],
    multiplexing_mode: str = "tdm",
    metadata: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    adc = np.asarray(adc_sctr, dtype=np.complex128)
    if adc.ndim != 4:
        raise ValueError("adc_sctr must be 4D [sample, chirp, tx, rx]")

    n_samp, n_chirp, n_tx, n_rx = [int(x) for x in adc.shape]
    if n_samp <= 0 or n_chirp <= 0 or n_tx <= 0 or n_rx <= 0:
        raise ValueError("invalid adc shape")

    tx_sched = [int(x) for x in tx_schedule]
    if len(tx_sched) != n_chirp:
        raise ValueError("tx_schedule length must equal chirp dimension")

    adc_virtual = adc.reshape(n_samp, n_chirp, n_tx * n_rx)
    rng_fft = np.fft.fft(adc_virtual, axis=0)
    n_range = max(1, int(n_samp // 2))
    rng_half = rng_fft[:n_range, :, :]
    doppler = np.fft.fftshift(np.fft.fft(rng_half, axis=1), axes=1)
    rd_power_drc = np.transpose(np.abs(doppler) ** 2, (1, 0, 2))

    tx_pairs = _build_tx_pairs(n_tx=n_tx)
    pair_count = int(tx_pairs.shape[0])
    pair_doppler_power = np.zeros((pair_count, n_chirp, n_range), dtype=np.float64)
    for pair_idx, (tx_a, tx_b) in enumerate(tx_pairs.tolist()):
        per_tx = np.mean(adc[:, :, [int(tx_a), int(tx_b)], :], axis=3)
        combined = np.sum(per_tx, axis=2)
        pair_rng = np.fft.fft(combined, axis=0)[:n_range, :]
        pair_doppler = np.fft.fftshift(np.fft.fft(pair_rng, axis=1), axes=1)
        pair_doppler_power[pair_idx, :, :] = np.transpose(np.abs(pair_doppler) ** 2, (1, 0))

    payload_meta: Dict[str, Any] = {
        "version": "lgit_customized_output_v1",
        "multiplexing_mode": str(multiplexing_mode),
        "adc_shape_sctr": [n_samp, n_chirp, n_tx, n_rx],
        "tx_schedule": tx_sched,
        "virtual_channel_count": int(n_tx * n_rx),
        "tx_pairs": [[int(a), int(b)] for a, b in tx_pairs.tolist()],
    }
    if isinstance(metadata, Mapping):
        payload_meta["upstream_metadata"] = dict(metadata)

    return {
        "adc_virtual_scv": np.asarray(adc_virtual, dtype=np.complex128),
        "range_doppler_power_drc": np.asarray(rd_power_drc, dtype=np.float64),
        "tx_pair_doppler_power_pdr": np.asarray(pair_doppler_power, dtype=np.float64),
        "tx_pairs": np.asarray(tx_pairs, dtype=np.int64),
        "metadata_json": json.dumps(payload_meta),
    }


def save_lgit_customized_output_npz(
    *,
    output_npz: str | Path,
    adc_sctr: np.ndarray,
    tx_schedule: Sequence[int],
    multiplexing_mode: str = "tdm",
    metadata: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    out_path = Path(output_npz).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = build_lgit_customized_payload(
        adc_sctr=adc_sctr,
        tx_schedule=tx_schedule,
        multiplexing_mode=multiplexing_mode,
        metadata=metadata,
    )
    np.savez_compressed(str(out_path), **payload)

    with np.load(str(out_path), allow_pickle=False) as probe:
        adc_virtual = np.asarray(probe["adc_virtual_scv"])
        rd_power = np.asarray(probe["range_doppler_power_drc"])
        pair_power = np.asarray(probe["tx_pair_doppler_power_pdr"])

    return {
        "output_npz": str(out_path),
        "version": "lgit_customized_output_v1",
        "adc_virtual_shape": [int(x) for x in adc_virtual.shape],
        "range_doppler_power_shape": [int(x) for x in rd_power.shape],
        "tx_pair_doppler_power_shape": [int(x) for x in pair_power.shape],
    }


def _build_tx_pairs(n_tx: int) -> np.ndarray:
    if int(n_tx) <= 1:
        return np.asarray([[0, 0]], dtype=np.int64)
    pairs = []
    for tx_a in range(int(n_tx)):
        tx_b = int(tx_a + 1)
        if tx_b >= int(n_tx):
            tx_b = int(tx_a)
        pairs.append([int(tx_a), int(tx_b)])
    return np.asarray(pairs, dtype=np.int64)

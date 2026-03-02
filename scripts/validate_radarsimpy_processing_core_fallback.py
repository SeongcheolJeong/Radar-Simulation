#!/usr/bin/env python3
from __future__ import annotations

import numpy as np

import avxsim.radarsimpy_api as api


def run() -> None:
    old_resolve = api._resolve_submodule_attr

    def _resolve_with_fft_missing(submodule_name: str, attr_name: str):
        if submodule_name == "processing" and attr_name in {
            "range_fft",
            "doppler_fft",
            "range_doppler_fft",
        }:
            raise RuntimeError(f"forced missing processing attr: {attr_name}")
        return old_resolve(submodule_name, attr_name)

    try:
        api._resolve_submodule_attr = _resolve_with_fft_missing

        x = np.arange(2 * 3 * 4, dtype=np.float64).reshape(2, 3, 4)
        rw = np.hanning(4)
        dw = np.hanning(3)

        got_range = api.range_fft(x, axis=-1, n=4, window=rw)
        exp_range = np.fft.fft(x * rw.reshape(1, 1, 4), n=4, axis=-1)
        assert np.allclose(got_range, exp_range), "range_fft fallback mismatch"

        got_dop = api.doppler_fft(x, axis=-2, n=3, window=dw)
        exp_dop = np.fft.fft(x * dw.reshape(1, 3, 1), n=3, axis=-2)
        assert np.allclose(got_dop, exp_dop), "doppler_fft fallback mismatch"

        got_rd = api.range_doppler_fft(
            x,
            range_axis=-1,
            doppler_axis=-2,
            range_n=4,
            doppler_n=3,
            range_window=rw,
            doppler_window=dw,
        )
        exp_rd = np.fft.fft(
            np.fft.fft(x * rw.reshape(1, 1, 4), n=4, axis=-1) * dw.reshape(1, 3, 1),
            n=3,
            axis=-2,
        )
        assert np.allclose(got_rd, exp_rd), "range_doppler_fft fallback mismatch"
    finally:
        api._resolve_submodule_attr = old_resolve

    print("validate_radarsimpy_processing_core_fallback: pass")


if __name__ == "__main__":
    run()

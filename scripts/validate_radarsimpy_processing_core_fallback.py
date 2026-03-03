#!/usr/bin/env python3
from __future__ import annotations

import numpy as np

import avxsim.radarsimpy_api as api
from avxsim.radarsimpy_core_processing import (
    core_cfar_ca_1d,
    core_cfar_ca_2d,
    core_cfar_os_1d,
    core_cfar_os_2d,
    core_doa_bartlett,
    core_doa_capon,
    core_doa_esprit,
    core_doa_iaa,
    core_doa_music,
    core_doa_root_music,
)
from avxsim.radarsimpy_core_tools import core_roc_pd, core_roc_snr


def run() -> None:
    old_resolve = api._resolve_submodule_attr
    forced_processing = set(api.RADARSIMPY_PROCESSING_API)
    forced_tools = set(api.RADARSIMPY_TOOLS_API)

    def _resolve_with_fallback_forced(submodule_name: str, attr_name: str):
        if submodule_name == "processing" and attr_name in forced_processing:
            raise RuntimeError(f"forced missing processing attr: {attr_name}")
        if submodule_name == "tools" and attr_name in forced_tools:
            raise RuntimeError(f"forced missing tools attr: {attr_name}")
        return old_resolve(submodule_name, attr_name)

    try:
        api._resolve_submodule_attr = _resolve_with_fallback_forced

        x = np.arange(2 * 3 * 4, dtype=np.float64).reshape(2, 3, 4)
        rw = np.hanning(4)
        dw = np.hanning(3)

        got_range = api.range_fft(x, axis=-1, n=4, window=rw)
        exp_range = np.fft.fft(x * rw.reshape(1, 1, 4), n=4, axis=-1)
        assert np.allclose(got_range, exp_range), "range_fft fallback mismatch"
        got_range_canon = api.range_fft(x, rw, 4)
        assert np.allclose(got_range_canon, exp_range), "range_fft canonical fallback mismatch"

        got_dop = api.doppler_fft(x, axis=-2, n=3, window=dw)
        exp_dop = np.fft.fft(x * dw.reshape(1, 3, 1), n=3, axis=-2)
        assert np.allclose(got_dop, exp_dop), "doppler_fft fallback mismatch"
        got_dop_canon = api.doppler_fft(x, dw, 3)
        assert np.allclose(got_dop_canon, exp_dop), "doppler_fft canonical fallback mismatch"

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
        got_rd_canon = api.range_doppler_fft(x, rw, dw, 4, 3)
        assert np.allclose(got_rd_canon, exp_rd), "range_doppler_fft canonical fallback mismatch"

        # CFAR fallback
        p1 = np.arange(1, 65, dtype=np.float64)
        got_ca1 = api.cfar_ca_1d(p1, guard=1, trailing=4, pfa=1e-3, axis=0, detector="squarelaw")
        exp_ca1 = core_cfar_ca_1d(p1, guard=1, trailing=4, pfa=1e-3, axis=0, detector="squarelaw")
        assert np.allclose(got_ca1, exp_ca1), "cfar_ca_1d fallback mismatch"

        p2 = np.arange(1, 11 * 12 + 1, dtype=np.float64).reshape(11, 12)
        got_ca2 = api.cfar_ca_2d(p2, guard=[1, 1], trailing=[2, 3], pfa=1e-4)
        exp_ca2 = core_cfar_ca_2d(p2, guard=[1, 1], trailing=[2, 3], pfa=1e-4)
        assert np.allclose(got_ca2, exp_ca2), "cfar_ca_2d fallback mismatch"

        got_os1 = api.cfar_os_1d(p1, guard=1, trailing=4, k=5, pfa=1e-3, axis=0, detector="squarelaw")
        exp_os1 = core_cfar_os_1d(p1, guard=1, trailing=4, k=5, pfa=1e-3, axis=0, detector="squarelaw")
        assert np.allclose(got_os1, exp_os1), "cfar_os_1d fallback mismatch"

        got_os2 = api.cfar_os_2d(p2, guard=[1, 1], trailing=[2, 2], k=30, pfa=1e-3)
        exp_os2 = core_cfar_os_2d(p2, guard=[1, 1], trailing=[2, 2], k=30, pfa=1e-3)
        assert np.allclose(got_os2, exp_os2), "cfar_os_2d fallback mismatch"

        # DOA fallback
        n_array = 8
        spacing = 0.5
        true_deg = 20.0
        scan = np.arange(-60, 61)
        arr = np.linspace(0, (n_array - 1) * spacing, n_array)
        sv = np.exp(1j * 2 * np.pi * arr * np.sin(np.radians(true_deg))) / np.sqrt(n_array)
        cov = np.outer(sv, sv.conj()) + 1e-2 * np.eye(n_array, dtype=np.complex128)

        got_b = api.doa_bartlett(cov, spacing=spacing, scanangles=scan)
        exp_b = core_doa_bartlett(cov, spacing=spacing, scanangles=scan)
        assert np.allclose(got_b, exp_b), "doa_bartlett fallback mismatch"

        got_c = api.doa_capon(cov, spacing=spacing, scanangles=scan)
        exp_c = core_doa_capon(cov, spacing=spacing, scanangles=scan)
        assert np.allclose(got_c, exp_c), "doa_capon fallback mismatch"

        got_m = api.doa_music(cov, nsig=1, spacing=spacing, scanangles=scan)
        exp_m = core_doa_music(cov, nsig=1, spacing=spacing, scanangles=scan)
        assert np.allclose(got_m[0], exp_m[0]), "doa_music angles fallback mismatch"
        assert np.array_equal(got_m[1], exp_m[1]), "doa_music index fallback mismatch"
        assert np.allclose(got_m[2], exp_m[2]), "doa_music spectrum fallback mismatch"

        got_rm = np.sort(np.asarray(api.doa_root_music(cov, nsig=1, spacing=spacing), dtype=np.float64))
        exp_rm = np.sort(np.asarray(core_doa_root_music(cov, nsig=1, spacing=spacing), dtype=np.float64))
        assert np.allclose(got_rm, exp_rm), "doa_root_music fallback mismatch"

        got_es = np.sort(np.asarray(api.doa_esprit(cov, nsig=1, spacing=spacing), dtype=np.float64))
        exp_es = np.sort(np.asarray(core_doa_esprit(cov, nsig=1, spacing=spacing), dtype=np.float64))
        assert np.allclose(got_es, exp_es), "doa_esprit fallback mismatch"

        snaps = np.arange(16, dtype=np.float64)
        beam = sv[:, np.newaxis] * np.exp(1j * 2 * np.pi * 0.07 * snaps[np.newaxis, :])
        angle_grid = np.arange(-60, 61)
        arr_grid, ang_grid = np.meshgrid(arr, np.radians(angle_grid), indexing="ij")
        steering = np.exp(1j * 2 * np.pi * arr_grid * np.sin(ang_grid)) / np.sqrt(n_array)
        got_iaa = api.doa_iaa(beam, steering, num_it=3)
        exp_iaa = core_doa_iaa(beam, steering, num_it=3)
        assert np.allclose(got_iaa, exp_iaa), "doa_iaa fallback mismatch"

        # ROC fallback
        pfa = np.array([1e-3, 1e-5], dtype=np.float64)
        snr_db = np.array([-5.0, 0.0, 10.0], dtype=np.float64)

        got_pd = api.roc_pd(pfa, snr_db, npulses=8, stype="Coherent")
        exp_pd = core_roc_pd(pfa, snr_db, npulses=8, stype="Coherent")
        assert np.allclose(got_pd, exp_pd), "roc_pd coherent fallback mismatch"

        got_pd_sw = api.roc_pd(pfa, snr_db, npulses=8, stype="Swerling 1")
        exp_pd_sw = core_roc_pd(pfa, snr_db, npulses=8, stype="Swerling 1")
        assert np.allclose(got_pd_sw, exp_pd_sw), "roc_pd swerling1 fallback mismatch"

        pd_goal = np.array([0.6, 0.9], dtype=np.float64)
        got_snr = api.roc_snr(1e-6, pd_goal, npulses=8, stype="Coherent")
        exp_snr = core_roc_snr(1e-6, pd_goal, npulses=8, stype="Coherent")
        assert np.allclose(got_snr, exp_snr), "roc_snr fallback mismatch"
    finally:
        api._resolve_submodule_attr = old_resolve

    print("validate_radarsimpy_processing_core_fallback: pass")


if __name__ == "__main__":
    run()

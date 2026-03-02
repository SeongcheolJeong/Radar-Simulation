#!/usr/bin/env python3
from __future__ import annotations

import types
from typing import Any, Callable, List, Tuple

import avxsim.radarsimpy_api as api
from avxsim import (
    API_INDEX_URL,
    API_INDEX_VERSION,
    RADARSIMPY_EXCLUDED_API,
    RADARSIMPY_SUPPORTED_API,
    Radar,
    Receiver,
    Transmitter,
    cfar_ca_1d,
    cfar_ca_2d,
    cfar_os_1d,
    cfar_os_2d,
    doa_bartlett,
    doa_capon,
    doa_esprit,
    doa_iaa,
    doa_music,
    doa_root_music,
    doppler_fft,
    inspect_radarsimpy_api_coverage,
    range_doppler_fft,
    range_fft,
    roc_pd,
    roc_snr,
    sim_radar,
    sim_rcs,
)


def _make_stub(tag: str, calls: List[Tuple[str, tuple, dict]]) -> Callable[..., Any]:
    def _call(*args: Any, **kwargs: Any) -> Any:
        calls.append((tag, args, kwargs))
        return {"tag": tag, "args": args, "kwargs": kwargs}

    return _call


def run() -> None:
    calls: List[Tuple[str, tuple, dict]] = []

    fake = types.SimpleNamespace()
    fake.__name__ = "radarsimpy"
    fake.__version__ = "stubbed_api_surface"
    fake.Transmitter = _make_stub("Transmitter", calls)
    fake.Receiver = _make_stub("Receiver", calls)
    fake.Radar = _make_stub("Radar", calls)
    fake.sim_radar = _make_stub("sim_radar", calls)
    fake.sim_rcs = _make_stub("sim_rcs", calls)
    fake.processing = types.SimpleNamespace(
        cfar_ca_1d=_make_stub("processing.cfar_ca_1d", calls),
        cfar_ca_2d=_make_stub("processing.cfar_ca_2d", calls),
        cfar_os_1d=_make_stub("processing.cfar_os_1d", calls),
        cfar_os_2d=_make_stub("processing.cfar_os_2d", calls),
        doa_bartlett=_make_stub("processing.doa_bartlett", calls),
        doa_capon=_make_stub("processing.doa_capon", calls),
        doa_esprit=_make_stub("processing.doa_esprit", calls),
        doa_iaa=_make_stub("processing.doa_iaa", calls),
        doa_music=_make_stub("processing.doa_music", calls),
        doa_root_music=_make_stub("processing.doa_root_music", calls),
        doppler_fft=_make_stub("processing.doppler_fft", calls),
        range_doppler_fft=_make_stub("processing.range_doppler_fft", calls),
        range_fft=_make_stub("processing.range_fft", calls),
    )
    fake.tools = types.SimpleNamespace(
        roc_pd=_make_stub("tools.roc_pd", calls),
        roc_snr=_make_stub("tools.roc_snr", calls),
    )

    old_import = api._import_radarsimpy_module
    try:
        api._import_radarsimpy_module = lambda: fake

        coverage = inspect_radarsimpy_api_coverage()
        assert coverage["api_index_url"] == API_INDEX_URL
        assert coverage["api_index_version"] == API_INDEX_VERSION
        assert coverage["all_supported_available"] is True
        assert coverage["missing"] == []
        assert tuple(coverage["supported_api"]) == tuple(RADARSIMPY_SUPPORTED_API)
        assert tuple(coverage["excluded_api"]) == tuple(RADARSIMPY_EXCLUDED_API)
        assert "sim_lidar" not in coverage["supported_api"]
        assert "sim_lidar" in coverage["excluded_api"]

        dispatch_cases = [
            ("Transmitter", Transmitter, "Transmitter"),
            ("Receiver", Receiver, "Receiver"),
            ("Radar", Radar, "Radar"),
            ("sim_radar", sim_radar, "sim_radar"),
            ("sim_rcs", sim_rcs, "sim_rcs"),
            ("cfar_ca_1d", cfar_ca_1d, "processing.cfar_ca_1d"),
            ("cfar_ca_2d", cfar_ca_2d, "processing.cfar_ca_2d"),
            ("cfar_os_1d", cfar_os_1d, "processing.cfar_os_1d"),
            ("cfar_os_2d", cfar_os_2d, "processing.cfar_os_2d"),
            ("doa_bartlett", doa_bartlett, "processing.doa_bartlett"),
            ("doa_capon", doa_capon, "processing.doa_capon"),
            ("doa_esprit", doa_esprit, "processing.doa_esprit"),
            ("doa_iaa", doa_iaa, "processing.doa_iaa"),
            ("doa_music", doa_music, "processing.doa_music"),
            ("doa_root_music", doa_root_music, "processing.doa_root_music"),
            ("doppler_fft", doppler_fft, "processing.doppler_fft"),
            ("range_doppler_fft", range_doppler_fft, "processing.range_doppler_fft"),
            ("range_fft", range_fft, "processing.range_fft"),
            ("roc_pd", roc_pd, "tools.roc_pd"),
            ("roc_snr", roc_snr, "tools.roc_snr"),
        ]

        for idx, (name, fn, expected_tag) in enumerate(dispatch_cases):
            result = fn(idx, label=name)
            assert isinstance(result, dict)
            assert result.get("tag") == expected_tag
            assert result.get("kwargs", {}).get("label") == name

        assert not hasattr(api, "sim_lidar")
    finally:
        api._import_radarsimpy_module = old_import

    print("validate_radarsimpy_api_coverage_excluding_sim_lidar: pass")


if __name__ == "__main__":
    run()

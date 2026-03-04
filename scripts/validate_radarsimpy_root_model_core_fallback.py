#!/usr/bin/env python3
from __future__ import annotations

import numpy as np

import avxsim.radarsimpy_api as api
from avxsim.radarsimpy_core_model import CoreRadar, CoreReceiver, CoreTransmitter


def run() -> None:
    old_resolve = api._resolve_root_attr
    forced_missing = {"Transmitter", "Receiver", "Radar"}

    def _resolve_forced(name: str):
        if name in forced_missing:
            raise RuntimeError(f"forced missing root attr: {name}")
        return old_resolve(name)

    try:
        api._resolve_root_attr = _resolve_forced

        tx = api.Transmitter(
            f=[76.5e9, 77.0e9],
            t=[0.0, 1.0e-6],
            tx_power=11.0,
            pulses=4,
            prp=2.0e-6,
            channels=[
                {
                    "location": [0.0, 0.0, 0.0],
                    "pulse_amp": [1.0, 1.0, 1.0, 1.0],
                    "mod_t": [0.0, 1.0e-6],
                    "amp": [1.0, 0.8],
                    "phs": [0.0, 90.0],
                },
                {
                    "location": [0.03, 0.0, 0.0],
                    "pulse_amp": [1.0, 0.0, 1.0, 0.0],
                },
            ],
        )
        assert isinstance(tx, CoreTransmitter)
        assert int(tx.waveform_prop["pulses"]) == 4
        assert int(tx.txchannel_prop["size"]) == 2
        assert np.shape(tx.txchannel_prop["locations"]) == (2, 3)
        assert np.shape(tx.txchannel_prop["pulse_mod"]) == (2, 4)
        assert np.allclose(np.abs(tx.txchannel_prop["pulse_mod"][1]), [1.0, 0.0, 1.0, 0.0])
        assert bool(tx.txchannel_prop["waveform_mod"][0]["enabled"]) is True
        assert bool(tx.txchannel_prop["waveform_mod"][1]["enabled"]) is False

        rx = api.Receiver(
            fs=20.0e6,
            noise_figure=12.0,
            rf_gain=18.0,
            load_resistor=500.0,
            baseband_gain=28.0,
            bb_type="complex",
            channels=[
                {"location": [0.0, 0.0, 0.0]},
                {"location": [0.0, 0.03, 0.0]},
                {"location": [0.0, 0.06, 0.0]},
            ],
        )
        assert isinstance(rx, CoreReceiver)
        assert int(rx.rxchannel_prop["size"]) == 3
        assert np.shape(rx.rxchannel_prop["locations"]) == (3, 3)
        assert float(rx.bb_prop["noise_bandwidth"]) == float(rx.bb_prop["fs"])

        radar = api.Radar(
            transmitter=tx,
            receiver=rx,
            frame_time=[0.0, 1.0e-3],
            location=(1.0, 2.0, 3.0),
            speed=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 5.0),
            rotation_rate=(0.0, 0.0, 0.5),
            seed=7,
        )
        assert isinstance(radar, CoreRadar)
        assert int(radar.array_prop["size"]) == 6
        assert np.shape(radar.array_prop["virtual_array"]) == (6, 3)
        assert int(radar.sample_prop["samples_per_pulse"]) == 20
        assert np.shape(radar.time_prop["origin_timestamp"]) == (6, 4, 20)
        assert np.shape(radar.time_prop["timestamp"]) == (12, 4, 20)
        assert float(radar.sample_prop["noise"]) > 0.0
        assert radar.sample_prop["phase_noise"] is None
        assert np.shape(radar.timestamp) == (12, 4, 20)
    finally:
        api._resolve_root_attr = old_resolve

    print("validate_radarsimpy_root_model_core_fallback: pass")


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
from __future__ import annotations

import numpy as np

import avxsim.radarsimpy_api as api
from avxsim.radarsimpy_core_model import CoreRadar, CoreReceiver, CoreTransmitter


def run() -> None:
    old_resolve = api._resolve_root_attr
    forced_missing = {"sim_radar", "sim_rcs"}

    def _resolve_forced(name: str):
        if name in forced_missing:
            raise RuntimeError(f"forced missing root attr: {name}")
        return old_resolve(name)

    tx = CoreTransmitter(
        f=[76.5e9, 77.0e9],
        t=[0.0, 1.0e-6],
        tx_power=0.0,
        pulses=4,
        prp=2.0e-6,
        channels=[
            {"location": [0.0, 0.0, 0.0], "pulse_amp": [1.0, 1.0, 1.0, 1.0]},
            {"location": [0.03, 0.0, 0.0], "pulse_amp": [1.0, 0.0, 1.0, 0.0]},
        ],
    )
    rx = CoreReceiver(
        fs=20.0e6,
        noise_figure=12.0,
        rf_gain=18.0,
        load_resistor=500.0,
        baseband_gain=28.0,
        bb_type="complex",
        channels=[
            {"location": [0.0, 0.0, 0.0]},
            {"location": [0.0, 0.03, 0.0]},
        ],
    )
    radar = CoreRadar(transmitter=tx, receiver=rx, frame_time=0.0)

    point_targets = [
        {
            "location": [22.0, 0.0, 0.0],
            "speed": [-2.0, 0.0, 0.0],
            "rcs": 10.0,
            "phase": 0.0,
        },
        {
            "location": [30.0, 2.0, 0.0],
            "speed": [-1.0, 0.0, 0.0],
            "rcs": 6.0,
            "phase": 45.0,
        },
    ]

    try:
        api._resolve_root_attr = _resolve_forced

        out = api.sim_radar(
            radar,
            point_targets,
            density=1.25,
            level="pulse",
            frame_time=None,  # exercise extra kwarg passthrough support in fallback
            debug=False,  # exercise extra kwarg passthrough support in fallback
            device="cpu",
        )
        assert isinstance(out, dict)
        assert set(out.keys()) >= {"baseband", "noise", "timestamp", "interference"}
        bb = np.asarray(out["baseband"])
        noise = np.asarray(out["noise"])
        ts = np.asarray(out["timestamp"])
        assert bb.shape == (4, 4, 20), bb.shape  # n_tx*n_rx, pulses, samples
        assert noise.shape == bb.shape
        assert ts.shape == bb.shape
        assert np.all(np.isfinite(np.real(bb))) and np.all(np.isfinite(np.imag(bb)))
        assert np.max(np.abs(bb)) > 0.0

        dry = api.sim_radar(radar, point_targets, dry_run=True)
        dry_bb = np.asarray(dry["baseband"])
        assert dry_bb.shape == bb.shape
        assert np.allclose(dry_bb, 0.0)

        rcs_scalar = api.sim_rcs(
            point_targets,
            f=77e9,
            inc_phi=0.0,
            inc_theta=90.0,
            obs_phi=0.0,
            obs_theta=90.0,
        )
        assert isinstance(rcs_scalar, float)
        assert np.isfinite(rcs_scalar) and rcs_scalar > 0.0

        rcs_vec = api.sim_rcs(
            point_targets,
            f=77e9,
            inc_phi=[0.0, 20.0, -15.0],
            inc_theta=[90.0, 90.0, 90.0],
            obs_phi=[0.0, 20.0, -15.0],
            obs_theta=[90.0, 85.0, 95.0],
            density=1.1,
        )
        assert isinstance(rcs_vec, np.ndarray)
        assert rcs_vec.shape == (3,)
        assert np.all(np.isfinite(rcs_vec))
        assert np.all(rcs_vec >= 0.0)

        got_error = False
        try:
            api.sim_rcs(
                point_targets,
                f=77e9,
                inc_phi=[0.0, 10.0],
                inc_theta=[90.0],
            )
        except ValueError:
            got_error = True
        assert got_error is True
    finally:
        api._resolve_root_attr = old_resolve

    print("validate_radarsimpy_simulator_core_fallback: pass")


if __name__ == "__main__":
    run()

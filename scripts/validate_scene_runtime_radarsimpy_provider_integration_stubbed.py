#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

import numpy as np

import avxsim.radarsimpy_api as rs_api
from avxsim.scene_pipeline import run_object_scene_to_radar_map_json
from avxsim.runtime_providers import radarsimpy_rt_provider as provider


class _FakeRadarSimPy:
    __name__ = "radarsimpy"
    __version__ = "stubbed"


class _FakeTransmitter:
    def __init__(self, f, t, tx_power=0.0, pulses=1, prp=None, channels=None, **kwargs):
        del f, tx_power, prp, kwargs
        self.t = t
        self.pulses = int(pulses)
        self.channels = list(channels or [{"location": [0.0, 0.0, 0.0]}])


class _FakeReceiver:
    def __init__(
        self,
        fs,
        noise_figure=0.0,
        rf_gain=0.0,
        load_resistor=500.0,
        baseband_gain=0.0,
        bb_type="complex",
        channels=None,
        **kwargs,
    ):
        del noise_figure, rf_gain, load_resistor, baseband_gain, bb_type, kwargs
        self.fs = float(fs)
        self.channels = list(channels or [{"location": [0.0, 0.0, 0.0]}])


class _FakeRadar:
    def __init__(self, transmitter, receiver, seed=None, **kwargs):
        del seed, kwargs
        self.transmitter = transmitter
        self.receiver = receiver


class _FakeRadarSimPyWithSim:
    __name__ = "radarsimpy"
    __version__ = "stubbed_sim"
    Radar = _FakeRadar
    Transmitter = _FakeTransmitter
    Receiver = _FakeReceiver

    @staticmethod
    def sim_radar(radar, targets, **kwargs):
        del targets, kwargs
        pulses = int(radar.transmitter.pulses)
        chirp_duration = float(radar.transmitter.t[-1]) - float(radar.transmitter.t[0])
        n_samples = int(round(chirp_duration * float(radar.receiver.fs)))
        n_chan = int(len(radar.receiver.channels))
        baseband = np.zeros((n_chan, pulses, n_samples), dtype=np.complex128)
        for ch in range(n_chan):
            for pulse in range(pulses):
                for sample in range(n_samples):
                    baseband[ch, pulse, sample] = complex((100 * (ch + 1)) + pulse, -sample)
        return {
            "baseband": baseband,
            "noise": np.zeros_like(baseband),
            "timestamp": np.zeros_like(baseband, dtype=np.float64),
            "interference": None,
        }


def _load_runtime_resolution(radar_map_npz: Path) -> dict:
    payload = np.load(str(radar_map_npz), allow_pickle=False)
    metadata = json.loads(str(payload["metadata_json"]))
    info = metadata.get("runtime_resolution")
    if not isinstance(info, dict):
        raise AssertionError("runtime_resolution metadata missing")
    return info


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_radarsimpy_runtime_provider_integration_") as td:
        root = Path(td)
        scene_json = root / "scene_radarsimpy_runtime_provider.json"
        scene_json.write_text(
            json.dumps(
                {
                    "scene_id": "radarsimpy_runtime_provider_integration_case",
                    "backend": {
                        "type": "radarsimpy_rt",
                        "n_chirps": 4,
                        "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                        "rx_pos_m": [
                            [0.0, 0.00185, 0.0],
                            [0.0, 0.0037, 0.0],
                            [0.0, 0.00555, 0.0],
                            [0.0, 0.0074, 0.0],
                        ],
                        "runtime_provider": (
                            "avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths"
                        ),
                        "runtime_required_modules": [],
                        "runtime_failure_policy": "error",
                        "runtime_input": {
                            "target_range_m": 25.0,
                            "target_az_deg": 0.0,
                            "target_el_deg": 0.0,
                            "target_radial_velocity_mps": 0.0,
                            "material_tag": "stubbed_radarsimpy",
                            "path_id_prefix": "stubbed_radarsimpy",
                        },
                        "noise_sigma": 0.0,
                    },
                    "radar": {
                        "fc_hz": 77e9,
                        "slope_hz_per_s": 20e12,
                        "fs_hz": 20e6,
                        "samples_per_chirp": 512,
                    },
                    "map_config": {"nfft_range": 512, "range_bin_limit": 64},
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        old_import_provider = provider._import_radarsimpy_module
        old_import_api = rs_api._import_radarsimpy_module
        try:
            provider._import_radarsimpy_module = lambda: _FakeRadarSimPy
            rs_api._import_radarsimpy_module = lambda: _FakeRadarSimPy
            out_dir = root / "outputs"
            result = run_object_scene_to_radar_map_json(
                scene_json_path=str(scene_json),
                output_dir=str(out_dir),
                run_hybrid_estimation=False,
            )
        finally:
            provider._import_radarsimpy_module = old_import_provider
            rs_api._import_radarsimpy_module = old_import_api

        path_payload = json.loads(Path(result["path_list_json"]).read_text(encoding="utf-8"))
        assert isinstance(path_payload, list) and len(path_payload) == 4
        for chirp_idx, chirp_paths in enumerate(path_payload):
            assert isinstance(chirp_paths, list) and len(chirp_paths) == 1
            path = chirp_paths[0]
            assert path["path_id"] == f"stubbed_radarsimpy_c{chirp_idx:04d}"
            assert path["material_tag"] == "stubbed_radarsimpy"

        runtime_resolution = _load_runtime_resolution(Path(result["radar_map_npz"]))
        assert runtime_resolution["mode"] == "runtime_provider"
        assert str(runtime_resolution.get("runtime_provider", "")).endswith(
            "generate_radarsimpy_like_paths"
        )
        runtime_info = runtime_resolution.get("runtime_info")
        assert isinstance(runtime_info, dict)
        assert runtime_info.get("provider_spec") == (
            "avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths"
        )

        sim_scene_json = root / "scene_radarsimpy_runtime_provider_simulated.json"
        sim_scene_json.write_text(
            json.dumps(
                {
                    "scene_id": "radarsimpy_runtime_provider_simulated_case",
                    "backend": {
                        "type": "radarsimpy_rt",
                        "n_chirps": 3,
                        "tx_pos_m": [[0.0, 0.0, 0.0]],
                        "rx_pos_m": [[0.0, 0.00185, 0.0]],
                        "runtime_provider": (
                            "avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths"
                        ),
                        "runtime_required_modules": [],
                        "runtime_failure_policy": "error",
                        "runtime_input": {
                            "simulation_mode": "radarsimpy_adc",
                            "fallback_to_analytic_on_error": False,
                            "target_range_m": 25.0,
                            "target_az_deg": 0.0,
                            "target_el_deg": 0.0,
                            "target_radial_velocity_mps": 0.0,
                            "material_tag": "stubbed_radarsimpy_sim",
                            "path_id_prefix": "stubbed_radarsimpy_sim",
                        },
                        "noise_sigma": 0.0,
                    },
                    "radar": {
                        "fc_hz": 77e9,
                        "slope_hz_per_s": 20e12,
                        "fs_hz": 20e6,
                        "samples_per_chirp": 16,
                    },
                    "map_config": {"nfft_range": 16, "range_bin_limit": 8},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        old_import_provider = provider._import_radarsimpy_module
        old_import_api = rs_api._import_radarsimpy_module
        try:
            provider._import_radarsimpy_module = lambda: _FakeRadarSimPyWithSim
            rs_api._import_radarsimpy_module = lambda: _FakeRadarSimPyWithSim
            out_dir = root / "outputs_simulated"
            sim_result = run_object_scene_to_radar_map_json(
                scene_json_path=str(sim_scene_json),
                output_dir=str(out_dir),
                run_hybrid_estimation=False,
            )
        finally:
            provider._import_radarsimpy_module = old_import_provider
            rs_api._import_radarsimpy_module = old_import_api

        adc_payload = np.load(str(sim_result["adc_cube_npz"]), allow_pickle=False)
        adc = np.asarray(adc_payload["adc"])
        assert adc.shape == (16, 3, 1, 1), adc.shape
        # baseband(ch=0, pulse=p, sample=s) = (100+p) + j*(-s)
        assert np.isclose(adc[0, 0, 0, 0], complex(100, 0))
        assert np.isclose(adc[5, 2, 0, 0], complex(102, -5))

        sim_runtime_resolution = _load_runtime_resolution(Path(sim_result["radar_map_npz"]))
        assert sim_runtime_resolution["mode"] == "runtime_provider"
        assert sim_runtime_resolution["adc_source"] == "runtime_payload_adc_sctr"
        assert sim_runtime_resolution["adc_payload_present"] is True

    print("validate_scene_runtime_radarsimpy_provider_integration_stubbed: pass")


if __name__ == "__main__":
    run()

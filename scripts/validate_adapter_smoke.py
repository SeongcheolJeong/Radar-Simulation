#!/Library/Developer/CommandLineTools/usr/bin/python3
import numpy as np

from avxsim.adapters.hybriddynamicrt_adapter import adapt_records_by_chirp
from avxsim.adapters.radarsimpy_checker import to_radarsimpy_view, validate_radarsimpy_view_shape
from avxsim.synth import synth_fmcw_tdm
from avxsim.types import RadarConfig


def run():
    # fake RT records for 2 chirps
    records = [
        [
            {
                "range_m": 42.0,
                "doppler_hz": 1000.0,
                "az_deg": 15.0,
                "el_deg": 0.0,
                "amp_complex": {"re": 1.0, "im": 0.2},
                "pol_matrix": [
                    {"re": 1.0, "im": 0.0},
                    {"re": 0.1, "im": 0.2},
                    {"re": -0.1, "im": 0.05},
                    {"re": 0.9, "im": 0.0},
                ],
            }
        ],
        [
            {
                "delay_s": 2.0 * 42.0 / 299_792_458.0,
                "doppler_hz": 1000.0,
                "unit_direction": [0.0, 1.0, 0.0],
                "amp_complex": [0.8, -0.1],
            }
        ],
    ]

    paths = adapt_records_by_chirp(records)
    assert paths[0][0].pol_matrix is not None
    assert len(paths[0][0].pol_matrix) == 4

    radar = RadarConfig(
        fc_hz=77e9,
        slope_hz_per_s=20e12,
        fs_hz=20e6,
        samples_per_chirp=4096,
        tx_schedule=[0, 1],
    )
    tx_pos = np.array([[0.0, 0.0, 0.0], [0.002, 0.0, 0.0]], dtype=np.float64)
    rx_pos = np.array(
        [[0.0, 0.0, 0.0], [0.002, 0.0, 0.0], [0.004, 0.0, 0.0], [0.006, 0.0, 0.0]],
        dtype=np.float64,
    )

    adc = synth_fmcw_tdm(paths, tx_pos, rx_pos, radar)
    assert adc.shape == (4096, 2, 2, 4), adc.shape

    rs_view = to_radarsimpy_view(adc)
    validate_radarsimpy_view_shape(rs_view, n_channels=8, n_pulses=2, n_samples=4096)

    print("Adapter smoke test passed.")


if __name__ == "__main__":
    run()

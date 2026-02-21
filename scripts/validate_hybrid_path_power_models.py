#!/usr/bin/env python3
import numpy as np

from avxsim.hybrid_pcode import calculate_reflecting_path_power, calculate_scattering_path_power


def run() -> None:
    p_t_dbm = 60.0
    pw = 500
    ph = 500
    lam = 0.0039

    ranges = np.array([5.0, 6.0, 8.0, 12.0], dtype=np.float64)
    refl = calculate_reflecting_path_power(
        p_t_dbm=p_t_dbm,
        pixel_width=pw,
        pixel_height=ph,
        reflecting_coefficient=0.6,
        lambda_m=lam,
        temp_range_m=ranges,
    )
    assert refl.shape == ranges.shape
    assert np.all(np.isfinite(refl))
    assert np.all(refl > 0.0)
    assert np.all(np.diff(refl) < 0.0)  # decays with range

    # Same range, varying angle: scattering should attenuate at large elevation
    ranges2 = np.array([8.0, 8.0, 8.0], dtype=np.float64)
    angles = np.array(
        [
            [0.0, 0.0],      # broadside
            [0.0, np.pi / 4],  # moderate elevation
            [0.0, np.pi / 2],  # near grazing in this model -> strong attenuation
        ],
        dtype=np.float64,
    )
    scat = calculate_scattering_path_power(
        p_t_dbm=p_t_dbm,
        pixel_width=pw,
        pixel_height=ph,
        scattering_coefficient=0.2,
        lambda_m=lam,
        temp_range_m=ranges2,
        temp_angles_rad=angles,
    )
    assert scat.shape == ranges2.shape
    assert np.all(np.isfinite(scat))
    assert np.all(scat >= 0.0)
    assert scat[0] > scat[1] > scat[2]

    print("Hybrid path-power replacement validation passed.")


if __name__ == "__main__":
    run()


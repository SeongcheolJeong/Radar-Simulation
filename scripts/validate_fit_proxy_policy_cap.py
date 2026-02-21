#!/usr/bin/env python3
import numpy as np

from avxsim.adc_pack_builder import apply_path_power_fit_proxy_to_estimation


def main() -> None:
    rd = np.ones((64, 128), dtype=np.float64)
    ra = np.ones((64, 128), dtype=np.float64)
    fit_payload = {
        "fit": {
            "model": "scattering",
            "best_params": {
                "range_power_exponent": 5.0,
                "azimuth_mix": 0.2,
                "azimuth_power": 4.0,
            },
        }
    }

    base = apply_path_power_fit_proxy_to_estimation(rd, ra, fit_payload)
    capped = apply_path_power_fit_proxy_to_estimation(
        rd,
        ra,
        fit_payload,
        fit_proxy_policy={
            "max_range_power_exponent": 1.0,
            "max_azimuth_power": 2.0,
            "min_weight": 0.8,
            "max_weight": 1.2,
        },
    )

    mb = base["metadata"]
    mc = capped["metadata"]

    if abs(float(mc["effective_range_power_exponent"]) - 1.0) > 1e-9:
        raise AssertionError("range exponent cap not applied")
    if abs(float(mc["effective_azimuth_power"]) - 2.0) > 1e-9:
        raise AssertionError("azimuth exponent cap not applied")
    if float(mc["range_weight_min"]) < 0.8 - 1e-6:
        raise AssertionError("min_weight cap not applied")
    if float(mc["range_weight_max"]) > 1.2 + 1e-6:
        raise AssertionError("max_weight cap not applied")

    base_span = float(mb["range_weight_max"]) - float(mb["range_weight_min"])
    cap_span = float(mc["range_weight_max"]) - float(mc["range_weight_min"])
    if cap_span >= base_span:
        raise AssertionError("weight span was not reduced by proxy policy")

    print("validate_fit_proxy_policy_cap: pass")


if __name__ == "__main__":
    main()

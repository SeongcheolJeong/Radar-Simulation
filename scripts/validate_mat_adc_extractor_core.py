#!/usr/bin/env python3
import numpy as np

from avxsim.mat_adc_extract import select_4d_numeric_array


def run() -> None:
    payload = {
        "__header__": "x",
        "not_adc": np.ones((8, 8), dtype=np.float64),
        "adc_small": np.zeros((8, 8, 2, 2), dtype=np.float32),
        "adc_big": np.zeros((16, 16, 4, 2), dtype=np.complex64),
    }

    arr, key = select_4d_numeric_array(payload, variable=None)
    assert key == "adc_big"
    assert arr.shape == (16, 16, 4, 2)

    arr2, key2 = select_4d_numeric_array(payload, variable="adc_small")
    assert key2 == "adc_small"
    assert arr2.shape == (8, 8, 2, 2)

    failed = False
    try:
        select_4d_numeric_array(payload, variable="not_adc")
    except ValueError:
        failed = True
    assert failed

    failed2 = False
    try:
        select_4d_numeric_array({"a": np.ones((4, 4), dtype=np.float64)}, variable=None)
    except ValueError:
        failed2 = True
    assert failed2

    print("MAT ADC extractor core validation passed.")


if __name__ == "__main__":
    run()

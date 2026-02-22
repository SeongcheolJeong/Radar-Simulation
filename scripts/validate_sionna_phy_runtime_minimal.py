#!/usr/bin/env python3
import math


def run() -> None:
    import tensorflow as tf
    import sionna
    from sionna.phy.utils import ebnodb2no

    x = tf.constant([[1.0, 2.0]], dtype=tf.float32)
    y = tf.linalg.matmul(x, tf.transpose(x))
    y_val = float(y.numpy().reshape(-1)[0])
    if not math.isclose(y_val, 5.0, rel_tol=1e-6, abs_tol=1e-6):
        raise AssertionError(f"unexpected tf matmul result: {y_val}")

    no = ebnodb2no(10.0, num_bits_per_symbol=2, coderate=1.0)
    no_val = float(no.numpy().reshape(-1)[0])
    if not math.isclose(no_val, 0.05, rel_tol=1e-4, abs_tol=1e-4):
        raise AssertionError(f"unexpected ebnodb2no value: {no_val}")

    print(f"validate_sionna_phy_runtime_minimal: pass (sionna {sionna.__version__})")


if __name__ == "__main__":
    run()

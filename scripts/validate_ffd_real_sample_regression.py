#!/usr/bin/env python3
from pathlib import Path

import numpy as np

from avxsim.ffd import FfdPattern


def run() -> None:
    root = Path(__file__).resolve().parents[1]
    sample = root / "tests" / "data" / "ffd" / "pyaedt_T04_test.ffd"
    assert sample.exists(), str(sample)

    pat = FfdPattern.from_file(str(sample), field_format="real_imag")
    # This real sample has one theta slice and dense phi sweep.
    assert pat.theta_deg.size == 1, pat.theta_deg.size
    assert pat.phi_deg.size >= 180, pat.phi_deg.size
    assert pat.etheta.shape == (pat.theta_deg.size, pat.phi_deg.size)
    assert pat.ephi.shape == (pat.theta_deg.size, pat.phi_deg.size)
    assert np.all(np.isfinite(np.real(pat.etheta)))
    assert np.all(np.isfinite(np.imag(pat.etheta)))

    # Spot-check that lookup returns finite complex gains.
    g0 = pat.gain_from_azel(az_deg=0.0, el_deg=90.0)
    g1 = pat.gain_from_azel(az_deg=45.0, el_deg=90.0)
    g2 = pat.gain_from_azel(az_deg=180.0, el_deg=90.0)
    assert np.isfinite(np.real(g0)) and np.isfinite(np.imag(g0))
    assert np.isfinite(np.real(g1)) and np.isfinite(np.imag(g1))
    assert np.isfinite(np.real(g2)) and np.isfinite(np.imag(g2))

    # Regression anchor: keep one deterministic value check.
    et_ref = pat.etheta[0, 0]
    ep_ref = pat.ephi[0, 0]
    assert abs(np.real(et_ref) + 1.483427722) < 1e-6, et_ref
    assert abs(np.imag(et_ref) + 0.8592655294) < 1e-6, et_ref
    assert abs(np.real(ep_ref) - 5.840127509) < 1e-6, ep_ref
    assert abs(np.imag(ep_ref) + 2.125146534) < 1e-6, ep_ref

    print("FFD real-sample regression validation passed.")


if __name__ == "__main__":
    run()


#!/usr/bin/env python3
import tempfile
from pathlib import Path

import numpy as np

from avxsim.ffd import FfdPattern


def _write_test_ffd(path: Path, gain_map):
    lines = ["# synthetic ffd", "# theta phi et_re et_im ep_re ep_im"]
    for th in [0.0, 90.0, 180.0]:
        for ph in [0.0, 90.0, 180.0, 270.0]:
            g = gain_map(float(th), float(ph))
            lines.append(f"{th:.1f} {ph:.1f} {np.real(g):.8f} {np.imag(g):.8f} 0.0 0.0")
    path.write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "pat.ffd"

        def gain_map(theta, phi):
            # intentionally complex-valued with theta/phi dependence
            return (1.0 + 0.1 * np.cos(np.deg2rad(theta))) * np.exp(1j * np.deg2rad(phi))

        _write_test_ffd(p, gain_map)
        pat = FfdPattern.from_file(str(p), field_format="real_imag")

        # grid exact point
        g1 = pat.gain_from_azel(az_deg=90.0, el_deg=0.0)
        expected1 = gain_map(90.0, 90.0)
        assert abs(g1 - expected1) < 1e-9

        # periodic phi wrap: 360 == 0
        g2 = pat.gain_from_azel(az_deg=360.0, el_deg=0.0)
        g3 = pat.gain_from_azel(az_deg=0.0, el_deg=0.0)
        assert abs(g2 - g3) < 1e-9

        # interpolation sanity: midpoint between phi=0 and phi=90
        g_mid = pat.gain_from_azel(az_deg=45.0, el_deg=0.0)
        assert np.isfinite(np.real(g_mid))
        assert np.isfinite(np.imag(g_mid))

    print("FFD parser/interpolation validation passed.")


if __name__ == "__main__":
    run()


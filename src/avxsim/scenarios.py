from typing import List, Sequence, Tuple

from .constants import C0
from .types import Path


def make_static_paths(
    n_chirps: int,
    range_m: float,
    amp: complex,
    unit_direction: Tuple[float, float, float],
) -> List[List[Path]]:
    delay_s = 2.0 * range_m / C0
    p = Path(delay_s=delay_s, doppler_hz=0.0, unit_direction=unit_direction, amp=amp)
    return [[p] for _ in range(n_chirps)]


def make_constant_velocity_paths(
    n_chirps: int,
    range_m: float,
    radial_velocity_mps: float,
    fc_hz: float,
    amp: complex,
    unit_direction: Tuple[float, float, float],
) -> List[List[Path]]:
    delay_s = 2.0 * range_m / C0
    lam = C0 / fc_hz
    doppler_hz = 2.0 * radial_velocity_mps / lam
    p = Path(delay_s=delay_s, doppler_hz=doppler_hz, unit_direction=unit_direction, amp=amp)
    return [[p] for _ in range(n_chirps)]


def make_two_path_multipath(
    n_chirps: int,
    ranges_m: Sequence[float],
    amps: Sequence[complex],
    unit_direction: Tuple[float, float, float],
) -> List[List[Path]]:
    if len(ranges_m) != len(amps):
        raise ValueError("ranges_m and amps length mismatch")
    chirp_paths: List[List[Path]] = []
    for _ in range(n_chirps):
        row: List[Path] = []
        for r, a in zip(ranges_m, amps):
            row.append(
                Path(
                    delay_s=2.0 * float(r) / C0,
                    doppler_hz=0.0,
                    unit_direction=unit_direction,
                    amp=complex(a),
                )
            )
        chirp_paths.append(row)
    return chirp_paths


from dataclasses import dataclass
from typing import Sequence, Tuple


@dataclass(frozen=True)
class Path:
    delay_s: float
    doppler_hz: float
    unit_direction: Tuple[float, float, float]
    amp: complex


@dataclass(frozen=True)
class RadarConfig:
    fc_hz: float
    slope_hz_per_s: float
    fs_hz: float
    samples_per_chirp: int
    tx_schedule: Sequence[int]


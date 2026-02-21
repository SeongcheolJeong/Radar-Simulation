from dataclasses import dataclass
from typing import Optional, Sequence, Tuple


@dataclass(frozen=True)
class Path:
    delay_s: float
    doppler_hz: float
    unit_direction: Tuple[float, float, float]
    amp: complex
    pol_matrix: Optional[Tuple[complex, complex, complex, complex]] = None
    path_id: Optional[str] = None
    material_tag: Optional[str] = None
    reflection_order: Optional[int] = None


@dataclass(frozen=True)
class RadarConfig:
    fc_hz: float
    slope_hz_per_s: float
    fs_hz: float
    samples_per_chirp: int
    tx_schedule: Sequence[int]

import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from ..constants import C0
from ..types import Path as RadarPath


def _to_unit_direction(az_deg: float, el_deg: float) -> Tuple[float, float, float]:
    az = math.radians(az_deg)
    el = math.radians(el_deg)
    x = math.cos(el) * math.cos(az)
    y = math.cos(el) * math.sin(az)
    z = math.sin(el)
    return (x, y, z)


def _amp_from_record(rec: Dict[str, Any]) -> complex:
    if "amp_complex" in rec:
        v = rec["amp_complex"]
        if isinstance(v, dict):
            return complex(float(v.get("re", 0.0)), float(v.get("im", 0.0)))
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return complex(float(v[0]), float(v[1]))
        raise ValueError("amp_complex must be {re,im} or [re,im]")

    if "amp" in rec:
        return complex(rec["amp"])

    # fallback: strength/power-only records
    if "power_linear" in rec:
        return complex(math.sqrt(float(rec["power_linear"])))
    if "strength_linear" in rec:
        return complex(float(rec["strength_linear"]))
    return 1.0 + 0.0j


def _delay_from_record(rec: Dict[str, Any]) -> float:
    if "delay_s" in rec:
        return float(rec["delay_s"])
    if "range_m" in rec:
        return 2.0 * float(rec["range_m"]) / C0
    raise ValueError("record must include delay_s or range_m")


def _doppler_from_record(rec: Dict[str, Any], fc_hz: Optional[float]) -> float:
    if "doppler_hz" in rec:
        return float(rec["doppler_hz"])
    if "radial_velocity_mps" in rec:
        if not fc_hz:
            raise ValueError("fc_hz required when radial_velocity_mps is provided")
        lam = C0 / float(fc_hz)
        return 2.0 * float(rec["radial_velocity_mps"]) / lam
    return 0.0


def _direction_from_record(rec: Dict[str, Any]) -> Tuple[float, float, float]:
    if "unit_direction" in rec:
        u = rec["unit_direction"]
        if not isinstance(u, (list, tuple)) or len(u) != 3:
            raise ValueError("unit_direction must have length 3")
        return (float(u[0]), float(u[1]), float(u[2]))
    if "az_deg" in rec:
        return _to_unit_direction(float(rec["az_deg"]), float(rec.get("el_deg", 0.0)))
    if "aod_az_deg" in rec:
        return _to_unit_direction(float(rec["aod_az_deg"]), float(rec.get("aod_el_deg", 0.0)))
    raise ValueError("record must include unit_direction or az/el")


def _pol_matrix_from_record(rec: Dict[str, Any]):
    if "pol_matrix" not in rec:
        return None
    p = rec["pol_matrix"]
    if isinstance(p, dict):
        vals = [
            p.get("m00", {"re": 1.0, "im": 0.0}),
            p.get("m01", {"re": 0.0, "im": 0.0}),
            p.get("m10", {"re": 0.0, "im": 0.0}),
            p.get("m11", {"re": 1.0, "im": 0.0}),
        ]
        out = []
        for v in vals:
            if isinstance(v, dict):
                out.append(complex(float(v.get("re", 0.0)), float(v.get("im", 0.0))))
            else:
                out.append(complex(v))
        return tuple(out)
    if isinstance(p, (list, tuple)) and len(p) == 4:
        out = []
        for v in p:
            if isinstance(v, dict):
                out.append(complex(float(v.get("re", 0.0)), float(v.get("im", 0.0))))
            elif isinstance(v, (list, tuple)) and len(v) == 2:
                out.append(complex(float(v[0]), float(v[1])))
            else:
                out.append(complex(v))
        return tuple(out)
    raise ValueError("pol_matrix must be length-4 list or dict with m00,m01,m10,m11")


def adapt_records_by_chirp(
    records_by_chirp: Sequence[Iterable[Dict[str, Any]]],
    fc_hz: Optional[float] = None,
) -> List[List[RadarPath]]:
    """
    Convert generic RT records into canonical paths_by_chirp.

    The adapter is intentionally permissive to support evolving upstream
    record formats while keeping local simulation contracts stable.
    """
    out: List[List[RadarPath]] = []
    for chirp_records in records_by_chirp:
        row: List[RadarPath] = []
        for rec in chirp_records:
            row.append(
                RadarPath(
                    delay_s=_delay_from_record(rec),
                    doppler_hz=_doppler_from_record(rec, fc_hz=fc_hz),
                    unit_direction=_direction_from_record(rec),
                    amp=_amp_from_record(rec),
                    pol_matrix=_pol_matrix_from_record(rec),
                )
            )
        out.append(row)
    return out


def load_records_by_chirp_json(json_path: str) -> List[List[Dict[str, Any]]]:
    p = Path(json_path)
    with p.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError("JSON root must be a list of chirp record lists")
    for idx, chirp in enumerate(payload):
        if not isinstance(chirp, list):
            raise ValueError(f"payload[{idx}] must be list")
    return payload

import json
from pathlib import Path
from typing import Any, Dict, Mapping

from .po_sbr_paths import adapt_po_sbr_paths_payload_to_paths_by_chirp


def load_radarsimpy_paths_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("radarsimpy paths json must be object")
    return dict(payload)


def adapt_radarsimpy_paths_payload_to_paths_by_chirp(
    payload: Mapping[str, Any],
    n_chirps: int,
    fc_hz: float,
):
    # RadarSimPy integration accepts the same canonical path payload schema
    # as the PO-SBR adapter path format.
    return adapt_po_sbr_paths_payload_to_paths_by_chirp(
        payload=payload,
        n_chirps=int(n_chirps),
        fc_hz=float(fc_hz),
    )

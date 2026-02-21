from pathlib import Path as FilePath
from typing import Protocol, Sequence, Tuple

import numpy as np

from .ffd import FieldFormat, FfdPattern
from .types import Path as RadarPath


class AntennaModel(Protocol):
    def tx_gain(self, tx_idx: int, path: RadarPath) -> complex:
        ...

    def rx_gain(self, path: RadarPath, n_rx: int) -> np.ndarray:
        ...


class IsotropicAntenna:
    def tx_gain(self, tx_idx: int, path: RadarPath) -> complex:
        _ = tx_idx
        _ = path
        return 1.0 + 0.0j

    def rx_gain(self, path: RadarPath, n_rx: int) -> np.ndarray:
        _ = path
        return np.ones((n_rx,), dtype=np.complex128)


class FfdAntennaModel:
    def __init__(
        self,
        tx_patterns: Sequence[FfdPattern],
        rx_patterns: Sequence[FfdPattern],
        tx_pol_weights: Tuple[complex, complex] = (1.0 + 0.0j, 0.0 + 0.0j),
        rx_pol_weights: Tuple[complex, complex] = (1.0 + 0.0j, 0.0 + 0.0j),
    ) -> None:
        if not tx_patterns or not rx_patterns:
            raise ValueError("tx_patterns and rx_patterns must be non-empty")
        self._tx_patterns = list(tx_patterns)
        self._rx_patterns = list(rx_patterns)
        self._tx_pol = tx_pol_weights
        self._rx_pol = rx_pol_weights

    @staticmethod
    def from_files(
        tx_ffd_files: Sequence[str],
        rx_ffd_files: Sequence[str],
        n_tx: int,
        n_rx: int,
        field_format: FieldFormat = "auto",
        tx_pol_weights: Tuple[complex, complex] = (1.0 + 0.0j, 0.0 + 0.0j),
        rx_pol_weights: Tuple[complex, complex] = (1.0 + 0.0j, 0.0 + 0.0j),
    ) -> "FfdAntennaModel":
        tx_files = _resolve_ffd_list(tx_ffd_files, n_expected=n_tx)
        rx_files = _resolve_ffd_list(rx_ffd_files, n_expected=n_rx)
        tx_patterns = [FfdPattern.from_file(p, field_format=field_format) for p in tx_files]
        rx_patterns = [FfdPattern.from_file(p, field_format=field_format) for p in rx_files]
        return FfdAntennaModel(
            tx_patterns=tx_patterns,
            rx_patterns=rx_patterns,
            tx_pol_weights=tx_pol_weights,
            rx_pol_weights=rx_pol_weights,
        )

    def tx_gain(self, tx_idx: int, path: RadarPath) -> complex:
        if tx_idx < 0 or tx_idx >= len(self._tx_patterns):
            raise ValueError(f"tx_idx out of range: {tx_idx}")
        return self._tx_patterns[tx_idx].gain_from_unit_direction(
            path.unit_direction,
            pol_weights=self._tx_pol,
        )

    def rx_gain(self, path: RadarPath, n_rx: int) -> np.ndarray:
        if n_rx != len(self._rx_patterns):
            raise ValueError(f"n_rx mismatch: {n_rx} != {len(self._rx_patterns)}")
        out = np.zeros((n_rx,), dtype=np.complex128)
        for i in range(n_rx):
            out[i] = self._rx_patterns[i].gain_from_unit_direction(
                path.unit_direction,
                pol_weights=self._rx_pol,
            )
        return out


def _resolve_ffd_list(files: Sequence[str], n_expected: int) -> Sequence[str]:
    items = [str(FilePath(x)) for x in files if str(x).strip()]
    if not items:
        raise ValueError("empty .ffd file list")
    if len(items) == 1 and n_expected > 1:
        items = items * n_expected
    if len(items) != n_expected:
        raise ValueError(f".ffd file count mismatch: got {len(items)}, expected {n_expected}")
    for p in items:
        if not FilePath(p).exists():
            raise FileNotFoundError(f".ffd file not found: {p}")
    return items

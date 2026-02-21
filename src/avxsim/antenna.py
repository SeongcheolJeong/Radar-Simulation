from typing import Protocol

import numpy as np

from .types import Path


class AntennaModel(Protocol):
    def tx_gain(self, tx_idx: int, path: Path) -> complex:
        ...

    def rx_gain(self, path: Path, n_rx: int) -> np.ndarray:
        ...


class IsotropicAntenna:
    def tx_gain(self, tx_idx: int, path: Path) -> complex:
        _ = tx_idx
        _ = path
        return 1.0 + 0.0j

    def rx_gain(self, path: Path, n_rx: int) -> np.ndarray:
        _ = path
        return np.ones((n_rx,), dtype=np.complex128)


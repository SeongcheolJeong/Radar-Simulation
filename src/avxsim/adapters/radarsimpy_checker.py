import numpy as np


def to_radarsimpy_view(adc: np.ndarray) -> np.ndarray:
    """
    Convert canonical adc[sample, chirp, tx, rx] to
    radarsimpy-style view data[channel, pulse, sample].
    """
    if adc.ndim != 4:
        raise ValueError("adc must have shape (sample, chirp, tx, rx)")
    n_sample, n_chirp, n_tx, n_rx = adc.shape
    flattened = adc.reshape(n_sample, n_chirp, n_tx * n_rx)
    # [sample, chirp, channel] -> [channel, pulse, sample]
    return np.transpose(flattened, (2, 1, 0))


def validate_radarsimpy_view_shape(data: np.ndarray, n_channels: int, n_pulses: int, n_samples: int) -> None:
    if data.shape != (n_channels, n_pulses, n_samples):
        raise ValueError(
            "unexpected shape: "
            f"{data.shape} != ({n_channels}, {n_pulses}, {n_samples})"
        )


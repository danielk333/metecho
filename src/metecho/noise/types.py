from typing import NamedTuple

import numpy as np
import numpy.typing as npt


class GaussianNoise(NamedTuple):
    mean: float
    std_dev: float
    confidence_interval: tuple[float, float]


class GaussianNoiseChunks(NamedTuple):
    mean: npt.NDArray[np.floating]
    std_dev: npt.NDArray[np.floating]
    confidence_interval: npt.NDArray[np.floating]
    epoch_us: int
    chunk_size_usec: int

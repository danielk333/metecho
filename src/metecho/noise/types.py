from typing import NamedTuple

import numpy as np


class GaussianNoise(NamedTuple):
    mean: np.floating
    std_dev: np.floating
    confidence_interval: tuple[np.floating, np.floating]

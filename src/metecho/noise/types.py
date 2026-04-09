from typing import NamedTuple


class GaussianNoise(NamedTuple):
    mean: float
    std_dev: float
    confidence_interval: tuple[float, float]

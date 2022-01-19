import numpy as np
from scipy.stats.distributions import chi2
from abc import ABC, abstractmethod


class NoiseObject(ABC):
    def __init__(self, **kwargs):
        self.arguments = kwargs
        super().__init__()

    @abstractmethod
    def calc(self, raw_data):
        pass


class CalculateGaussianNoise(NoiseObject):
    """
    Calculates the gaussian noise for a filtered_data object
    """

    def calc(self, filtered_data, axis):
        confidence_probability = 0.000001
        echo_location = []
        channel_size = filtered_data.shape[axis]
        s_noise_all = np.array(np.concatenate(
            (filtered_data.real, filtered_data.imag), axis=None), dtype=np.float64)
        sig_est_freedom = len(s_noise_all) - 1
        mean = np.mean(s_noise_all)
        std_dev = np.std(s_noise_all)
        confidence_interval = [np.sqrt(
            sig_est_freedom * np.square(std_dev) / chi2.ppf(
                confidence_probability / 2,
                sig_est_freedom)
        ), np.sqrt(
            sig_est_freedom * np.square(std_dev) / chi2.ppf(
                1 - (confidence_probability / 2),
                sig_est_freedom)
        )]
        return {'mean': mean, 'std_dev': std_dev, 'confidence_interval': confidence_interval}

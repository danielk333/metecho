import numpy as np
from scipy.stats.distributions import chi2
from abc import ABC, abstractmethod


class FilterObject(ABC):
    def __init__(self, **kwargs):
        self.arguments = kwargs
        super().__init__()

    @abstractmethod
    def filter(self, raw_data):
        pass


class CalculateGaussianNoise(FilterObject):
    """
    Calculates the gaussian noise for a raw_data object
    """

    def filter(self, raw_data):
        confidence_probability = 0.000001
        echo_location = []
        channel_size = raw_data.data[raw_data.axis["channel"]].size
        s_noise_all = np.array(np.concatenate(
            (raw_data.data.real, raw_data.data.imag), axis=None), dtype=np.float64)
        sig_est_freedom = len(s_noise_all) - 1
        mean = np.mean(s_noise_all)
        std_dev = np.std(s_noise_all)
        CI = [np.sqrt(
            sig_est_freedom * np.square(std_dev) / chi2.ppf(
                confidence_probability / 2,
                sig_est_freedom)
        ), np.sqrt(
            sig_est_freedom * np.square(std_dev) / chi2.ppf(
                1 - (confidence_probability / 2),
                sig_est_freedom)
        )]
        return {'mean': mean, 'std_dev': std_dev, 'CI': CI}

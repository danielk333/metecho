import numpy as np
import numpy.typing as npt
from scipy.stats.distributions import chi2  # type: ignore[attr-defined]

from metecho.noise.types import GaussianNoise


def calc_gaussian_noise(data: npt.NDArray[np.complex128]) -> GaussianNoise:
    """
    Calculate gaussain noise.

    Args:
        raw_data: Data to calculate noise on. It is expected that peaks has been filtered out from the data before to get a correct noise estimation.
    Returns:
        Gaussian noise

    """

    confidence_probability = 0.000001
    s_noise_all = np.array(np.concatenate((data.real, data.imag), axis=None), dtype=np.float64)
    sig_est_freedom = len(s_noise_all) - 1
    mean = np.mean(s_noise_all)
    std_dev = np.std(s_noise_all)
    confidence_interval = (
        np.sqrt(sig_est_freedom * np.square(std_dev) / chi2.ppf(confidence_probability / 2, sig_est_freedom)),
        np.sqrt(
            sig_est_freedom * np.square(std_dev) / chi2.ppf(1 - (confidence_probability / 2), sig_est_freedom)
        ),
    )
    return GaussianNoise(mean=mean, std_dev=std_dev, confidence_interval=confidence_interval)

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
    return GaussianNoise(mean=float(mean), std_dev=float(std_dev), confidence_interval=confidence_interval)


def calc_gaussian_noise_from_batches(
    mean_per_batch: npt.NDArray, std_dev_per_batch: npt.NDArray, batch_size: int
) -> GaussianNoise:

    mean, std_dev = calc_batch_mean_and_std_dev(mean_per_batch, std_dev_per_batch, batch_size)

    confidence_probability = 0.000001
    sig_est_freedom = len(mean_per_batch) * batch_size * 2 - 1
    confidence_interval = (
        np.sqrt(sig_est_freedom * np.square(std_dev) / chi2.ppf(confidence_probability / 2, sig_est_freedom)),
        np.sqrt(
            sig_est_freedom * np.square(std_dev) / chi2.ppf(1 - (confidence_probability / 2), sig_est_freedom)
        ),
    )
    return GaussianNoise(mean=mean, std_dev=std_dev, confidence_interval=confidence_interval)


def calc_batch_mean_and_std_dev(
    mean_per_batch: npt.NDArray, std_dev_per_batch: npt.NDArray, samples_per_batch: int
) -> tuple[float, float]:
    # https://stats.stackexchange.com/a/442050
    n_batches = len(mean_per_batch)
    mean = np.mean(mean_per_batch)

    var_sum = np.sum(
        std_dev_per_batch**2 * samples_per_batch + samples_per_batch * (mean - mean_per_batch) ** 2
    )
    std_dev = np.sqrt(var_sum / (samples_per_batch * n_batches))

    return mean, std_dev

import numpy as np
import numpy.typing as npt
from radardef.tools.mpi_tools import MPIProgress
from scipy.stats.distributions import chi2  # type: ignore[attr-defined]

from metecho.noise.types import GaussianNoise


def calc_gaussian_noise(data: npt.NDArray[np.complex128]) -> GaussianNoise:
    """
    Calculate gaussain noise.

    Args:
        raw_data: Data to calculate noise on.
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


def calc_gaussian_noise_batch_chunks(
    mean_per_batch: npt.NDArray,
    std_dev_per_batch: npt.NDArray,
    batch_size: int,
    chunk_size: int,
    progress: bool = False,
) -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating], npt.NDArray[np.floating]]:
    """
    Calculate the gaussian noise in the requested chunk size from a serier of batches.

    ```
    |s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s|s| original data is in samples
    |--b--|--b--|--b--|--b--|--b--|--b--|--b--|--b--|--b--|--b--|--b--|--b--| from x amount if samples a batch of mean and std dev is calculated
    |--------c--------|--------c--------|--------c--------|--------c--------| from these batches we can calculate a mean and std dev of requested sizes
    ```
    Args:
        mean_per_batch: Calculated mean for each batch
        std_dev_per_batch : Calculated standard deviation for each batch
        batch_size: number of samples per batch
        chunk_size: Number of batches per chunk

    Returns
        Gaussian noise for each chunk derived from the batches. (mean, std_dev, confidence_interval)
    """

    if mean_per_batch.shape != std_dev_per_batch.shape:
        raise ValueError("mean and std dev those not have the same amount of batches")

    # If chunk size is larger than the size of the input, estimate over the available data
    if len(mean_per_batch) < chunk_size:
        chunk_size = len(mean_per_batch)

    # Calculate what does not fit in the chunks
    remenants = len(mean_per_batch) % chunk_size

    # Divide into chunks
    mean_chunks = mean_per_batch[:-remenants].reshape(-1, chunk_size)
    std_dev_chunks = std_dev_per_batch[:-remenants].reshape(-1, chunk_size)

    # Output arrays
    length = mean_chunks.shape[0] + (1 if remenants else 0)
    mean = np.zeros((length,))
    std_dev = np.zeros((length,))
    confidence_interval = np.zeros((length, 2))

    if progress:
        prog = MPIProgress(tot=length, desc="Estimating Noise", barrier_on_close=False)

    else:
        prog = None

    # Calculate mean and std dev for each chunk
    for i in range(length):
        if i == length - 1 and remenants:
            mean_chunk = mean_per_batch[-remenants:]
            std_dev_chunk = std_dev_per_batch[-remenants:]
        else:
            mean_chunk = mean_chunks[i]
            std_dev_chunk = std_dev_chunks[i]

        mean[i], std_dev[i] = calc_batch_mean_and_std_dev(mean_chunk, std_dev_chunk, batch_size)

        confidence_probability = 0.000001
        sig_est_freedom = len(mean_chunk) * batch_size * 2 - 1

        confidence_interval[i, 0] = np.sqrt(
            sig_est_freedom * np.square(std_dev[i]) / chi2.ppf(confidence_probability / 2, sig_est_freedom)
        )
        confidence_interval[i, 1] = np.sqrt(
            sig_est_freedom
            * np.square(std_dev[i])
            / chi2.ppf(1 - (confidence_probability / 2), sig_est_freedom)
        )

        if prog:
            prog.update(1)

    if prog:
        prog.close()

    return mean, std_dev, confidence_interval


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

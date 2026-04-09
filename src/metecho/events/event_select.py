from configparser import ConfigParser

import numpy as np
import numpy.typing as npt
from scipy.signal import savgol_filter  # type: ignore[attr-defined]


def cluster(
    event_indices: npt.NDArray[np.integer],
    best_doppler: npt.NDArray,
    best_start: npt.NDArray[np.integer],
    config: ConfigParser,
) -> npt.NDArray[np.int64]:
    """

    Args:
        event_indices: Bool array marking the ipps with detected event.
        best_doppler: Best doppler array from echo search.
        best_start: Array containing the indices with max power each ipp.
        config: configuration parser.

    Returns:
        List containing each start and stop ipp for each event, shape (N_events, 2)
    """

    event_ipp_indices: list[tuple[int, int]] = []

    if event_indices.size < config.getint("General", "least_ipp_available"):
        return np.array(event_ipp_indices)

    smooth_doppler = savgol_filter(
        best_doppler[event_indices].flatten(),
        config.getint("General", "smoothing_window"),
        config.getint("General", "polyorder"),
    )
    smooth_start = savgol_filter(
        best_start[event_indices].flatten(),
        config.getint("General", "smoothing_window"),
        config.getint("General", "polyorder"),
    )

    indices_diff = np.diff(event_indices)
    doppler_diff = np.abs(np.diff(smooth_doppler))
    start_diff = np.abs(np.diff(smooth_start))

    split_metric = [
        indices_diff >= config.getint("General", "min_ipp_separation_split"),
        start_diff >= config.getfloat("General", "min_range_separation_split"),
        doppler_diff >= config.getfloat("General", "min_dop_separation_split"),
    ]

    split_indices = np.argwhere(np.sum(split_metric, 0) >= 1)
    split_indices = np.append(split_indices, len(event_indices))

    new_indices = []
    start_index = 0

    for x in range(len(split_indices)):
        new_indices.append(event_indices[start_index : split_indices[x]])
        start_index = split_indices[x]

    least_ipp_available = config.getint("General", "least_ipp_available")
    IPP_extend = config.getint("General", "IPP_extend")

    for x in range(len(new_indices)):
        if len(new_indices[x]) > least_ipp_available:
            event_ipp_indices.append(
                (np.amin(new_indices[x]) - IPP_extend, np.amax(new_indices[x]) + IPP_extend)
            )

    return np.array(event_ipp_indices)

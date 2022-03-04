import numpy as np
from scipy.signal import savgol_filter


def cluster(found_indices, best_doppler, best_start, config):
    start_IPP = []
    end_IPP = []

    if found_indices.size < config.getint("General", "least_ipp_available"):
        return start_IPP, end_IPP

    smooth_doppler = savgol_filter(
        best_doppler[found_indices.flatten()].flatten(),
        config.getint("General", "smoothing_window"),
        config.getint("General", "polyorder"),
    )
    smooth_start = savgol_filter(
        best_start[found_indices.flatten()].flatten(),
        config.getint("General", "smoothing_window"),
        config.getint("General", "polyorder"),
    )

    indices_diff = np.diff(found_indices.flatten())
    doppler_diff = np.abs(np.diff(smooth_doppler))
    start_diff = np.abs(np.diff(smooth_start))

    split_metric = [
        indices_diff >= config.getint("General", "min_ipp_separation_split"),
        start_diff >= config.getfloat("General", "min_range_separation_split"),
        doppler_diff >= config.getfloat("General", "min_dop_separation_split")
    ]

    split_indices = np.argwhere(np.sum(split_metric, 0) >= 1)
    split_indices = np.append(split_indices, len(found_indices))

    new_indices = []
    start_index = 0

    for x in range(len(split_indices)):
        new_indices.append(
            found_indices.flatten()[start_index:split_indices[x]]
        )
        start_index = split_indices[x]

    least_ipp_available = config.getint("General", "least_ipp_available")
    IPP_extend = config.getint("General", "IPP_extend")

    for x in range(len(new_indices)):
        if len(new_indices[x]) > least_ipp_available:
            start_IPP.append(np.amin(new_indices[x]) - IPP_extend)
            end_IPP.append(np.amax(new_indices[x]) + IPP_extend)

    return start_IPP, end_IPP

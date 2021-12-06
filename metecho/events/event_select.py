import numpy as np
from scipy.signal import savgol_filter


def cluster(found_indices, best_doppler, best_start, config):
    start_IPP = []
    end_IPP = []

    if found_indices.size < config.getint("General", "least_ipp_available"):
        return start_IPP, end_IPP

    smooth_doppler = savgol_filter(best_doppler[found_indices].flatten(),
                                   config.getint("General", "smoothing_window"),
                                   config.getint("General", "polyorder"))
    smooth_start = savgol_filter(best_start[found_indices].flatten(),
                                 config.getint("General", "smoothing_window"),
                                 config.getint("General", "polyorder"))

    indices_diff = np.diff(found_indices)
    doppler_diff = np.abs(np.diff(smooth_doppler))
    start_diff = np.abs(np.diff(smooth_start))

    split_metric = [
        indices_diff >= config.getfloat("General", "min_ipp_separation_split"),
        start_diff >= config.getfloat("General", "min_range_separation_split"),
        doppler_diff >= config.getfloat("General", "min_dop_separation_split")
    ]

    print(split_metric)

    return start_IPP, end_IPP

import numpy as np
import copy
from . import conf, event_select, search_objects
from metecho.generalized_matched_filter import xcorr, signal_model
from metecho.noise import calc_noise
import logging


logger = logging.getLogger(__name__)


def mergeDict(dict1, dict2, axis=None):
    """
    Merges two dicts while trying to concatenate np-arrays where possible
    """
    dict3 = {**dict1, **dict2}
    for key, value in dict3.items():
        if key in dict1 and key in dict2:
            if type(value) == np.ndarray and value.ndim > 1:
                dict3[key] = np.concatenate((value, dict1[key]), axis=axis)
            elif type(value) == np.ndarray:
                dict3[key] = np.concatenate((value, dict1[key]))
            else:
                dict3[key] = [value, dict1[key]]
    return dict3


def search(raw_data, config, matched_filter_output, signal, filters=None, search_function_objects=None):
    """
    Searches for potential events from the filtered data and establishes if they can be analyzed further.
    """
    events = []
    matched_filter_output["doppler_coherrence"] = 0
    matched_filter_output["start_coherrence"] = 0
    if "best_doppler" not in matched_filter_output:
        matched_filter_output["best_doppler"] = []
    if "best_start" not in matched_filter_output:
        matched_filter_output["best_start"] = []

    # Barker thing here
    if raw_data is not None:
        if matched_filter_output is not None:
            raw_data_pulse_length = raw_data.data.shape[raw_data.axis["pulse"]]
            if matched_filter_output["pulse_length"] < raw_data_pulse_length:
                temp_raw_data = copy.deepcopy(raw_data)
                temp_raw_data.data = temp_raw_data.data[
                    :,
                    :,
                    matched_filter_output["pulse_length"]:
                ]
                append_data = xcorr.xcorr_echo_search(
                    temp_raw_data,
                    config.getint("General", "dop_min_freq"),
                    config.getint("General", "dop_max_freq"),
                    config.getint("General", "dop_step_size"),
                    signal
                )
                matched_filter_output = mergeDict(matched_filter_output, append_data, axis=1)
                matched_filter_output["pulse_length"] = np.sum(matched_filter_output["pulse_length"])

        else:
            matched_filter_output = xcorr.xcorr_echo_search(
                raw_data,
                config.getint("General", "dop_min_freq"),
                config.getint("General", "dop_max_freq"),
                config.getint("General", "dop_step_size"),
                signal
            )
        matched_filter_output["tot_pow"] = np.squeeze(np.sum(np.square(np.abs(np.sum(raw_data.data, 0))), 1))

        matched_filter_output["doppler_window"] = np.lib.stride_tricks.sliding_window_view(
            matched_filter_output["best_doppler"],
            config.getint("General", "MOVE_STD_WINDOW")
        )
        matched_filter_output["start_window"] = np.lib.stride_tricks.sliding_window_view(
            matched_filter_output["best_start"],
            config.getint("General", "MOVE_STD_WINDOW")
        )

        matched_filter_output["doppler_std"] = np.std(matched_filter_output["doppler_window"], axis=0)
        start_std = np.std(matched_filter_output["start_window"], axis=0)

        matched_filter_output["doppler_coherrence"] = np.sum(
            matched_filter_output["doppler_std"] < config.getfloat(
                "General", "dop_std_coherr") / len(matched_filter_output["doppler_std"])
        )
        matched_filter_output["start_coherrence"] = np.sum(
            start_std < config.getfloat("General", "start_std_coherr") / len(start_std)
        )

        matched_filter_output["gauss_noise"] = calc_noise.CalculateGaussianNoise().calc(raw_data)

        matched_filter_output["filter_indices"] = (matched_filter_output["tot_pow"]
                                                   < matched_filter_output["gauss_noise"]["mean"]
                                                   + config.getfloat("General", "pow_std_est")
                                                   * matched_filter_output["gauss_noise"]["std_dev"])

        if not np.any(matched_filter_output["filter_indices"]):
            logger.debug("No matches found, returning...")
            return events

        matched_filter_output["best_peak_filt"] = \
            matched_filter_output["best_peak"][matched_filter_output["filter_indices"]]
        matched_filter_output["tot_pow_filt"] = \
            matched_filter_output["tot_pow"][matched_filter_output["filter_indices"]]

    find_indices = []
    find_indices_req = []
    find_indices_trail = []
    if search_function_objects is None:
        search_function_objects = search_objects.get_defaults()
    for searcher in search_function_objects:
        curr = searcher.search(matched_filter_output, raw_data, config)
        events.append(curr)
        if searcher.trailable:
            if find_indices_trail != []:
                find_indices_trail = np.logical_and(curr, find_indices_trail)
            else:
                find_indices_trail = curr
        if searcher.required:
            if find_indices_req != []:
                find_indices_req = np.logical_and(curr, find_indices_req)
            else:
                find_indices_req = curr
        else:
            if find_indices != []:
                find_indices = curr * 1 + find_indices * 1
            else:
                find_indices = curr * 1

    if find_indices_req == []:
        found_indices = np.argwhere(np.array(find_indices >= config.getint("General", "CRITERIA_N")))
    else:
        found_indices = np.argwhere(np.logical_and(find_indices_req, find_indices
                                                   >= config.getint("General", "CRITERIA_N")))

    start_IPP, end_IPP = event_select.cluster(
        found_indices,
        matched_filter_output["best_doppler"],
        matched_filter_output["best_start"],
        config
    )

    if np.any(find_indices_trail):
        found_indices_trail = np.argwhere(
            np.logical_not(
                np.logical_and(
                    find_indices_trail,
                    find_indices >= config.getint("General", "CRITERIA_N"))))
    else:
        found_indices_trail = []

    if np.any(found_indices_trail):
        start_IPP_trail, end_IPP_trail = event_select.cluster(
            found_indices_trail,
            matched_filter_output["best_doppler"],
            matched_filter_output["best_start"],
            config
        )
    else:
        start_IPP_trail = []
        end_IPP_trail = []

    mets_found = len(start_IPP)
    # if

    # Event search thing here
    # Cluster thing here

    return events


def remove_indices(ignore_indices, mets_found, start_IPP, end_IPP, config):
    remove_indices = []
    if len(ignore_indices) < 1 or mets_found < 1:
        return start_IPP, end_IPP
    for index_1 in range(len(ignore_indices[0])):
        for index_2 in range(0, mets_found):
            if (start_IPP[index_2] >= ignore_indices[0][index_1]
                    and end_IPP[index_2] <= ignore_indices[1][index_1]):
                remove_indices.append(index_2)
    return [5], [6]

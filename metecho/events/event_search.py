import numpy as np
import copy
from . import conf
from metecho.generalized_matched_filter import xcorr, signal_model
from metecho.noise import calc_noise


def elements(array):
    return array.ndim and array.size


def mergeDict(dict1, dict2, axis=None):
    dict3 = {**dict1, **dict2}
    for key, value in dict3.items():
        if key in dict1 and dict2:
            if type(value) == np.ndarray and value.ndim > 1:
                dict3[key] = np.concatenate((value, dict1[key]), axis=axis)
            elif type(value) == np.ndarray:
                dict3[key] = np.concatenate((value, dict1[key]))
            else:
                dict3[key] = [value, dict1[key]]
    return dict3


def search(raw_data, config, matched_filter_output, search_function_objects, signal, filters=None):
    events = []
    matched_filter_output["doppler_coherrence"] = 0
    matched_filter_output["start_coherrence"] = 0
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

        matched_filter_output["filter_indices"] = matched_filter_output["tot_pow"] < matched_filter_output["gauss_noise"]["mean"] + \
            config.getfloat("General", "pow_std_est") * matched_filter_output["gauss_noise"]["std_dev"]

        if not np.any(matched_filter_output["filter_indices"]):
            return events

        matched_filter_output["best_peak_filt"] = matched_filter_output["best_peak"][matched_filter_output["filter_indices"]]
        matched_filter_output["tot_pow_filt"] = matched_filter_output["tot_pow"][matched_filter_output["filter_indices"]]

    if (matched_filter_output["doppler_coherrence"] < config.getfloat("General", "dop_std_coherr_percent")
            or matched_filter_output["start_coherrence"] < config.getfloat("General", "start_std_coherr_percent")):
        for searcher in search_function_objects:
            events.append(searcher.search(matched_filter_output, raw_data, config))
        # Event search thing here
        # Cluster thing here
    return events

import numpy as np
import copy
from . import conf
from metecho.generalized_matched_filter import xcorr, signal_model


def mergeDict(dict1, dict2, axis=None):
    dict3 = {**dict1, **dict2}
    for key, value in dict3.items():
        if key in dict1 and dict2:
            if type(value) == np.ndarray:
                # print(value.shape)
                # print(dict1[key].shape)
                dict3[key] = np.concatenate((value, dict1[key]), axis=axis)
            else:
                dict3[key] = [value, dict1[key]]
    return dict3


def search(raw_data, config, matched_filter_output, search_function_objects):
    events = []
    # Barker thing here
    if matched_filter_output is not None:
        raw_data_pulse_length = raw_data.data.shape[raw_data.axis["pulses"]]
        """
        if matched_filter_output["sample_length"] < raw_data_sample_length:
            sample_diff = raw_data_sample_length - matched_filter_output["sample_length"]
            temp_raw_data = copy.deepcopy(raw_data)
            temp_raw_data.data = temp_raw_data.data[
                :,
                matched_filter_output["sample_length"]:,
                :matched_filter_output["pulse_length"]
            ]
            print(temp_raw_data.data.shape)
            
            signal = signal_model.barker_code_13(sample_diff, 2)
            append_data = xcorr.xcorr_echo_search(
                temp_raw_data,
                config.getint("General", "dop_min_freq"),
                config.getint("General", "dop_max_freq"),
                config.getint("General", "dop_step_size"),
                signal
            )
            matched_filter_output = mergeDict(matched_filter_output, append_data, axis=0)
            matched_filter_output["pulse_length"] = matched_filter_output["pulse_length"][0]
            matched_filter_output["sample_length"] = np.sum(matched_filter_output["sample_length"])
        """
        if matched_filter_output["pulse_length"] < raw_data_pulse_length:
            temp_raw_data = copy.deepcopy(raw_data)
            temp_raw_data.data = temp_raw_data.data[
                :,
                :,
                matched_filter_output["pulse_length"]:
            ]
            signal = signal_model.barker_code_13(raw_data_pulse_length, 2)
            append_data = xcorr.xcorr_echo_search(
                temp_raw_data,
                config.getint("General", "dop_min_freq"),
                config.getint("General", "dop_max_freq"),
                config.getint("General", "dop_step_size"),
                signal
            )
            matched_filter_output = mergeDict(matched_filter_output, append_data, axis=1)
            matched_filter_output["sample_length"] = matched_filter_output["sample_length"][0]
            matched_filter_output["pulse_length"] = np.sum(matched_filter_output["pulse_length"])
    else:
        matched_filter_output = {"powmaxall": np.zeros(100, dtype=np.complex128)}
    for searcher in search_function_objects:
        events.append(searcher.search(matched_filter_output))
        # Event search thing here
    # Cluster thing here
    return events

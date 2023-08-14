import numpy as np
import copy
import math
from datetime import datetime
from . import event_select, search_objects, event
from metecho.generalized_matched_filter import xcorr
from metecho.noise import calc_noise
import logging
import matplotlib.pyplot as plt

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


def search(raw_data,
           config,
           matched_filter_output,
           signal,
           filters=None,
           search_function_objects=None,
           plot=True,
           save_as_image=False,
           save_matched_filter_output=False,
           save_location=""
           ):
    """
    Searches for potential events from the filtered data and establishes if they can be analyzed further.
    Plots them as well by default. Search algorithm adapted from [1]_.

    Parameters
    ----------
    raw_data : metecho.RawData
        The raw radar data to search for head echoes in
    config : configparser.ConfigParser
        The search configuration
    matched_filter_output : dict
        Output data from the matched filter analysis
    signal : np.ndarray
        `shape=(samples, pulses)` model if the transmitted signals.

    Returns
    -------
    float
        Negative of the generalized match function absolute value.

    .. [1] Kastinen, Daniel et. al

    """
    # Initiates variables so they're never empty when used
    events = []
    non_head = []
    best_data = []
    gauss_noise = {}

    # Checks that we got input
    if raw_data is not None:
        # Checks if we got partial input
        if matched_filter_output is not None:
            if "best_doppler" not in matched_filter_output:
                matched_filter_output["best_doppler"] = []
            if "best_start" not in matched_filter_output:
                matched_filter_output["best_start"] = []
            # Calculates how much is already done and xcorrs the rest
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
        # If not, xcorr everything
        else:
            matched_filter_output = xcorr.xcorr_echo_search(
                raw_data,
                config.getint("General", "dop_min_freq"),
                config.getint("General", "dop_max_freq"),
                config.getint("General", "dop_step_size"),
                signal
            )
        # Calculates some variables for later use
        matched_filter_output["tot_pow"] = np.squeeze(np.sum(np.square(np.abs(np.sum(raw_data.data, 0))), 0))

        matched_filter_output["doppler_window"] = np.lib.stride_tricks.sliding_window_view(
            matched_filter_output["best_doppler"],
            config.getint("General", "MOVE_STD_WINDOW")
        )
        matched_filter_output["start_window"] = np.lib.stride_tricks.sliding_window_view(
            matched_filter_output["best_start"],
            config.getint("General", "MOVE_STD_WINDOW")
        )

        matched_filter_output["doppler_std"] = np.std(matched_filter_output["doppler_window"], axis=1)
        matched_filter_output["start_std"] = np.std(matched_filter_output["start_window"], axis=1)

        matched_filter_output["doppler_coherrence"] = np.sum(
            matched_filter_output["doppler_std"] < config.getfloat(
                "General", "dop_std_coherr") / len(matched_filter_output["doppler_std"])
        )
        matched_filter_output["start_coherrence"] = np.sum(
            (matched_filter_output["start_std"]
                < (config.getfloat("General", "start_std_coherr")
                   / len(matched_filter_output["start_std"])))
        )

        coherent_signal_indicator = np.argwhere(matched_filter_output["best_peak"]
                                                > config.getfloat("General", "xcorr_noise_limit")).flatten()

        no_coherent_signal_indicator = np.argwhere(
            matched_filter_output["best_peak"] < config.getfloat("General", "xcorr_noise_limit")
        ).flatten()

        tot_pow_mean = np.mean(matched_filter_output["tot_pow"][no_coherent_signal_indicator])
        tot_pow_std = np.std(matched_filter_output["tot_pow"][no_coherent_signal_indicator])

        removed_coherent_signal_indicator = np.delete(
            raw_data.data, coherent_signal_indicator, axis=raw_data.axis["pulse"])

        matched_filter_output["gauss_noise"] = calc_noise.CalculateGaussianNoise().calc(
            removed_coherent_signal_indicator,
            raw_data.axis["channel"]
        )

        matched_filter_output["filter_indices"] = (matched_filter_output["tot_pow"]
                                                   < (tot_pow_mean
                                                      + config.getfloat("General", "pow_std_est")
                                                      * tot_pow_std))

        if not np.any(matched_filter_output["filter_indices"]):
            logger.warning("No noise found, returning...")
            return [], [], [], []

        matched_filter_output["best_peak_filt"] = \
            matched_filter_output["best_peak"][matched_filter_output["filter_indices"]]
        matched_filter_output["tot_pow_filt"] = \
            matched_filter_output["tot_pow"][matched_filter_output["filter_indices"]]

        best_data.append(matched_filter_output["best_peak"])
        best_data.append(matched_filter_output["best_doppler"])
        best_data.append(matched_filter_output["best_start"])

        gauss_noise = matched_filter_output["gauss_noise"]

    find_indices = None
    find_indices_req = None
    find_indices_trail = None
    # Checks if we got any search functions, otherwise defaults
    if search_function_objects is None:
        search_function_objects = search_objects.get_defaults()
    # Iterates over all search functions and applies them to each respective array
    # depending on their attributes. The Required attribute means that *all* search
    # functions must be true on those locations to count. "Required_trails" means that only
    # these are required to check for meteor trails. For all others, there must be
    # a total of CRITERIA_N matches for it to count as a found event.
    for searcher in search_function_objects:
        curr = searcher.search(matched_filter_output, raw_data, config)
        # Ugly error fix, make prettier version later
        if curr.shape != (512, ):
            curr = np.resize(curr, (512,))
        if searcher.required:
            if find_indices_req is not None:
                find_indices_req = np.logical_and(curr, find_indices_req)
            else:
                find_indices_req = curr
        if searcher.required_trails:
            if find_indices_trail is not None:
                find_indices_trail = np.logical_and(curr, find_indices_trail)
            else:
                find_indices_trail = curr
        else:
            if find_indices is not None:
                find_indices = curr * 1 + find_indices * 1
            else:
                find_indices = curr * 1

    if find_indices_req is not None:
        found_indices = np.argwhere(np.array(find_indices >= config.getint("General", "CRITERIA_N")))
    else:
        found_indices = np.argwhere(np.logical_and(find_indices_req, find_indices
                                                   >= config.getint("General", "CRITERIA_N")))

    # Clusters the events. giving start and end points in a 2-d array.
    start_IPP, end_IPP = event_select.cluster(
        found_indices,
        matched_filter_output["best_doppler"],
        matched_filter_output["best_start"],
        config
    )

    # Checks if there are any trails and tries to cluster these as well
    if np.any(find_indices_trail):
        found_indices_trail = np.argwhere(
            np.logical_and(
                np.logical_not(find_indices_trail),
                find_indices >= config.getint("General", "CRITERIA_N")
            )
        )
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

    # If the "ignore_indices" variable is set in matched_filter_output,
    # it removes these values from the start and end IPPs (if there are
    # matches there)
    if "ignore_indices" in matched_filter_output:
        start_IPP, end_IPP = remove_indices(config["General"]["ignore_indices"],
                                            mets_found,
                                            start_IPP,
                                            end_IPP,
                                            config
                                            )
    # In case it was removed by "remove_indices"
    mets_found = len(start_IPP)

    # If multiple meteors are found, adjust them to not overlap as much
    if mets_found > 1:
        for x in range(0, mets_found - 1):
            dIPP = end_IPP[x] - start_IPP[x + 1]
            if dIPP > config.getint("General", "event_max_overlap"):
                contr_IPP = math.floor(0.5 * (dIPP - config.getint("General", "event_max_overlap")))
                end_IPP[x] = end_IPP[x] - contr_IPP
                start_IPP[x + 1] = start_IPP[x + 1] + contr_IPP

    # Create trail events
    if start_IPP_trail:
        for x in range(0, len(start_IPP_trail)):
            FND_INDS = [i for i in found_indices_trail.flatten()
                        if i > start_IPP_trail[x] and i < end_IPP_trail[x]]
            
            ev_date = raw_data.meta.get('date', None)
            raw_date = ev_date

            if 'T_ipp' in raw_data.meta and ev_date is not None:
                offset_ns = int(1e9*start_IPP_trail[x]*raw_data.meta['T_ipp'])
                ev_date += np.timedelta64(offset_ns, 'ns')

            ev = event.Event(
                start_IPP_trail[x], 
                end_IPP_trail[x], 
                [raw_data.path], 
                ev_date, 
                files_start_date = [raw_date],
                found_indices = FND_INDS,
                event_search_executed = datetime.now(),
                event_search_config = config,
                type = 'meteor:trail',
                noise = matched_filter_output["gauss_noise"],
            )
            if "date" in raw_data.meta:
                ev.files_start_date = [raw_data.meta["date"]]
            if save_matched_filter_output:
                ev.search_data = matched_filter_output

            non_head.append(ev)

    # Create head events
    if mets_found > 0:
        for x in range(0, mets_found):
            FND_INDS = [i for i in found_indices.flatten() if i > start_IPP[x] and i < end_IPP[x]]

            ev_date = raw_data.meta.get('date', None)
            raw_date = ev_date

            if 'T_ipp' in raw_data.meta and ev_date is not None:
                offset_ns = int(1e9*start_IPP[x]*raw_data.meta['T_ipp'])
                ev_date += np.timedelta64(offset_ns, 'ns')

            ev = event.Event(
                start_IPP[x], 
                end_IPP[x], 
                [raw_data.path], 
                ev_date, 
                files_start_date = [raw_date],
                found_indices = FND_INDS,
                event_search_executed = datetime.now(),
                event_search_config = config,
                type = 'meteor:head',
                noise = matched_filter_output["gauss_noise"],
            )
            if save_matched_filter_output:
                ev.search_data = matched_filter_output

            events.append(ev)

    # Plots the data in a way which makes it easier to see what's happening.
    if plot or save_as_image:

        # Create x-axis for plots
        PULSE_V = np.arange(raw_data.data.shape[raw_data.axis['pulse']])
        # Create a 3x3 grid that's 16 times 9 inches big
        fig, axs = plt.subplots(3, 3)
        fig.set_size_inches(16, 9)

        # Create a 2 by 1 plot and replace axis 2 and 3 with it.
        long_plot = axs[1, 0].get_gridspec()
        for ax in axs[0, 1:]:
            ax.remove()
        long_plot_ax = fig.add_subplot(long_plot[0, 1:])

        custom_fontdict = {
            'size': 18,
            'weight': 'bold',
        }
        # Create title
        event_save = f'Events saved: {mets_found}' if mets_found > 0 else 'No events found'
        fig.suptitle(f'{raw_data.path.name}, Matches={len(found_indices)}, \
Non-transient coherent detection ({matched_filter_output["doppler_coherrence"]}, \
{matched_filter_output["start_coherrence"]}), \
{event_save}',
                     fontdict=custom_fontdict,
                     wrap=True,
                     )

        plot_highlight_match(axs[0, 0], found_indices,
                             np.abs(matched_filter_output["best_peak"]), "IPP [1]", "Xcorr Match", config)

        summed = raw_data.data
        remove_axis = copy.deepcopy(raw_data.DATA_AXIS)
        remove_axis.remove('sample')
        remove_axis.remove('pulse')
        for axis in remove_axis:
            if raw_data.axis[axis] is not None:
                summed = np.sum(summed, axis=raw_data.axis[axis])

        powsum = np.abs(summed)**2

        pmesh = long_plot_ax.pcolormesh(powsum)
        long_plot_ax.set_xlabel('IPP [1]')
        long_plot_ax.set_ylabel('Sample [1]')

        cbar = plt.colorbar(pmesh)
        cbar.set_label('Power [1]')

        plot_highlight_match(axs[1, 0], found_indices, matched_filter_output["tot_pow"],
                             "IPP [1]", "Total Power", config)
        plot_highlight_match(axs[1, 1], found_indices, matched_filter_output["start_std"],
                             "IPP [1]", "Range moving STD", config)
        plot_highlight_match(axs[1, 2], found_indices, matched_filter_output["doppler_std"],
                             "IPP [1]", "Doppler shift moving STD", config)

        criteria_mat = find_indices if find_indices_req is not None else find_indices + 1 * find_indices_req
        axs[2, 0].plot(PULSE_V, criteria_mat)
        axs[2, 0].set_xlabel("IPP [1]")
        axs[2, 0].set_ylabel("Event Criteria met")

        plot_highlight_match(axs[2, 1], found_indices,
                             matched_filter_output["best_start"], "IPP [1]", "Range start", config)
        plot_highlight_match(axs[2, 2, ], found_indices,
                             matched_filter_output["best_doppler"], "IPP [1]", "Doppler shift match", config)

        colors = plt.cm.rainbow(np.linspace(0, 1, len(start_IPP)))

        for rows in axs:
            for ax in rows:
                for start, stop, color in zip(start_IPP, end_IPP, colors):
                    ax.axvspan(start, stop, facecolor=color, alpha=0.4)

        for start, stop, color in zip(start_IPP, end_IPP, colors):
            long_plot_ax.axvspan(start, stop, facecolor=color, alpha=0.4)

        # fig.tight_layout()
        if save_as_image and save_location != "":
            if "." in str(save_location):
                save_location = save_location.parent
            if not save_location.is_dir():
                save_location.mkdir(parents=True)
            save_location = save_location / (raw_data.path.name + ".png")
            fig.savefig(save_location)

        if plot:
            plt.show()
        else:
            plt.close(fig)

    return events, non_head, best_data, gauss_noise


def plot_highlight_match(ax, matches, data, xlabel, ylabel, config):
    """
    Takes a set a of data and plots it on a graph, then marks all the points with matches.
    """
    if data.shape != (512,):
        data = np.resize(data, (512,))
    data_filt = np.zeros(len(data), dtype=bool)
    data_xaxis = np.arange(len(data))
    data_filt[matches] = True

    color_filter = []
    for ind in data_filt:
        if ind:
            color_filter.append(config["General"]["match_found"])
        else:
            color_filter.append(config["General"]["match_not_found"])
    ax.plot(data_xaxis, data)
    ax.scatter(data_xaxis, data, marker=".", c=color_filter)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)


def remove_indices(ignore_indices, mets_found, start_IPP, end_IPP, config):
    """
    Remoces indices where there's overlap
    """
    remove_indices = []
    if len(ignore_indices) < 1 or mets_found < 1:
        return start_IPP, end_IPP
    for index_1 in range(len(ignore_indices[0])):
        for index_2 in range(0, mets_found):
            if (start_IPP[index_2] >= ignore_indices[0][index_1]
                    and end_IPP[index_2] <= ignore_indices[1][index_1]):
                remove_indices.append(index_2)
            elif ((ignore_indices[0][index_1] - start_IPP[index_2])
                  > config.getint("General", "allow_analysis_overlap")
                  and end_IPP(index_2)
                  >= ignore_indices[1, index_1]
                  and start_IPP[index_2]
                  >= ignore_indices[0, index_1]):
                remove_indices.append(index_2)
            elif ((end_IPP[index_2] - ignore_indices[0][index_1])
                  > config.getint("General", "allow_analysis_overlap")
                  and start_IPP[index_2]
                  <= ignore_indices[0][index_1]
                  and end_IPP[index_2]
                  <= ignore_indices[1][index_1]):
                remove_indices.append(index_2)
    for remove_index in remove_indices[::-1]:
        del start_IPP[remove_index]
        del end_IPP[remove_index]
    return start_IPP, end_IPP

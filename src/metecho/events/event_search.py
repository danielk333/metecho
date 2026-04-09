import datetime as dt
import logging
import math
from configparser import ConfigParser
from pathlib import Path
from typing import Optional

import hardtarget
import numpy as np
from radardef.components import DataLoader

from metecho.events.types import Echo, Event, Events
from metecho.noise import calc_noise
from metecho.plot import plot_events

from . import event_select, search_objects

logger = logging.getLogger(__name__)


def event_search(
    data: DataLoader,
    config: ConfigParser,
    start_time: Optional[np.datetime64 | int | str | dt.datetime] = None,
    end_time: Optional[np.datetime64 | int | str | dt.datetime] = None,
    plot: bool = False,
    save_as_image: bool = False,
    save_location: Optional[str | Path] = None,
) -> Events:
    echo = echo_search(data, config, start_time, end_time)
    events = locate_events(data, echo, config)
    if plot:
        plot_events(data, config, echo, events, save_as_image, save_location)

    return events


def echo_search(
    data: DataLoader,
    config: ConfigParser,
    start_time: Optional[np.datetime64 | int | str | dt.datetime] = None,
    end_time: Optional[np.datetime64 | int | str | dt.datetime] = None,
) -> Echo:
    """
    Runs a echo search and derives from this data needed for further analysis.

    Args:
        data: Dataloader for the data to analyse.
        config : The search configuration

    Returns:
        Collected analysis from the echo search

    """

    # Run echo search
    results = hardtarget.echo_search(
        data=data,
        start_time=start_time,
        end_time=end_time,
        config={
            "n_ipp": 1,
            "samp_offset": 0,
            "doppler_freq_min": config.getint("General", "dop_min_freq"),
            "doppler_freq_max": config.getint("General", "dop_max_freq"),
            "doppler_freq_step": config.getint("General", "dop_step_size"),
        },
        progress=True,
    )
    # Gather data from echo search
    res_out, exp, cfg, pro = hardtarget.stack_analysed_data(results["data"])

    # Moving standard deviation of doppler
    best_doppler = np.concatenate(
        (res_out.best_doppler, np.zeros((config.getint("General", "MOVE_STD_WINDOW") - 1,)))
    )  # zero padded to make sure we get the same amount of windows as ipp's
    doppler_window = np.lib.stride_tricks.sliding_window_view(
        best_doppler,
        config.getint("General", "MOVE_STD_WINDOW"),
    )
    doppler_std = np.std(doppler_window, axis=1)

    # Moving standard deviation of range (max power index per ipp)
    max_pow_index = np.concatenate(
        (res_out.max_pow_ind, np.zeros((config.getint("General", "MOVE_STD_WINDOW") - 1,)))
    )  # zero padded to make sure we get the same amount of windows as ipp's
    start_window = np.lib.stride_tricks.sliding_window_view(
        max_pow_index,
        config.getint("General", "MOVE_STD_WINDOW"),
    )
    start_std = np.std(start_window, axis=1)

    # Coherrence
    doppler_coherrence = np.sum(doppler_std < config.getfloat("General", "dop_std_coherr") / len(doppler_std))
    start_coherrence = np.sum((start_std < (config.getfloat("General", "start_std_coherr") / len(start_std))))

    # Gaussian noise
    _coherent_signal_indicator = np.argwhere(
        res_out.max_peak > config.getfloat("General", "xcorr_noise_limit")
    ).flatten()
    _no_coherent_signal_indicator = np.argwhere(
        res_out.max_peak < config.getfloat("General", "xcorr_noise_limit")
    ).flatten()
    _tot_pow_mean = np.mean(res_out.ipps_pow[_no_coherent_signal_indicator])
    _tot_pow_std = np.std(res_out.ipps_pow[_no_coherent_signal_indicator])
    _filter_indices = res_out.ipps_pow < (
        _tot_pow_mean + config.getfloat("General", "pow_std_est") * _tot_pow_std
    )
    start_samp, end_samp = data.bounds(data.experiment.rx_channels[0])
    raw_data = np.zeros((len(data.channels), end_samp - start_samp), dtype=np.complex128)
    for i, channel in enumerate(data.channels):
        raw_data[i, :] = data.read(channel)
    _removed_coherent_signal_indicator = np.delete(raw_data, _coherent_signal_indicator, axis=1)
    gauss_noise = calc_noise.calc_gaussian_noise(_removed_coherent_signal_indicator)

    return Echo(
        tot_pow=res_out.ipps_pow,
        max_pow=res_out.max_pow,
        max_pow_norm=res_out.max_pow_norm,
        max_peak=res_out.max_peak,
        max_pow_ind=res_out.max_pow_ind,
        best_doppler=res_out.best_doppler,
        tot_pow_filt=res_out.ipps_pow[_filter_indices],
        best_peak_filt=res_out.max_peak[_filter_indices],
        gauss_noise=gauss_noise,
        start_std=start_std,
        start_coherrence=start_coherrence,
        doppler_std=doppler_std,
        doppler_coherrence=doppler_coherrence,
    )


def locate_events(
    data: DataLoader,
    echo: Echo,
    config: ConfigParser,
    search_function_objects: list[search_objects.SearchObject] = search_objects.get_defaults(),
) -> Events:
    """
    Searches for potential events from the filtered data and establishes if they can be analyzed further.
    Search algorithm adapted from [1]_.

    Args:
        data: Dataloader for the data to analyse.
        echo: The output from a echo search on the data.
        config : The search configuration

    Returns:
        Events found....

    .. [1] Kastinen, Daniel et. al
    """

    # Start and end of measurement file
    measurement_start_us, _ = data.epoch_bounds

    # Meteor filter - All search functions with required must be fullfilled for the index to classify as a meteor
    meteor_filter = np.all(
        [searcher.search(echo, config) for searcher in search_function_objects if searcher.required],
        axis=0,
    )
    # Trail filter - All search functions with trail must be fullfilled to classify as a meteor trail
    meteor_trail_filter = np.all(
        [searcher.search(echo, config) for searcher in search_function_objects if searcher.required_trails],
        axis=0,
    )
    # Amount of searchers fullfilled - Count amount of matches, can be used to filter out events with N criteras fullfilled.
    detection_per_index = np.sum(
        [
            searcher.search(echo, config).astype(int)
            for searcher in search_function_objects
            if not searcher.required_trails
        ],
        axis=0,
    )

    # Extract indicies with meteor trails.
    meteor_trail_indices = np.argwhere(
        np.logical_and(
            np.logical_not(meteor_trail_filter),
            detection_per_index >= config.getint("General", "CRITERIA_N"),
        )
    ).flatten()
    # Cluster the start and end point of each trail.
    meteor_trail_span = event_select.cluster(
        meteor_trail_indices,
        echo.best_doppler,
        echo.max_pow_ind,
        config,
    )

    # Amount of trail events present in the measurement,
    trails_found = len(meteor_trail_span)

    # Create trail events
    trail_events: list[Event] = []
    for x in range(0, trails_found):
        event_indices = meteor_trail_indices[
            np.logical_and(
                meteor_trail_indices > meteor_trail_span[x, 0], meteor_trail_indices < meteor_trail_span[x, 1]
            )
        ]
        event_offset_us = int(meteor_trail_span[x, 0] * data.experiment.t_ipp_usec)
        ev_date = np.datetime64(int(measurement_start_us + event_offset_us), "us")
        ev = Event(
            start_ipp=meteor_trail_span[x, 0],
            end_ipp=meteor_trail_span[x, 1],
            event_indices=event_indices,
            files=[data.path],
            event_date=ev_date,
            files_start_date_us=[int(measurement_start_us)],
            event_search_executed=np.datetime64(dt.datetime.now()),
            event_search_config=config,
            type="meteor:trail",
            noise=echo.gauss_noise,
        )

        trail_events.append(ev)

    # Extract indicies with meteor events.
    if np.any(detection_per_index):
        meteor_indices = np.argwhere(detection_per_index >= config.getint("General", "CRITERIA_N")).flatten()
    else:
        meteor_indices = np.argwhere(
            np.logical_and(
                meteor_filter, detection_per_index >= config.getint("General", "CRITERIA_N")
            ).flatten()
        )
    # Cluster the start and end point of each event.
    meteor_span = event_select.cluster(
        meteor_indices,
        echo.best_doppler,
        echo.max_pow_ind,
        config,
    )

    # Amount of meteors present in the measurement.
    mets_found = len(meteor_span)

    # If multiple meteors are found, adjust them to not overlap as much
    if mets_found > 1:
        for x in range(0, mets_found - 1):
            event_overlap = meteor_span[x, 1] - meteor_span[x + 1, 0]
            if event_overlap > config.getint("General", "event_max_overlap"):
                contr_IPP = math.floor(0.5 * (event_overlap - config.getint("General", "event_max_overlap")))
                meteor_span[x, 1] -= contr_IPP
                meteor_span[x + 1, 0] += contr_IPP

    # Create head events
    meteor_events: list[Event] = []
    for x in range(0, mets_found):
        event_indices = meteor_indices[
            np.logical_and(meteor_indices > meteor_span[x, 0], meteor_indices < meteor_span[x, 1])
        ]
        event_offset_us = int(meteor_span[x, 0] * data.experiment.t_ipp_usec)
        ev_date = np.datetime64(int(measurement_start_us + event_offset_us), "us")

        ev = Event(
            start_ipp=meteor_span[x, 0],
            end_ipp=meteor_span[x, 1],
            event_indices=event_indices,
            files=[data.path],
            event_date=ev_date,
            files_start_date_us=[int(measurement_start_us)],
            event_search_executed=np.datetime64(dt.datetime.now()),
            event_search_config=config,
            type="meteor:head",
            noise=echo.gauss_noise,
        )

        meteor_events.append(ev)

    return Events(
        meteors=meteor_events,
        meteor_indicies=meteor_indices,
        trails=trail_events,
        trail_indicies=meteor_indices,
        detection_per_index=detection_per_index,
    )


"""
TODO: Check where this was used
def remove_indices(ignore_indices, mets_found, start_IPP, end_IPP, config):

    #Remoces indices where there's overlap

    remove_indices = []
    if len(ignore_indices) < 1 or mets_found < 1:
        return start_IPP, end_IPP
    for index_1 in range(len(ignore_indices[0])):
        for index_2 in range(0, mets_found):
            if (
                start_IPP[index_2] >= ignore_indices[0][index_1]
                and end_IPP[index_2] <= ignore_indices[1][index_1]
            ):
                remove_indices.append(index_2)
            elif (
                (ignore_indices[0][index_1] - start_IPP[index_2])
                > config.getint("General", "allow_analysis_overlap")
                and end_IPP(index_2) >= ignore_indices[1, index_1]
                and start_IPP[index_2] >= ignore_indices[0, index_1]
            ):
                remove_indices.append(index_2)
            elif (
                (end_IPP[index_2] - ignore_indices[0][index_1])
                > config.getint("General", "allow_analysis_overlap")
                and start_IPP[index_2] <= ignore_indices[0][index_1]
                and end_IPP[index_2] <= ignore_indices[1][index_1]
            ):
                remove_indices.append(index_2)
    for remove_index in remove_indices[::-1]:
        del start_IPP[remove_index]
        del end_IPP[remove_index]
    return start_IPP, end_IPP
"""

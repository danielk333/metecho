import datetime as dt
import logging
import math
from pathlib import Path
from typing import Optional

import hardtarget
import numpy as np
from hardtarget.echo_search.types import EchoSearchCfgParams, EchoSearchOutArgs, EchoSearchProParams
from radardef.components import DataLoader
from radardef.types.types import ExpDef

from metecho.events.conf import generate_default_event_search_config
from metecho.events.types import Echo, Event, Events, EventSearchConfig
from metecho.noise import calc_noise
from metecho.tools.mpi_decorators import CommMock, CommObject

from . import event_select, search_objects

logger = logging.getLogger(__name__)


def event_search_on_old_data(
    data: Path,
    config: EventSearchConfig | None,
) -> tuple[Events, Echo]:
    old_data: tuple[EchoSearchOutArgs, ExpDef, EchoSearchCfgParams, EchoSearchProParams] = list(
        hardtarget.load_analysed_data(data)
    )[0]
    res_out, exp, _, _ = old_data

    if not isinstance(res_out, EchoSearchOutArgs):
        raise TypeError(f"Loaded data from : {data} is not compatible with the echo search")
    # If no config available generate a default one from the experiment definition
    if not config:
        config = generate_default_event_search_config(exp_def=exp)

    echo = echo_post_process(
        echo_search_analysis=res_out,
        config=config,
        exp_def=exp,
    )

    events = locate_events(echo, config, data=data if isinstance(data, DataLoader) else None)

    return events, echo


def event_search(
    data: DataLoader,
    config: EventSearchConfig | None,
    start_time: Optional[np.datetime64 | int | str | dt.datetime] = None,
    end_time: Optional[np.datetime64 | int | str | dt.datetime] = None,
    relative_time: bool = False,
    exp_def: ExpDef | None = None,
    progress: bool = False,
    comm: CommObject = CommMock(),
) -> tuple[Events, Echo]:

    # If no config available generate a default one from the experiment definition
    if not config:
        config = generate_default_event_search_config(exp_def=data.experiment)
    # Run echo search
    results = hardtarget.echo_search(
        data=data,
        start_time=start_time,
        end_time=end_time,
        relative_time=relative_time,
        exp_params=exp_def,
        config={
            "n_ipp": 1,
            "samp_offset": 0,
            "min_range_gate": 81,  # tmp
            "max_range_gate": 140,  # tmp
            "doppler_freq_min": config.dop_min_freq,
            "doppler_freq_max": config.dop_max_freq,
            "doppler_freq_step": config.dop_step_size,
        },
        progress=progress,
        comm=comm,
    )

    # Gather data from echo search
    output: tuple[EchoSearchOutArgs, ExpDef, EchoSearchCfgParams, EchoSearchProParams] = (
        hardtarget.stack_analysed_data(results["data"])
    )
    res_out, exp, _, _ = output

    echo = echo_post_process(
        echo_search_analysis=res_out,
        config=config,
        exp_def=exp,
    )

    events = locate_events(echo, config, data=data if isinstance(data, DataLoader) else None)

    return events, echo


def echo_post_process(
    echo_search_analysis: EchoSearchOutArgs,
    exp_def: ExpDef,
    config: EventSearchConfig,
) -> Echo:
    """
    Post processing of echo search to get data

    Args:
        echo_search_analysis: Output from hardtarget echo search
        exp_def: Experiment definition
        config : The search configuration

    Returns:
        Collected analysis from the echo search

    """

    # Moving standard deviation of doppler
    best_doppler = np.concatenate(
        (echo_search_analysis.best_doppler, np.zeros((config.MOVE_STD_WINDOW - 1,)))
    )  # zero padded to make sure we get the same amount of windows as ipp's
    doppler_window = np.lib.stride_tricks.sliding_window_view(
        best_doppler,
        config.MOVE_STD_WINDOW,
    )
    doppler_std = np.std(doppler_window, axis=1)

    # Moving standard deviation of range (max power index per ipp)
    max_corr_index = np.concatenate(
        (echo_search_analysis.max_corr_ind, np.zeros((config.MOVE_STD_WINDOW - 1,)))
    )  # zero padded to make sure we get the same amount of windows as ipp's
    start_window = np.lib.stride_tricks.sliding_window_view(
        max_corr_index,
        config.MOVE_STD_WINDOW,
    )
    start_std = np.std(start_window, axis=1)

    # Coherrence
    doppler_coherrence = np.sum(doppler_std < config.dop_std_coherr / len(doppler_std))
    start_coherrence = np.sum((start_std < (config.start_std_coherr / len(start_std))))

    # Gaussian noise
    _coherent_signal_indicator = np.argwhere(
        echo_search_analysis.max_corr > config.xcorr_noise_limit
    ).flatten()
    _no_coherent_signal_indicator = np.argwhere(
        echo_search_analysis.max_corr < config.xcorr_noise_limit
    ).flatten()
    _tot_pow_mean = np.mean(echo_search_analysis.tot_pow[_no_coherent_signal_indicator])
    _tot_pow_std = np.std(echo_search_analysis.tot_pow[_no_coherent_signal_indicator])
    _filter_indices = echo_search_analysis.tot_pow < (_tot_pow_mean + config.pow_std_est * _tot_pow_std)

    _mean_filtered = np.delete(echo_search_analysis.mean, _coherent_signal_indicator)
    _std_dev_filtered = np.delete(echo_search_analysis.std_dev, _coherent_signal_indicator)

    gauss_noise = calc_noise.calc_gaussian_noise_from_batches(
        _mean_filtered, _std_dev_filtered, exp_def.ipp_samps
    )

    return Echo(
        exp_def=exp_def,
        tot_pow=echo_search_analysis.tot_pow,
        max_corr=echo_search_analysis.max_corr,
        max_corr_ind=echo_search_analysis.max_corr_ind,
        best_doppler=echo_search_analysis.best_doppler,
        epoch_us=echo_search_analysis.epoch_us,
        tot_pow_filt=echo_search_analysis.tot_pow[_filter_indices],
        best_peak_filt=echo_search_analysis.max_corr[_filter_indices],
        gauss_noise=gauss_noise,
        start_std=start_std,
        start_coherrence=start_coherrence,
        doppler_std=doppler_std,
        doppler_coherrence=doppler_coherrence,
        ipp_offset=int(echo_search_analysis.epoch_us / exp_def.t_ipp_usec),
    )


def locate_events(
    echo: Echo,
    config: EventSearchConfig,
    data: Optional[DataLoader] = None,
    search_function_objects: list[search_objects.SearchObject] = search_objects.get_defaults(),
) -> Events:
    """
    Searches for potential events from the filtered data and establishes if they can be analyzed further.
    Search algorithm adapted from [1]_.

    Args:
        data: Dataloader for the data to analyse.
        echo: The output from a echo search on the data.
        config: The search configuration

    Returns:
        Events found....

    .. [1] Kastinen, Daniel et. al
    """

    # Measurement start
    if data:
        measurement_start_us, _ = data.epoch_bounds
        data_path = data.path
    else:
        measurement_start_us = echo.epoch_us
        data_path = Path("unknwn")

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
            detection_per_index >= config.CRITERIA_N,
        )
    ).flatten()
    # Cluster the start and end point of each trail.
    meteor_trail_span = event_select.cluster(
        meteor_trail_indices,
        echo.best_doppler,
        echo.max_corr_ind,
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
        event_offset_us = int(meteor_trail_span[x, 0] * echo.exp_def.t_ipp_usec)
        ev_date = np.datetime64(int(echo.epoch_us + event_offset_us), "us")
        ev = Event(
            start_ipp=meteor_trail_span[x, 0],
            end_ipp=meteor_trail_span[x, 1],
            event_indices=event_indices,
            file=data_path,
            event_date=ev_date,
            data_start_date_us=int(echo.epoch_us),
            event_search_executed=np.datetime64(dt.datetime.now()),
            type="meteor:trail",
            noise=echo.gauss_noise,
            ipp_offset=echo.ipp_offset,
        )

        trail_events.append(ev)

    # Extract indicies with meteor events.
    if np.any(detection_per_index):
        meteor_indices = np.argwhere(detection_per_index >= config.CRITERIA_N).flatten()
    else:
        meteor_indices = np.argwhere(
            np.logical_and(meteor_filter, detection_per_index >= config.CRITERIA_N)
        ).flatten()

    # Cluster the start and end point of each event.
    meteor_span = event_select.cluster(
        meteor_indices,
        echo.best_doppler,
        echo.max_corr_ind,
        config,
    )

    # Amount of meteors present in the measurement.
    mets_found = len(meteor_span)

    # If multiple meteors are found, adjust them to not overlap as much
    if mets_found > 1:
        for x in range(0, mets_found - 1):
            event_overlap = meteor_span[x, 1] - meteor_span[x + 1, 0]
            if event_overlap > config.event_max_overlap:
                contr_IPP = math.floor(0.5 * (event_overlap - config.event_max_overlap))
                meteor_span[x, 1] -= contr_IPP
                meteor_span[x + 1, 0] += contr_IPP

    # Create head events
    meteor_events: list[Event] = []
    for x in range(0, mets_found):
        event_indices = meteor_indices[
            np.logical_and(meteor_indices > meteor_span[x, 0], meteor_indices < meteor_span[x, 1])
        ]
        event_offset_us = int(meteor_span[x, 0] * echo.exp_def.t_ipp_usec)
        ev_date = np.datetime64(int(measurement_start_us + event_offset_us), "us")

        ev = Event(
            start_ipp=meteor_span[x, 0],
            end_ipp=meteor_span[x, 1],
            event_indices=event_indices,
            file=data_path,
            event_date=ev_date,
            data_start_date_us=int(measurement_start_us),
            event_search_executed=np.datetime64(dt.datetime.now()),
            type="meteor:head",
            noise=echo.gauss_noise,
            ipp_offset=echo.ipp_offset,
        )

        meteor_events.append(ev)

    return Events(
        meteors=meteor_events,
        meteor_indicies=meteor_indices,
        trails=trail_events,
        trail_indicies=meteor_indices,
        detection_per_index=detection_per_index,
        config=config,
        exp_def=echo.exp_def,
        measurement_start_us=int(measurement_start_us),
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

import datetime as dt
import logging
import math
from pathlib import Path
from typing import Optional

import hardtarget
import numpy as np
import numpy.typing as npt
from hardtarget.echo_search.types import EchoSearchCfgParams, EchoSearchOutArgs, EchoSearchProParams
from radardef.components import DataLoader
from radardef.types.types import ExpDef

from metecho.events.conf import extract_event_search_configurations, generate_default_configurations
from metecho.events.types import (
    Echo,
    Event,
    EventCriteriaCfg,
    Events,
    EventSearchCfg,
    EventSelectCfg,
)
from metecho.noise import calc_noise
from metecho.tools.mpi_decorators import CommMock, CommObject

from . import event_select, search_objects

logger = logging.getLogger(__name__)


def event_search(
    data: DataLoader,
    config: Optional[
        tuple[EventSearchCfg, EventCriteriaCfg, EventSelectCfg, EchoSearchCfgParams] | dict | Path
    ],
    start_time: Optional[np.datetime64 | int | str | dt.datetime] = None,
    end_time: Optional[np.datetime64 | int | str | dt.datetime] = None,
    relative_time: bool = False,
    progress: bool = False,
    comm: CommObject = CommMock(),
) -> tuple[Events, Echo]:

    if isinstance(config, tuple):
        event_search_cfg, event_criteria_cfg, event_select_cfg, echo_search_cfg = config
    elif not config:
        event_search_cfg, event_criteria_cfg, event_select_cfg, echo_search_cfg = (
            generate_default_configurations(data.experiment)
        )
    else:
        event_search_cfg, event_criteria_cfg, event_select_cfg, echo_search_cfg = (
            extract_event_search_configurations(config)
        )

    breakpoint()
    # Run echo search
    results = hardtarget.echo_search(
        data=data,
        start_time=start_time,
        end_time=end_time,
        relative_time=relative_time,
        config=echo_search_cfg,
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
        config=event_search_cfg,
        exp_def=exp,
    )

    meteor_indicies, meteor_trail_indicies, detection_per_index = meteor_search(echo, event_criteria_cfg)

    meteor_events = create_event_cluster(
        echo, meteor_indicies, event_select_cfg, data.epoch_bounds[0], overlap_correction=True
    )
    meteor_trail_events = create_event_cluster(
        echo, meteor_trail_indicies, event_select_cfg, data.epoch_bounds[0], overlap_correction=True
    )

    events = Events(
        meteors=meteor_events,
        meteor_indicies=meteor_indicies,
        trails=meteor_trail_events,
        trail_indicies=meteor_trail_indicies,
        detection_per_index=detection_per_index,
        config=event_criteria_cfg,
        exp_def=exp,
        measurement_start_us=data.epoch_bounds[0],
        file=data.path,
    )
    return events, echo


def echo_post_process(
    echo_search_analysis: EchoSearchOutArgs,
    exp_def: ExpDef,
    config: EventSearchCfg,
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
        (echo_search_analysis.best_doppler, np.zeros((config.move_std_window - 1,)))
    )  # zero padded to make sure we get the same amount of windows as ipp's
    doppler_window = np.lib.stride_tricks.sliding_window_view(
        best_doppler,
        config.move_std_window,
    )
    doppler_std = np.std(doppler_window, axis=1)

    # Moving standard deviation of range (max power index per ipp)
    max_corr_index = np.concatenate(
        (echo_search_analysis.max_corr_ind, np.zeros((config.move_std_window - 1,)))
    )  # zero padded to make sure we get the same amount of windows as ipp's
    start_window = np.lib.stride_tricks.sliding_window_view(
        max_corr_index,
        config.move_std_window,
    )
    start_std = np.std(start_window, axis=1)

    # Coherrence
    doppler_coherrence = np.sum(doppler_std < config.dop_std_coherr / len(doppler_std))
    start_coherrence = np.sum((start_std < (config.start_std_coherr / len(start_std))))

    # Gaussian noise
    _coherent_signal_indicator = np.argwhere(
        echo_search_analysis.max_corr >= config.corr_filter_limit
    ).flatten()
    _no_coherent_signal_indicator = np.argwhere(
        echo_search_analysis.max_corr < config.corr_filter_limit
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


def meteor_search(
    echo: Echo,
    config: EventCriteriaCfg,
    search_function_objects: list[search_objects.SearchObject] = search_objects.get_defaults(),
) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.int64], npt.NDArray[np.int64]]:
    """
    Searches the echo output and returns which ipps contains meteors and meteor trails based on the result of the search functions.

    Args:
        echo: Echo output from echo search
        config: Event critiera configuration
        search_function_objects: List of search functions
    Returns:
        Indicies of meteors, meteor trails and number of search functions fullfilled per index

    """

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
            detection_per_index >= config.criteria_n,
        )
    ).flatten()

    # Extract indicies with meteor events.
    if np.any(detection_per_index):
        meteor_indices = np.argwhere(detection_per_index >= config.criteria_n).flatten()
    else:
        meteor_indices = np.argwhere(
            np.logical_and(meteor_filter, detection_per_index >= config.criteria_n)
        ).flatten()

    return meteor_indices, meteor_trail_indices, detection_per_index


def create_event_cluster(
    echo: Echo,
    object_indicies: npt.NDArray,
    config: EventSelectCfg,
    measurement_start_us: int,
    overlap_correction=False,
) -> list[events]:
    # Generic function to cover both metors and trails

    # Cluster the start and end point of each event.
    event_span = event_select.cluster(
        object_indicies,
        echo.best_doppler,
        echo.max_corr_ind,
        config,
    )

    # Amount of meteors present in the measurement.
    events_found = len(event_span)

    # If multiple meteors are found, adjust them to not overlap as much
    if events_found > 1 and overlap_correction:
        for x in range(0, events_found - 1):
            event_overlap = event_span[x, 1] - event_span[x + 1, 0]
            if event_overlap > config.event_max_overlap:
                contr_IPP = math.floor(0.5 * (event_overlap - config.event_max_overlap))
                event_span[x, 1] -= contr_IPP
                event_span[x + 1, 0] += contr_IPP

    # Create head events
    events: list[Event] = []
    for x in range(0, events_found):
        event_indices = object_indicies[
            np.logical_and(object_indicies > event_span[x, 0], object_indicies < event_span[x, 1])
        ]
        event_offset_us = int(event_span[x, 0] * echo.exp_def.t_ipp_usec)
        # TODO: Event offset is relative to the analysis start, thus we need to take echo.epoch_us into consideration?
        ev_date = np.datetime64(int(measurement_start_us + event_offset_us), "us")

        ev = Event(
            start_ipp=event_span[x, 0],
            end_ipp=event_span[x, 1],
            event_indices=event_indices,
            event_date=ev_date,
            event_search_executed=np.datetime64(dt.datetime.now()),
            type="meteor:head",
            noise=echo.gauss_noise,
            ipp_offset=echo.ipp_offset,
        )

        events.append(ev)

    return events


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

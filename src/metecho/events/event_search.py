import datetime as dt
import logging
import math
from pathlib import Path

import hardtarget
import numpy as np
import numpy.typing as npt
from hardtarget.constants import AnalysisMethod, Impl
from hardtarget.echo_search.types import EchoSearchCfgParams, EchoSearchOutArgs, EchoSearchProParams
from radardef.components import DataLoader
from radardef.tools.mpi_tools import CommBar, CommMock, CommObject
from radardef.types.types import ExpDef

from metecho.data_handling.store_data import store_events, store_noise
from metecho.events.conf import extract_event_search_configurations, generate_default_configurations
from metecho.events.constants import MeteorType
from metecho.events.types import (
    Echo,
    Event,
    EventCriteriaCfg,
    Events,
    EventSearchCfg,
    EventSelectCfg,
)
from metecho.noise import calc_gaussian_noise_batch_chunks
from metecho.noise.types import GaussianNoiseChunks

from . import event_select, search_objects

logger = logging.getLogger(__name__)


def event_search(
    data: DataLoader,
    config: tuple[EventSearchCfg, EventCriteriaCfg, EventSelectCfg, EchoSearchCfgParams]
    | dict
    | Path
    | None = None,
    start_time: np.datetime64 | int | str | dt.datetime | None = None,
    end_time: np.datetime64 | int | str | dt.datetime | None = None,
    relative_time: bool = False,
    output: str | Path | None = None,
    implementation: Impl | None = None,
    progress: bool | CommBar = False,
    comm: CommObject = CommMock(),
) -> tuple[Events, Echo, GaussianNoiseChunks]:
    """
    Runs a echo search to identify meteor events.

    Args:
        data: Data loader to the data that shall be analysed.
        config (optional): Path to a configuration file, a dict with the config parameters or a
                           tuple containing the event search, criteria, select and echo search
                           cfg. If not set the a configuration will automatically be generated
                           based on the experiment parameters (from the dataloader).
        start_time (optional): Start time of analysis, datetime object, date string or seconds since epoch.
        end_time (optional): End time of analysis,datetime object, date string or seconds since epoch.
        relative_time (optional): If to use relative time, start and end time must be specified in int or float then.
        output (optional): Output directory for the analysed files, if None no files will be saved.
                           Path will be output/YYYY-MM-DD/HH-00-00.
        implementation (optional): Implementation of the method to be used during the echo search (Numpy/Cuda/C),
                                will override any implementation defined in the config params.
        progress (optional): If a progress bar should be visualized.
        comm (optional): Mpi communication object if analysis is expected to run on MPI or a specific Comm object.
    Returns:
        Detected Events, Echo data and the Gaussian Noise
    """

    if comm.rank == 0:
        if isinstance(config, tuple):
            event_search_cfg, event_criteria_cfg, event_select_cfg, echo_search_cfg = config
        elif not config:
            event_search_cfg, event_criteria_cfg, event_select_cfg, echo_search_cfg = (
                generate_default_configurations(data.exp_def)
            )
        else:
            event_search_cfg, event_criteria_cfg, event_select_cfg, echo_search_cfg = (
                extract_event_search_configurations(config)
            )
    else:
        event_search_cfg = event_criteria_cfg = event_select_cfg = echo_search_cfg = None  # type: ignore[assignment]

    event_search_cfg = comm.bcast(event_search_cfg, root=0)
    event_criteria_cfg = comm.bcast(event_criteria_cfg, root=0)
    event_select_cfg = comm.bcast(event_select_cfg, root=0)
    echo_search_cfg = comm.bcast(echo_search_cfg, root=0)

    # Run echo search
    results = hardtarget.echo_search(
        data=data,
        start_time=start_time,
        end_time=end_time,
        relative_time=relative_time,
        config=echo_search_cfg,
        output=output,
        sub_directory="echo",
        implementation=implementation,
        progress=progress,
        comm=comm,
    )
    comm.barrier()

    if comm.rank == 0:
        if output:
            # No chunksize so will ju be one object
            echo_result: tuple[EchoSearchOutArgs, ExpDef, EchoSearchCfgParams, EchoSearchProParams] = (
                hardtarget.load_analysed_data(results["file_dir"], method=AnalysisMethod.echo_search)
            )
            res_out, exp, _, _ = echo_result
        else:
            # Gather data from echo search
            echo_result = hardtarget.stack_analysed_data(results["data"])
            res_out, exp, _, _ = echo_result

        echo = echo_post_process(
            echo_search_analysis=res_out,
            config=event_search_cfg,
            exp_def=exp,
        )

        noise = calculate_noise(
            echo_search_analysis=res_out,
            chunk_size=event_search_cfg.noise_chunk_size,
            exp_def=exp,
            progress=progress,
        )

        if output:
            store_noise(noise, Path(output).resolve())

        # as it is unknown how many meteors is available we add a buffering bar, not blocking due to only running on one rank
        if progress:
            prog = CommBar(
                tot=None,
                desc="Searching for Events",
                transient=False,
                multi_process_bar=False,
                parent_progress=progress if isinstance(progress, CommBar) else None,
            )
        else:
            prog = None

        meteor_indicies, meteor_trail_indicies, detection_per_index = meteor_search(echo, event_criteria_cfg)

        meteor_events = create_event_cluster(
            echo,
            meteor_indicies,
            str(MeteorType.head),
            event_select_cfg,
            overlap_correction=True,
        )
        meteor_trail_events = create_event_cluster(
            echo,
            meteor_trail_indicies,
            str(MeteorType.trail),
            event_select_cfg,
        )

        events = Events(
            meteors=meteor_events,
            meteor_indicies=meteor_indicies,
            trails=meteor_trail_events,
            trail_indicies=meteor_trail_indicies,
            detection_per_index=detection_per_index,
            config=(echo_search_cfg, event_search_cfg, event_select_cfg, event_criteria_cfg),
            exp_def=exp,
            event_search_start_us=echo.epoch_us,
            event_search_end_us=int(echo.epoch_us + len(echo.max_corr) * exp.t_ipp_usec),
            file=data.path,
        )

        if output:
            store_events(events, Path(output).resolve())

        if prog:
            prog.update(len(events.meteors) + len(events.trails))
            prog.close()

    else:
        events = None
        echo = None
        noise = None

    events = comm.bcast(events, root=0)
    echo = comm.bcast(echo, root=0)
    noise = comm.bcast(noise, root=0)

    return events, echo, noise


def echo_post_process(
    echo_search_analysis: EchoSearchOutArgs,
    exp_def: ExpDef,
    config: EventSearchCfg,
) -> Echo:
    """
    Post processing of echo search.

    Args:
        echo_search_analysis: Output from hardtarget echo search
        exp_def: Experiment definition
        config: The search configuration

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
    doppler_coherrence = int(np.sum(doppler_std < config.dop_std_coherr / len(doppler_std)))
    start_coherrence = int(np.sum(start_std < (config.start_std_coherr / len(start_std))))

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

    return Echo(
        exp_def=exp_def,
        tot_pow=echo_search_analysis.tot_pow,
        max_corr=echo_search_analysis.max_corr,
        max_corr_ind=echo_search_analysis.max_corr_ind,
        best_doppler=echo_search_analysis.best_doppler,
        epoch_us=echo_search_analysis.epoch_us,
        tot_pow_filt=echo_search_analysis.tot_pow[_filter_indices],
        best_peak_filt=echo_search_analysis.max_corr[_filter_indices],
        start_std=start_std,
        start_coherrence=start_coherrence,
        doppler_std=doppler_std,
        doppler_coherrence=doppler_coherrence,
    )


def calculate_noise(
    echo_search_analysis: EchoSearchOutArgs,
    exp_def: ExpDef,
    chunk_size: int,
    progress: bool | CommBar = False,
) -> GaussianNoiseChunks:
    """
    Calculate the gaussian noise from a echo search.

    Args:
        echo_search_analysis: Output from a echo search (hardtarget)
        exp_def: Experiment parameters.
        chunk_size: Number of ipps to calculate each block of gaussian noise over.
        progress (optional): If a progress bar should be visualized.
    Returns.
        The gaussian noise over each chunk.
    """

    mean, std_dev, confidence_interval = calc_gaussian_noise_batch_chunks(
        mean_per_batch=echo_search_analysis.mean,
        std_dev_per_batch=echo_search_analysis.std_dev,
        batch_size=exp_def.ipp_samps,
        chunk_size=chunk_size,
        progress=progress,
    )

    return GaussianNoiseChunks(
        mean=mean,
        std_dev=std_dev,
        confidence_interval=confidence_interval,
        epoch_us=echo_search_analysis.epoch_us,
        chunk_size_usec=chunk_size * exp_def.ipp_samps * exp_def.t_samp_usec,
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
    type: str,
    config: EventSelectCfg,
    overlap_correction: bool = False,
) -> list[Event]:
    """
    Generate a event cluster of given type

    Args:
        echo: Echo
        object_indicies: Indicies in the Echo where events are present.
        type: object type, used as a category tag for the event.
        config: Event select configuration.
        overlap_correction (optional): If more than one event found, adjust the windows to not make them overlap.
    Returns:
        List of Events.

    """

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
        for x in range(events_found - 1):
            event_overlap = event_span[x, 1] - event_span[x + 1, 0]
            if event_overlap > config.event_max_overlap:
                contr_IPP = math.floor(0.5 * (event_overlap - config.event_max_overlap))
                event_span[x, 1] -= contr_IPP
                event_span[x + 1, 0] += contr_IPP

    # Create head events
    events: list[Event] = []
    for x in range(events_found):
        event_indices = object_indicies[
            np.logical_and(object_indicies > event_span[x, 0], object_indicies < event_span[x, 1])
        ]
        event_offset_us = int(event_span[x, 0] * echo.exp_def.t_ipp_usec)
        ev_date = np.datetime64(int(echo.epoch_us + event_offset_us), "us")

        ev = Event(
            start_ipp=int(event_span[x, 0]),
            end_ipp=int(event_span[x, 1]),
            event_indices=event_indices,
            event_date=ev_date,
            event_search_executed=np.datetime64(dt.datetime.now(dt.timezone.utc)),
            type=type,
        )

        events.append(ev)

    events.sort()
    return events

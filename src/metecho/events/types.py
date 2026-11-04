from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import numpy as np
import numpy.typing as npt
from hardtarget.echo_search.types import EchoSearchCfgParams
from radardef.types.types import ExpDef


@dataclass
class EventSearchCfg:
    """
    Args:
        dop_std_coherr: Threshold for the moving Doppler standard deviation to be considered coherent.
        start_std_coherr: Threshold for the moving range (max correlation index) standard deviation to be considered coherent.
        power_std_est: The number of standard deviations above the mean noise power used as a threshold to filter out Gaussian noise.
        corr_filter_limit: The correlation threshold used to separate coherent signals from background Gaussian noise.
        move_std_window:  Sliding windown size for standard deviation calculations.
        noise_chunk_size: The number of IPPs that each noise calculation segment should span.
    """

    dop_std_coherr: float = 7e3
    start_std_coherr: float = 13
    pow_std_est: float = 3
    corr_filter_limit: float = 0.5
    move_std_window: int = 10
    noise_chunk_size: int = 100


@dataclass
class EventSelectCfg:
    """
    Args:
        min_ipps: Least amount of ipps available to create a event.
        min_ipp_separation_split: Least amount of ipps between sightings for them to be qualified as different events.
        min_dop_separation_split: Least difference in doppler between sightings for them to be qualified as different events.
        min_range_separation_split: Least difference in range between sightings for them to be qualified as different events.
        smoothing_window: Window size for savgol filter when smoothing doppler and range.
        polyorder: Order of the polynomial used to fit the samples within the moving window.
        event_max_overlap: Maximum ipp overlap of windows before merging them to one.
    """

    min_ipps: int
    min_ipp_separation_split: int
    min_dop_separation_split: float
    min_range_separation_split: float
    smoothing_window: int
    polyorder: int
    event_max_overlap: int = 10


@dataclass
class EventCriteriaCfg:
    """
    Args:
        criteria_n: Number of search criteria that must be fulfilled per index to classify a detection as an event.
        correlation_sigma:  Number of standard deviations above the mean filtered peak used as a threshold for cross-correlation.
        totpow_sigma:  Number of standard deviations above the mean filtered total power used as a threshold.
        doppler_std_sigma: Multiplier for the standard deviation of best Doppler used to threshold the Doppler standard deviation.
        start_std_sigma:  Multiplier for the standard deviation of max correlation index used to threshold the range standard deviation.
        doppler_sigma: Number of standard deviations used to define the upper and lower bounds around the mean Doppler.
        ind_pm: The index tolerance (plus/minus) relative to the mean correlation index.
        min_start_allowed: Minimum tolerated start sample within the ipp (typically the tx start sample)
        max_start_allowed: Maximum tolerated start sanoke within the ipp.
        min_dop_allowed: Minimum doppler tolerated.
        start_std_coherr_percent: The minimum allowed percentage level of coherence for the range (max correlation index).
        dop_std_coherr_percent: The minimum allowed percentage level of coherence for the Doppler signal.
    """

    criteria_n: int = 3
    correlation_sigma: float = 1
    totpow_sigma: float = 1.5
    doppler_std_sigma: float = 0.5
    start_std_sigma: float = 0.5
    doppler_sigma: float = 3
    ind_pm: int = 3
    min_start_allowed: int = 0
    max_start_allowed: int = 1000
    min_dop_allowed: float = 0
    start_std_coherr_percent: float = 0.1
    dop_std_coherr_percent: float = 0.1


class Echo(NamedTuple):
    exp_def: ExpDef
    tot_pow: npt.NDArray[np.floating]
    max_corr: npt.NDArray[np.complex128]
    max_corr_ind: npt.NDArray[np.integer]
    max_corr_delay: npt.NDArray[np.integer]
    best_doppler: npt.NDArray[np.integer]
    epoch_us: int
    tot_pow_filt: npt.NDArray[np.floating]
    best_peak_filt: npt.NDArray[np.complex128]
    start_std: npt.NDArray[np.integer]  # derived from max_pow_ind
    start_coherrence: float
    doppler_std: npt.NDArray[np.integer]  # derived from best_doppler
    doppler_coherrence: float


class Event(NamedTuple):
    start_ipp: int
    end_ipp: int
    min_range_gate: int
    max_range_gate: int
    event_indices: npt.NDArray[np.int64]
    event_date: np.datetime64
    event_search_executed: np.datetime64
    type: str


class Events(NamedTuple):
    meteors: list[Event]
    meteor_indicies: npt.NDArray[np.int64]
    trails: list[Event]
    trail_indicies: npt.NDArray[np.int64]
    detection_per_index: npt.NDArray[np.int64]
    config: tuple[EchoSearchCfgParams, EventSearchCfg, EventSelectCfg, EventCriteriaCfg]
    exp_def: ExpDef
    event_search_start_us: int
    event_search_end_us: int
    file: Path

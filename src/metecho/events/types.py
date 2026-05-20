from pathlib import Path
from typing import NamedTuple

import numpy as np
import numpy.typing as npt
from radardef.types.types import ExpDef

from metecho.noise.types import GaussianNoise


class EventSearchCfg(NamedTuple):
    dop_std_coherr: float
    start_std_coherr: float
    pow_std_est: float
    pow_std_filt: float
    allow_analysis_overlap: int
    corr_filter_limit: float
    noise_time_window_sec: float
    move_std_window: int


class EventSelectCfg(NamedTuple):
    least_ipp_available: int
    min_ipp_separation_split: int
    min_dop_separation_split: float
    min_range_separation_split: float
    ipp_extend: int
    smoothing_window: int
    polyorder: int
    event_max_overlap: int = 10


class EventCriteriaCfg(NamedTuple):
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
    best_doppler: npt.NDArray[np.integer]
    epoch_us: int
    tot_pow_filt: npt.NDArray[np.floating]
    best_peak_filt: npt.NDArray[np.complex128]
    gauss_noise: GaussianNoise
    start_std: npt.NDArray[np.integer]  # derived from max_pow_ind
    start_coherrence: np.floating
    doppler_std: npt.NDArray[np.integer]  # derived from best_doppler
    doppler_coherrence: np.floating
    ipp_offset: int


class Event(NamedTuple):
    start_ipp: int
    end_ipp: int
    event_indices: npt.NDArray[np.int64]
    event_date: np.datetime64
    event_search_executed: np.datetime64
    type: str
    noise: GaussianNoise
    ipp_offset: int


class Events(NamedTuple):
    meteors: list[Event]
    meteor_indicies: npt.NDArray[np.int64]
    trails: list[Event]
    trail_indicies: npt.NDArray[np.int64]
    detection_per_index: npt.NDArray[np.int64]
    config: EventCriteriaCfg
    exp_def: ExpDef
    measurement_start_us: int
    file: Path

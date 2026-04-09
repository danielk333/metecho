from pathlib import Path
from typing import NamedTuple

import numpy as np
import numpy.typing as npt
from radardef.types.types import ExpDef

from metecho.noise.types import GaussianNoise


class EventSearchConfig(NamedTuple):
    # Detection metrics
    CRITERIA_N: int
    MOVE_STD_WINDOW: int
    # Power and correlation limits
    FIND_CRITERIA_xcorr_sigma: float
    FIND_CRITERIA_totpow_sigma: float
    # Normal move STD
    FIND_CRITERIA_dop_STD_sigma: float
    FIND_CRITERIA_start_STD_sigma: float
    # Constant echo prescense search
    dop_std_coherr: float
    start_std_coherr: float
    start_std_coherr_percent: float
    dop_std_coherr_percent: float
    # Filtering parameters
    pow_std_est: float
    pow_std_filt: float
    # If echoes are present
    FIND_CRITERIA_dop_sigma: float
    FIND_CRITERIA_ind_pm: int
    # 0 dop removal
    # 1e3 * 1 * 46.5e6 / 299792458
    min_dop_allowed: float
    # 85 - 26 / 2
    max_start_allowed: int
    min_start_allowed: int
    # Recursive "index-island" detector
    least_ipp_available: int
    min_ipp_separation_split: int
    # 10e3 * 1 * 46.5e6 / 299792458
    min_dop_separation_split: float
    min_range_separation_split: float
    smoothing_window: int
    polyorder: int
    IPP_extend: int
    # Sequential analysis config
    allow_analysis_overlap: int
    event_max_overlap: int
    # Xcorr settings
    dop_min_freq: int
    dop_max_freq: int
    dop_step_size: int
    # Noise limit
    xcorr_noise_limit: float


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
    data_start_date_us: int
    file: Path
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
    config: EventSearchConfig
    exp_def: ExpDef
    measurement_start_us: int

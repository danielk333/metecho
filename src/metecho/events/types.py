from configparser import ConfigParser
from pathlib import Path
from typing import NamedTuple

import numpy as np
import numpy.typing as npt

from metecho.noise.types import GaussianNoise


class Echo(NamedTuple):
    tot_pow: npt.NDArray[np.complex128]
    max_pow: npt.NDArray[np.complex128]
    max_pow_norm: npt.NDArray[np.complex128]
    max_peak: npt.NDArray[np.complex128]
    max_pow_ind: npt.NDArray[np.integer]
    best_doppler: npt.NDArray[np.integer]
    tot_pow_filt: npt.NDArray[np.floating]
    best_peak_filt: npt.NDArray[np.complex128]
    gauss_noise: GaussianNoise
    start_std: npt.NDArray[np.integer]  # derived from max_pow_ind
    start_coherrence: np.floating
    doppler_std: npt.NDArray[np.integer]  # derived from best_doppler
    doppler_coherrence: np.floating


class Event(NamedTuple):
    start_ipp: int
    end_ipp: int
    event_indices: npt.NDArray[np.int64]
    event_date: np.datetime64
    files_start_date_us: list[int]
    files: list[Path]
    event_search_executed: np.datetime64
    event_search_config: ConfigParser
    type: str
    noise: GaussianNoise


class Events(NamedTuple):
    meteors: list[Event]
    meteor_indicies: npt.NDArray[np.int64]
    trails: list[Event]
    trail_indicies: npt.NDArray[np.int64]
    detection_per_index: list[Event]

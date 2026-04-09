from abc import ABC, abstractmethod
from configparser import ConfigParser

import numpy as np
import numpy.typing as npt

from metecho.events.types import Echo


class SearchObject(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def search(self, event_search_out: Echo, config: ConfigParser) -> npt.NDArray[np.bool]:
        """Searches the data and returns an array of booleans of where the search function is fullfilled"""
        pass

    @property
    @abstractmethod
    def required(self) -> bool:
        pass

    @property
    @abstractmethod
    def required_trails(self) -> bool:
        pass


class XcorrSigma(SearchObject):
    @property
    def required(self) -> bool:
        return False

    @property
    def required_trails(self) -> bool:
        return False

    def search(self, event_search_out: Echo, config: ConfigParser) -> npt.NDArray[np.bool]:
        criteria = np.array(
            event_search_out.max_peak
            > (
                np.mean(event_search_out.best_peak_filt)
                + config.getfloat("General", "FIND_CRITERIA_xcorr_sigma")
                * np.std(event_search_out.best_peak_filt)
            )
        )
        return criteria


class TotpowSigma(SearchObject):
    @property
    def required(self) -> bool:
        return False

    @property
    def required_trails(self) -> bool:
        return False

    def search(self, event_search_out: Echo, config: ConfigParser) -> npt.NDArray[np.bool]:
        criteria = np.array(
            event_search_out.tot_pow
            > (
                np.mean(event_search_out.tot_pow_filt)
                + config.getfloat("General", "FIND_CRITERIA_totpow_sigma")
                * np.std(event_search_out.tot_pow_filt)
            )
        )
        return criteria


class DopplerSigma(SearchObject):
    @property
    def required(self) -> bool:
        return False

    @property
    def required_trails(self) -> bool:
        return False

    def search(self, event_search_out: Echo, config: ConfigParser) -> npt.NDArray[np.bool]:
        self.doppler_coherrence = event_search_out.doppler_coherrence < config.getfloat(
            "General", "dop_std_coherr_percent"
        ) or event_search_out.start_coherrence < config.getfloat("General", "start_std_coherr_percent")
        doppler_std = event_search_out.doppler_std < config.getfloat(
            "General", "FIND_CRITERIA_dop_STD_sigma"
        ) * np.std(event_search_out.best_doppler)
        upper_limit = np.mean(event_search_out.best_doppler) + (
            config.getfloat("General", "FIND_CRITERIA_dop_sigma") * np.std(event_search_out.best_doppler)
        )
        lower_limit = np.mean(event_search_out.best_doppler) - (
            config.getfloat("General", "FIND_CRITERIA_dop_sigma") * np.std(event_search_out.best_doppler)
        )
        best_doppler_above_limit = event_search_out.best_doppler > upper_limit
        best_doppler_below_limit = event_search_out.best_doppler < lower_limit
        criteria = (
            np.array(doppler_std)
            if self.doppler_coherrence
            else np.logical_or(best_doppler_above_limit, best_doppler_below_limit)
        )
        return criteria


class IndPm(SearchObject):
    @property
    def required(self) -> bool:
        return False

    @property
    def required_trails(self) -> bool:
        return False

    def search(self, event_search_out: Echo, config: ConfigParser) -> npt.NDArray[np.bool]:
        self.doppler_coherrence = event_search_out.doppler_coherrence < config.getfloat(
            "General", "dop_std_coherr_percent"
        ) or event_search_out.start_coherrence < config.getfloat("General", "start_std_coherr_percent")
        start_std = event_search_out.start_std < config.getfloat(
            "General", "FIND_CRITERIA_start_STD_sigma"
        ) * np.std(event_search_out.max_pow_ind)
        upper_limit = np.mean(event_search_out.max_pow_ind) + config.getfloat(
            "General", "FIND_CRITERIA_ind_pm"
        )
        lower_limit = np.mean(event_search_out.max_pow_ind) - config.getfloat(
            "General", "FIND_CRITERIA_ind_pm"
        )
        best_start_above_limit = event_search_out.max_pow_ind > upper_limit
        best_start_below_limit = event_search_out.max_pow_ind < lower_limit
        criteria = (
            np.array(start_std)
            if self.doppler_coherrence
            else np.logical_or(best_start_above_limit, best_start_below_limit)
        )
        return criteria


class MinDopAllowed(SearchObject):
    @property
    def required(self) -> bool:
        return True

    @property
    def required_trails(self) -> bool:
        return True

    def search(self, event_search_out: Echo, config: ConfigParser) -> npt.NDArray[np.bool]:
        criteria = np.array(
            ((np.abs(event_search_out.best_doppler)) > config.getfloat("General", "min_dop_allowed"))
        )
        return criteria


class MinStartAllowed(SearchObject):
    @property
    def required(self) -> bool:
        return True

    @property
    def required_trails(self) -> bool:
        return False

    def search(self, event_search_out: Echo, config: ConfigParser) -> npt.NDArray[np.bool]:
        criteria = np.logical_and(
            (event_search_out.max_pow_ind >= config.getint("General", "min_start_allowed")),
            (event_search_out.max_pow_ind <= config.getint("General", "max_start_allowed")),
        )
        return criteria


def get_defaults() -> list[SearchObject]:
    return [XcorrSigma(), TotpowSigma(), DopplerSigma(), IndPm(), MinDopAllowed(), MinStartAllowed()]

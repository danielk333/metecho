from abc import ABC, abstractmethod
import numpy as np


def get_defaults():
    return [XcorrSigma(), TotpowSigma(), DopplerSigma(), IndPm(), MinDopAllowed(), MinStartAllowed()]


class SearchObject(ABC):
    def __init__(self, **kwargs):
        self.criteria = []
        self.arguments = kwargs
        super().__init__()

    @abstractmethod
    def search(self, matched_filter_output, raw_data, *args):
        pass

    @property
    @abstractmethod
    def required(self):
        pass

    @property
    @abstractmethod
    def required_trails(self):
        pass


class XcorrSigma(SearchObject):
    required = False
    required_trails = False

    def search(self, matched_filter_output, raw_data, config):
        self.required = False
        self.criteria = np.array(matched_filter_output["best_peak"]
                                 > (np.mean(matched_filter_output["best_peak_filt"])
                                    + config.getfloat("General", "FIND_CRITERIA_xcorr_sigma")
                                    * np.std(matched_filter_output["best_peak_filt"])))
        return self.criteria


class TotpowSigma(SearchObject):
    required = False
    required_trails = False

    def search(self, matched_filter_output, raw_data, config):
        self.criteria = np.array(matched_filter_output["tot_pow"]
                                 > (np.mean(matched_filter_output["tot_pow_filt"])
                                    + config.getfloat("General", "FIND_CRITERIA_totpow_sigma")
                                    * np.std(matched_filter_output["tot_pow_filt"])))
        return self.criteria


class DopplerSigma(SearchObject):
    required = False
    required_trails = False

    def search(self, matched_filter_output, raw_data, config):
        self.doppler_coherrence = (matched_filter_output["doppler_coherrence"]
                                   < config.getfloat("General", "dop_std_coherr_percent")
                                   or matched_filter_output["start_coherrence"]
                                   < config.getfloat("General", "start_std_coherr_percent"))
        doppler_std = (matched_filter_output["doppler_std"]
                       < config.getfloat("General", "FIND_CRITERIA_dop_STD_sigma")
                       * np.std(matched_filter_output["best_doppler"]))
        upper_limit = (np.mean(matched_filter_output["best_doppler"])
                       + (config.getfloat("General", "FIND_CRITERIA_dop_sigma")
                          * np.std(matched_filter_output["best_doppler"])))
        lower_limit = (np.mean(matched_filter_output["best_doppler"])
                       - (config.getfloat("General", "FIND_CRITERIA_dop_sigma")
                          * np.std(matched_filter_output["best_doppler"])))
        best_doppler_above_limit = matched_filter_output["best_doppler"] > upper_limit
        best_doppler_below_limit = matched_filter_output["best_doppler"] < lower_limit
        self.criteria = (np.array(doppler_std)
                         if self.doppler_coherrence
                         else np.logical_or(best_doppler_above_limit, best_doppler_below_limit))
        return self.criteria


class IndPm(SearchObject):
    required = False
    required_trails = False

    def search(self, matched_filter_output, raw_data, config):
        self.doppler_coherrence = (matched_filter_output["doppler_coherrence"]
                                   < config.getfloat("General", "dop_std_coherr_percent")
                                   or matched_filter_output["start_coherrence"]
                                   < config.getfloat("General", "start_std_coherr_percent"))
        start_std = (matched_filter_output["start_std"]
                     < config.getfloat("General", "FIND_CRITERIA_start_STD_sigma")
                     * np.std(matched_filter_output["best_start"]))
        upper_limit = (np.mean(matched_filter_output["best_start"])
                       + config.getfloat("General", "FIND_CRITERIA_ind_pm"))
        lower_limit = (np.mean(matched_filter_output["best_start"])
                       - config.getfloat("General", "FIND_CRITERIA_ind_pm"))
        best_start_above_limit = matched_filter_output["best_start"] > upper_limit
        best_start_below_limit = matched_filter_output["best_start"] < lower_limit
        self.criteria = (np.array(start_std)
                         if self.doppler_coherrence
                         else np.logical_or(best_start_above_limit, best_start_below_limit))
        return self.criteria


class MinDopAllowed(SearchObject):
    required = True
    required_trails = True

    def search(self, matched_filter_output, raw_data, config):
        self.criteria = np.array(((np.abs(matched_filter_output["best_doppler"]))
                                  > config.getfloat("General", "min_dop_allowed")))
        return self.criteria


class MinStartAllowed(SearchObject):
    required = True
    required_trails = False

    def search(self, matched_filter_output, raw_data, config):
        self.criteria = np.logical_and((matched_filter_output["best_start"]
                                        >= config.getint("General", "min_start_allowed")),
                                       (matched_filter_output["best_start"]
                                        <= config.getint("General", "max_start_allowed")))
        return self.criteria

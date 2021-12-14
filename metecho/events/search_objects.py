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
    def trailable(self):
        pass


class XcorrSigma(SearchObject):
    required = False
    trailable = False

    def search(self, matched_filter_output, raw_data, config):
        self.required = False
        self.criteria = np.array(matched_filter_output["best_peak"]
                                 > (np.mean(matched_filter_output["best_peak_filt"])
                                    + config.getfloat("General", "FIND_CRITERIA_xcorr_sigma")
                                    * np.std(matched_filter_output["best_peak_filt"])))
        return self.criteria


class TotpowSigma(SearchObject):
    required = False
    trailable = False

    def search(self, matched_filter_output, raw_data, config):
        self.criteria = np.array(matched_filter_output["tot_pow"]
                                 > (np.mean(matched_filter_output["tot_pow_filt"])
                                    + config.getfloat("General", "FIND_CRITERIA_totpow_sigma")
                                    * np.std(matched_filter_output["tot_pow_filt"])))
        return self.criteria


class DopplerSigma(SearchObject):
    required = False
    trailable = False

    def search(self, matched_filter_output, raw_data, config):
        self.doppler_coherrence = (matched_filter_output["doppler_coherrence"]
                                   < config.getfloat("General", "dop_std_coherr_percent")
                                   or matched_filter_output["start_coherrence"]
                                   < config.getfloat("General", "start_std_coherr_percent"))
        doppler_std = (matched_filter_output["doppler_std"]
                       < config.getfloat("General", "FIND_CRITERIA_dop_STD_sigma")
                       * np.std(matched_filter_output["best_doppler"]))
        best_doppler_plus_std = (matched_filter_output["best_doppler"]
                                 > ((np.mean(matched_filter_output["best_doppler"])
                                     + config.getfloat("General", "FIND_CRITERIA_dop_sigma")
                                     * np.std(matched_filter_output["best_doppler"]))))
        best_doppler_minus_std = (matched_filter_output["best_doppler"]
                                  < np.mean(matched_filter_output["best_doppler"])
                                  - config.getfloat("General",
                                                    "FIND_CRITERIA_dop_sigma")
                                  * np.std(matched_filter_output["best_doppler"]))
        self.criteria = (np.array(doppler_std)
                         if self.doppler_coherrence
                         else np.logical_or(best_doppler_plus_std, best_doppler_minus_std))
        return self.criteria


class IndPm(SearchObject):
    required = False
    trailable = False

    def search(self, matched_filter_output, raw_data, config):
        self.doppler_coherrence = (matched_filter_output["doppler_coherrence"]
                                   < config.getfloat("General", "dop_std_coherr_percent")
                                   or matched_filter_output["start_coherrence"]
                                   < config.getfloat("General", "start_std_coherr_percent"))
        start_std = (matched_filter_output["start_std"]
                     < config.getfloat("General", "FIND_CRITERIA_start_STD_sigma")
                     * np.std(matched_filter_output["best_start"]))
        best_start_plus = (matched_filter_output["best_start"]
                           > np.mean(matched_filter_output["best_start"])
                           + config.getfloat("General", "FIND_CRITERIA_ind_pm"))
        best_start_minus = (matched_filter_output["best_start"]
                            < np.mean(matched_filter_output["best_start"])
                            - config.getfloat("General", "FIND_CRITERIA_ind_pm"))
        self.criteria = (np.array(start_std)
                         if self.doppler_coherrence
                         else np.logical_or(best_start_plus, best_start_minus))
        return self.criteria


class MinDopAllowed(SearchObject):
    required = True
    trailable = True

    def search(self, matched_filter_output, raw_data, config):
        self.criteria = np.array(((np.abs(matched_filter_output["best_doppler"]))
                                  > config.getfloat("General", "min_dop_allowed")))
        return self.criteria


class MinStartAllowed(SearchObject):
    required = True
    trailable = False

    def search(self, matched_filter_output, raw_data, config):
        self.criteria = np.logical_and((matched_filter_output["best_start"]
                                        >= config.getint("General", "min_start_allowed")),
                                       (matched_filter_output["best_start"]
                                        <= config.getint("General", "max_start_allowed")))
        return self.criteria

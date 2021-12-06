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


class XcorrSigma(SearchObject):
    required = False

    def search(self, matched_filter_output, raw_data, config):
        self.required = False
        self.criteria = np.array(matched_filter_output["best_peak"]
                                 > (np.mean(matched_filter_output["best_peak_filt"])
                                    + config.getfloat("General", "FIND_CRITERIA_xcorr_sigma")
                                    * np.std(matched_filter_output["best_peak_filt"])))
        return self.criteria


class TotpowSigma(SearchObject):
    required = False

    def search(self, matched_filter_output, raw_data, config):
        self.criteria = np.array(matched_filter_output["tot_pow"]
                                 > (np.mean(matched_filter_output["tot_pow_filt"])
                                    + config.getfloat("General", "FIND_CRITERA_totpow_sigma")
                                    * np.str(matched_filter_output["tot_pow_filt"])))
        return self.criteria


class DopplerSigma(SearchObject):
    required = False

    def search(self, matched_filter_output, raw_data, config):
        self.doppler_coherrence = (matched_filter_output["doppler_coherrence"]
                                   < config.getfloat("General", "dop_std_coherr_percent")
                                   or matched_filter_output["start_coherrence"]
                                   < config.getfloat("General", "start_std_coherr_percent"))
        self.criteria = np.array(matched_filter_output["best_doppler"]
                                 > (np.mean(matched_filter_output["best_doppler"]))
                                 + config.getfloat("General", "FIND_CRITERIA_dop_sigma")
                                 or (self.doppler_coherrence and matched_filter_output["best_doppler"]
                                     < np.mean(matched_filter_output["best_doppler"])
                                     - config.getfloat("General", "FIND_CRITERIA_dop_sigma")
                                     * np.mean(matched_filter_output["best_doppler"])))
        return self.criteria


class IndPm(SearchObject):
    required = False

    def search(self, matched_filter_output, raw_data, config):
        self.doppler_coherrence = (matched_filter_output["doppler_coherrence"]
                                   < config.getfloat("General", "dop_std_coherr_percent")
                                   or matched_filter_output["start_coherrence"]
                                   < config.getfloat("General", "start_std_coherr_percent"))
        self.criteria = np.array(matched_filter_output["best_start"]
                                 > np.mean(matched_filter_output["best_start"])
                                 + config.getfloat("General", "FIND_CRITERIA_ind_pm")
                                 or (self.doppler_coherrence and matched_filter_output["best_start"]
                                     < np.mean(matched_filter_output["best_start"])
                                     - config.getfloat("General", "FIND_CRITERIA_ind_pm")))
        return self.criteria


class MinDopAllowed(SearchObject):
    required = True

    def search(self, matched_filter_output, raw_data, config):
        self.criteria = np.array(np.abs(matched_filter_output["best_doppler"]
                                        ) > config.getfloat("General", "min_dop_allowed"))
        return self.criteria


class MinStartAllowed(SearchObject):
    required = True

    def search(self, matched_filter_output, raw_data, config):
        self.criteria = np.array(matched_filter_output["best_start"]
                                 >= config.getfloat("General", "min_start_allowed")
                                 and matched_filter_output["best_start"]
                                 <= config.getfloat("General", "max_start_allowed"))
        return self.criteria

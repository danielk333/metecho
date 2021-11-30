from abc import ABC, abstractmethod
import numpy as np


class SearchObject(ABC):
    def __init__(self, **kwargs):
        self.arguments = kwargs
        super().__init__()

    @abstractmethod
    def search(self, matched_filter_output, raw_data, *args):
        pass


"""
class XcorrSigma(SearchObject):
    def search(self, matched_filter_output, raw_data, config):
        matched_filter_output["best_peak"] > np.mean(config)
"""
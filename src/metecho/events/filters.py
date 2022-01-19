import numpy as np
from abc import ABC, abstractmethod


class FilterObject(ABC):
    def __init__(self, **kwargs):
        self.arguments = kwargs
        super().__init__()

    @abstractmethod
    def filter(self, raw_data):
        pass

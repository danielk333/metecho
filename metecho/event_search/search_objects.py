from abc import ABC, abstractmethod


class SearchObject(ABC):
    def __init__(self, **kwargs):
        self.arguments = kwargs
        super().__init__()

    @abstractmethod
    def search(self, matched_filter_output):
        pass

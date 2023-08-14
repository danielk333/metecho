from abc import ABC, abstractmethod


class Model(ABC):

    def __init__(self, duration=0):
        self.duration = duration

    @abstractmethod
    def evaluate(self, t, **kwargs):
        pass

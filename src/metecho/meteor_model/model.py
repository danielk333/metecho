from abc import ABC, abstractmethod

import numpy as np
import numpy.typing as npt


class Model(ABC):
    @abstractmethod
    def evaluate(
        self, t: npt.NDArray[np.float64] | npt.NDArray[np.int64]
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """Evalutate over time t"""
        pass

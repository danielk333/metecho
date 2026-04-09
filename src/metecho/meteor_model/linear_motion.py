from abc import abstractmethod

import numpy as np
import numpy.typing as npt

from .model import Model


class LinearMotion(Model):
    """Base linear motion model to be subclassed with a velocity function


    Args:
        p0: Initial position at t = 0
        r0: Initial velocity at t = 0
        vel_params: TODO
    """

    def __init__(self, p0: npt.NDArray[np.float64], r0: npt.NDArray[np.float64], vel_params) -> None:
        self.p0 = p0
        self.r0 = r0
        self.vel_params = vel_params

    def evaluate(
        self, t: npt.NDArray[np.float64] | npt.NDArray[np.int64]
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Evaluate range and velocity over time t

        Args:
            t: Timepoints to evaluate
        Returns:
            range and velocity at time t.
        """

        dist = self.integral_velocity(t)
        vel = self.velocity(t)
        r = self.p0[:, None] + dist[None, :] * self.r0[:, None]
        v = self.r0[:, None] * vel[None, :]
        return r, v

    @abstractmethod
    def velocity(self, t: npt.NDArray[np.float64] | npt.NDArray[np.int64]) -> npt.NDArray[np.float64]:
        """Velocity at time t"""
        pass

    @abstractmethod
    def integral_velocity(
        self, t: npt.NDArray[np.float64] | npt.NDArray[np.int64]
    ) -> npt.NDArray[np.float64]:
        """Displacement at time t"""
        pass


class ExpVelocity(LinearMotion):
    """Exponential velocity along a linear trajectory"""

    def velocity(self, t: npt.NDArray[np.float64] | npt.NDArray[np.int64]) -> npt.NDArray[np.float64]:
        """Velocity at time t"""
        return self.vel_params[0] - self.vel_params[1] * np.exp(self.vel_params[2] * t)

    def integral_velocity(
        self, t: npt.NDArray[np.float64] | npt.NDArray[np.int64]
    ) -> npt.NDArray[np.float64]:
        """Displacement at time t"""

        return self.vel_params[0] * t - (self.vel_params[1] / self.vel_params[2]) * (
            np.exp(self.vel_params[2] * t) - 1
        )

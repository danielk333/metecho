from abc import abstractmethod

import numpy as np

from .model import Model


class LinearMotion(Model):
    """Base linear motion model to be subclassed with a velocity function"""

    def __init__(self, p0, r0, vel_params, **kwargs):
        super().__init__(**kwargs)
        self.p0 = p0
        self.r0 = r0
        self.vel_params = vel_params

    def evaluate(self, t, **kwargs):
        dist = self.integral_velocity(t)
        vel = self.velocity(t)
        r = self.p0[:, None] + dist[None, :] * self.r0[:, None]
        v = self.r0[:, None] * vel[None, :]
        return r, v

    @abstractmethod
    def velocity(self, t):
        pass

    @abstractmethod
    def integral_velocity(self, t):
        pass


class ExpVelocity(LinearMotion):
    """Exponential velocity along a linear trajectory"""

    def velocity(self, t):
        return self.vel_params[0] - self.vel_params[1] * np.exp(self.vel_params[2] * t)

    def integral_velocity(self, t):
        return self.vel_params[0] * t - (self.vel_params[1] / self.vel_params[2]) * (
            np.exp(self.vel_params[2] * t) - 1
        )

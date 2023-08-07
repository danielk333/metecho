#!/usr/bin/env python

"""
Calculating pre-encounter orbits
==================================

"""

import logging

import numpy as np
from astropy.time import TimeDelta

import pyorb

from .propagators import Rebound
from .. import frames

logger = logging.getLogger(__name__)


def distance_termination(dAU):
    def distance_termination_method(
        self, t, step_index, massive_states, particle_states
    ):
        e_state = massive_states[:3, step_index, self._earth_ind]
        d_earth = np.linalg.norm(
            particle_states[:3, step_index, :] - e_state[:, None], axis=0
        )
        return np.all(d_earth / pyorb.AU > dAU)

    return distance_termination_method


def propagate_pre_encounter(
    states,
    epoch,
    in_frame,
    out_frame,
    kernel,
    termination_check=None,
    dt=10.0,
    max_t=10 * 24 * 3600.0,
    settings=None,
):
    """Propagates a state from the states backwards in time until the termination_check is true."""
    t = -np.arange(0, max_t, dt, dtype=np.float64)

    if termination_check:

        class TerminatedRebound(Rebound):
            pass

        TerminatedRebound.termination_check = termination_check
        PropCls = TerminatedRebound
    else:
        PropCls = Rebound

    reb_settings = dict(
        in_frame=in_frame,
        out_frame=out_frame,
        time_step=dt,  # s
        termination_check=True,
    )
    if settings is not None:
        settings.update(reb_settings)
    else:
        settings = reb_settings

    prop = PropCls(
        kernel=kernel,
        settings=settings,
    )

    particle_states, massive_states = prop.propagate(t, states, epoch)

    t = t[: particle_states.shape[1]]

    return particle_states, massive_states, t


def rebound_orbit_determination(
    states,
    epoch,
    kernel,
    termination_check=True,
    dt=10.0,
    max_t=10 * 24 * 3600.0,
    settings=None,
):
    """Determine the orbit using rebound, states in ITRS"""
    logger.debug(f"Using JPL kernel: {kernel}")

    num = len(states.shape[1])
    results = {}

    check_func = distance_termination(dAU=0.01) if termination_check else None

    logger.debug(f"propagating {num} particles from epoch: {epoch.iso}")
    particle_states, massive_states, t = propagate_pre_encounter(
        states,
        epoch,
        in_frame="ITRS",
        out_frame="HCRS",
        kernel=kernel,
        termination_check=check_func,
    )
    results["states"] = particle_states
    results["massive_states"] = massive_states
    results["t"] = t

    if termination_check:
        logger.debug(f"Time to hill sphere exit: {t[-1]/3600.0:.2f} h")

    results["kepler"] = np.empty_like(particle_states)

    orb = pyorb.Orbit(
        M0=pyorb.M_sol,
        direct_update=True,
        auto_update=True,
        degrees=True,
        num=len(t),
    )

    for ind in range(num):
        p_states_HMC = frames.convert(
            epoch + TimeDelta(t, format="sec"),
            particle_states[:, :, ind],
            in_frame="HCRS",
            out_frame="HeliocentricMeanEcliptic",
        )
        orb.cartesian = p_states_HMC
        results["kepler"][:, :, ind] = orb.kepler

    return results

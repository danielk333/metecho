#!/usr/bin/env python

"""
Calculating pre-encounter orbits
==================================

"""

import logging

import numpy as np
from astropy.time import TimeDelta
from tqdm import tqdm

import pyorb
import pyant

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
    t = TimeDelta(-np.arange(0, max_t, dt, dtype=np.float64), format="sec")

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
        termination_check=True if termination_check else False,
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

    return particle_states, massive_states, t, prop


def rebound_od(
    states,
    epoch,
    kernel,
    out_frame="HCRS",
    termination_check=True,
    dt=10.0,
    max_t=10 * 24 * 3600.0,
    settings=None,
):
    """Determine the orbit using rebound, states in ITRS"""
    logger.debug(f"Using JPL kernel: {kernel}")

    if len(states.shape) == 1:
        states.shape = (states.size, 1)
    num = states.shape[1]

    results = {}

    check_func = distance_termination(dAU=0.01) if termination_check else None

    logger.debug(f"propagating {num} particles from epoch: {epoch.iso}")
    particle_states, massive_states, t, prop = propagate_pre_encounter(
        states,
        epoch,
        in_frame="ITRS",
        out_frame="HCRS",
        kernel=kernel,
        termination_check=check_func,
        dt=dt,
        max_t=max_t,
    )
    if len(particle_states.shape) == 2:
        particle_states.shape = particle_states.shape + (1,)
    results["states"] = particle_states
    results["massive_states"] = massive_states
    results["t"] = t

    sun_ind = prop._sun_ind
    earth_ind = prop._earth_ind

    if termination_check:
        logger.debug(f"Time to hill sphere exit: {t.sec[-1]/3600.0:.2f} h")

    p_states_hmc = frames.convert(
        epoch + TimeDelta(t[-1], format="sec"),
        particle_states[:, -1, :],
        in_frame="HCRS",
        out_frame=out_frame,
    )
    m_states_hmc = frames.convert(
        epoch + TimeDelta(t[-1], format="sec"),
        massive_states[:, -1, :],
        in_frame="HCRS",
        out_frame=out_frame,
    )
    earth_hmc = m_states_hmc[:, earth_ind]
    m_states_emc = m_states_hmc - earth_hmc[:, None]
    p_states_emc = p_states_hmc - earth_hmc[:, None]

    results["ecliptic_states"] = p_states_hmc
    ecliptic_radiant = -1 * pyant.coordinates.cart_to_sph(
        p_states_emc[3:, :], degrees=True
    )
    sun_emc = m_states_emc[:, sun_ind]
    sun_dir = pyant.coordinates.cart_to_sph(
        sun_emc[:3], degrees=True
    )
    results["ecliptic_radiant"] = ecliptic_radiant[:2, :]
    results["ecliptic_sun_dir"] = sun_dir[:2]

    results["kepler"] = np.empty_like(particle_states)
    orb = pyorb.Orbit(
        M0=pyorb.M_sol,
        direct_update=True,
        auto_update=True,
        degrees=True,
        num=len(t),
    )
    for ind in tqdm(range(num)):
        p_cart = frames.convert(
            epoch + TimeDelta(t, format="sec"),
            particle_states[:, :, ind],
            in_frame="HCRS",
            out_frame="HeliocentricMeanEcliptic",
        )
        orb.cartesian = p_cart
        results["kepler"][:, :, ind] = orb.kepler

    return results

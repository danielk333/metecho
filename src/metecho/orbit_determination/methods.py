#!/usr/bin/env python

"""
Calculating pre-encounter orbits
==================================

"""

import logging

import numpy as np
from astropy.time import TimeDelta
import astropy.coordinates as coords
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
    kepler_out_frame="ICRS",
    radiant_out_frame="GeocentricMeanEcliptic",
    termination_check=True,
    dt=10.0,
    max_t=10 * 24 * 3600.0,
    settings=None,
    progress_bar=True,
):
    """Determine the orbit using rebound, states in ITRS"""
    logger.debug(f"Using JPL kernel: {kernel}")

    if len(states.shape) == 1:
        states.shape = (states.size, 1)
    num = states.shape[1]

    results = {}
    if settings is None:
        settings = {}
    settings.update(dict(tqdm=progress_bar))

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
        settings=settings,
    )
    if len(particle_states.shape) == 2:
        particle_states.shape = particle_states.shape + (1,)
    results["states"] = particle_states
    results["massive_states"] = massive_states
    results["t"] = t

    results["hcrs_states"] = particle_states[:, -1, :]

    if termination_check:
        logger.debug(f"Time to hill sphere exit: {t.sec[-1]/3600.0:.2f} h")

    if not isinstance(radiant_out_frame, list):
        radiant_out_frame = [radiant_out_frame]

    sun_radiant = coords.get_sun(epoch)
    for frame_name in radiant_out_frame:

        p_states_radiant = frames.convert(
            epoch,
            states,
            in_frame="ITRS",
            out_frame=frame_name,
        )
        results["radiant_obs_states_" + frame_name] = p_states_radiant
        radiant = pyant.coordinates.cart_to_sph(
            -1 * p_states_radiant[3:, :], degrees=True
        )
        # ra-dec radiant angles are measured from +x -> +y, not from +y -> +x
        radiant[0, :] = 90 - radiant[0, :]

        p_zat_states_radiant = frames.convert(
            epoch + t[-1],
            results["hcrs_states"],
            in_frame="HCRS",
            out_frame=frame_name,
        )
        results["radiant_orbit_states_" + frame_name] = p_zat_states_radiant
        radiant_zat = pyant.coordinates.cart_to_sph(
            -1 * p_zat_states_radiant[3:, :], degrees=True
        )
        # ra-dec radiant angles are measured from +x -> +y, not from +y -> +x
        radiant_zat[0, :] = 90 - radiant_zat[0, :]

        frame_cls = getattr(coords, frame_name)
        sun_radiant = sun_radiant.transform_to(frame_cls())

        results["radiant_obs_" + frame_name] = radiant[:2, :]
        results["radiant_orbit_" + frame_name] = radiant_zat[:2, :]
        results["radiant_sun_" + frame_name] = np.empty((2, ), dtype=np.float64)
        if hasattr(sun_radiant, "lon"):
            results["radiant_sun_" + frame_name][0] = sun_radiant.lon.deg
            results["radiant_sun_" + frame_name][1] = sun_radiant.lat.deg
        else:
            results["radiant_sun_" + frame_name][0] = sun_radiant.ra.deg
            results["radiant_sun_" + frame_name][1] = sun_radiant.dec.deg

    orb = pyorb.Orbit(
        M0=pyorb.M_sol,
        direct_update=True,
        auto_update=True,
        degrees=True,
        num=len(t),
    )
    if not isinstance(kepler_out_frame, list):
        kepler_out_frame = [kepler_out_frame]

    for frame_name in kepler_out_frame:
        results["kepler_" + frame_name] = np.empty_like(particle_states)
        if progress_bar:
            pbar = tqdm(total=num, desc="Converting frame")

        for ind in range(num):
            if progress_bar:
                pbar.update(1)
            p_cart = frames.convert(
                epoch + TimeDelta(t, format="sec"),
                particle_states[:, :, ind],
                in_frame="HCRS",
                out_frame=frame_name,
            )
            orb.cartesian = p_cart
            results["kepler_" + frame_name][:, :, ind] = orb.kepler

        if progress_bar:
            pbar.close()

    return results

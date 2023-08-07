#!/usr/bin/env python

"""Coordinate frame transformations and related functions.
Main usage is the :code:`convert` function that wraps Astropy frame transformations.

"""

# Python standard import
from collections import OrderedDict

# Third party import
import numpy as np
import astropy.coordinates as coord
import astropy.units as units

try:
    from jplephem.spk import SPK
except ImportError:
    SPK = None


"""List of astropy frames
"""
ASTROPY_FRAMES = {
    "TEME": "TEME",
    "ITRS": "ITRS",
    "ITRF": "ITRS",
    "ICRS": "ICRS",
    "ICRF": "ICRS",
    "GCRS": "GCRS",
    "GCRF": "GCRS",
    "HCRS": "HCRS",
    "HCRF": "HCRS",
    "HeliocentricMeanEcliptic".upper(): "HeliocentricMeanEcliptic",
    "GeocentricMeanEcliptic".upper(): "GeocentricMeanEcliptic",
    "HeliocentricTrueEcliptic".upper(): "HeliocentricTrueEcliptic",
    "GeocentricTrueEcliptic".upper(): "GeocentricTrueEcliptic",
    "BarycentricMeanEcliptic".upper(): "BarycentricMeanEcliptic",
    "BarycentricTrueEcliptic".upper(): "BarycentricTrueEcliptic",
    "SPICEJ2000": "ICRS",
}

ASTROPY_NOT_OBSTIME = [
    "ICRS",
    "BarycentricMeanEcliptic",
    "BarycentricTrueEcliptic",
]

"""Mapping from body name to integer id's used by the kernels.

Taken from `astropy.coordinates.solar_system`
"""
BODY_NAME_TO_KERNEL_SPEC = OrderedDict(
    [
        ("sun", [(0, 10)]),
        ("mercury", [(0, 1), (1, 199)]),
        ("venus", [(0, 2), (2, 299)]),
        ("earth-moon-barycenter", [(0, 3)]),
        ("earth", [(0, 3), (3, 399)]),
        ("moon", [(0, 3), (3, 301)]),
        ("mars", [(0, 4)]),
        ("jupiter", [(0, 5)]),
        ("saturn", [(0, 6)]),
        ("uranus", [(0, 7)]),
        ("neptune", [(0, 8)]),
        ("pluto", [(0, 9)]),
    ]
)


def not_geocentric(frame):
    """Check if the given frame name is one of the non-geocentric frames."""
    frame = frame.upper()
    return frame in ["ICRS", "ICRF", "HCRS", "HCRF"] or frame.startswith(
        "Heliocentric".upper()
    )


def is_geocentric(frame):
    """Check if the frame name is a supported geocentric frame"""
    return not not_geocentric(frame)


def arctime_to_degrees(minutes, seconds):
    return (minutes + seconds / 60.0) / 60.0


def get_solarsystem_body_states(bodies, epoch, kernel, units=None):
    """Open a kernel file and get the statates of the given bodies at epoch in ICRS.

    Note: All outputs from kernel computations are in the Barycentric (ICRS) "eternal" frame.
    """
    assert SPK is not None, "jplephem package needed to directly interact with kernels"
    states = {}

    kernel = SPK.open(kernel)

    epoch_ = epoch.tdb  # jplephem uses Barycentric Dynamical Time (TDB)
    jd1, jd2 = epoch_.jd1, epoch_.jd2

    for body in bodies:
        body_ = body.lower().strip()

        if body_ not in BODY_NAME_TO_KERNEL_SPEC:
            raise ValueError(f'Body name "{body}" not recognized')

        states[body] = np.zeros((6,), dtype=np.float64)

        # if there are multiple steps to go from states to
        # ICRS barycentric, iterate trough and combine
        for pair in BODY_NAME_TO_KERNEL_SPEC[body_]:
            spk = kernel[pair]
            if spk.data_type == 3:
                # Type 3 kernels contain both position and velocity.
                posvel = spk.compute(jd1, jd2).flatten()
            else:
                pos_, vel_ = spk.compute_and_differentiate(jd1, jd2)
                posvel = np.zeros((6,), dtype=np.float64)
                posvel[:3] = pos_
                posvel[3:] = vel_

            states[body] += posvel

        # units from kernels are usually in km and km/day
        if units is None:
            states[body] *= 1e3
            states[body][3:] /= 86400.0
        else:
            states[body] *= units[0]
            states[body][3:] /= units[1]

    return states


def convert(t, states, in_frame, out_frame, **kwargs):
    """Perform predefined coordinate transformations using Astropy.
    Always returns a copy of the array.

    :param numpy.ndarray/float t: Absolute time corresponding to the input states.
    :param numpy.ndarray states: Size `(6,n)` matrix of states in SI units where
        rows 1-3 are position and 4-6 are velocity.
    :param str in_frame: Name of the frame the input states are currently in.
    :param str out_frame: Name of the state to transform to.
    :param Profiler profiler: Profiler instance for checking function performance.
    :param logging.Logger logger: Logger instance for logging the execution of
        the function.
    :rtype: numpy.ndarray
    :return: Size `(6,n)` matrix of states in SI units where rows
        1-3 are position and 4-6 are velocity.

    """

    in_frame = in_frame.upper()
    out_frame = out_frame.upper()

    if in_frame == out_frame:
        return states.copy()

    if in_frame in ASTROPY_FRAMES:
        in_frame_ = ASTROPY_FRAMES[in_frame]
        in_frame_cls = getattr(coord, in_frame_)
    else:
        err_str = (
            f"In frame '{in_frame}' not recognized, "
            "please check spelling or perform manual transformation"
        )
        raise ValueError(err_str)

    kw = {}
    kw.update(kwargs)
    if in_frame_ not in ASTROPY_NOT_OBSTIME:
        kw["obstime"] = t

    astropy_states = _convert_to_astropy(states, in_frame_cls, **kw)

    if out_frame in ASTROPY_FRAMES:
        out_frame_ = ASTROPY_FRAMES[out_frame]
        out_frame_cls = getattr(coord, out_frame_)
    else:
        err_str = (
            f"Out frame '{out_frame}' not recognized, "
            "please check spelling or perform manual transformation"
        )
        raise ValueError(err_str)

    kw = {}
    kw.update(kwargs)
    if out_frame_ not in ASTROPY_NOT_OBSTIME:
        kw["obstime"] = t

    out_states = astropy_states.transform_to(out_frame_cls(**kw))

    rets = states.copy()
    rets[:3, ...] = out_states.cartesian.xyz.to(units.m).value
    rets[3:, ...] = out_states.velocity.d_xyz.to(units.m / units.s).value

    return rets


def _convert_to_astropy(states, frame, **kw):
    state_p = coord.CartesianRepresentation(states[:3, ...] * units.m)
    state_v = coord.CartesianDifferential(states[3:, ...] * units.m / units.s)
    astropy_states = frame(state_p.with_differentials(state_v), **kw)
    return astropy_states

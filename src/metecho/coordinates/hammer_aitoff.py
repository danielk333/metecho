from typing import Optional

import numpy as np
import numpy.typing as npt


def ecliptic_to_hammer(
    lon: npt.NDArray[np.float64],
    lat: npt.NDArray[np.float64],
    sun_lon: Optional[npt.NDArray[np.float64]] = None,
    radians: bool = False,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """
    Convert ecliptic coordinates to hammer projection

    Args:
        lon: Longitude
        lat: Latitude
        sun_lon (optional): TODO
        radians: If lat and lon is declared in radians or not
    Returns:
        Hammer x coordinates and hammer y coordinates
    """

    if not radians:
        lon = np.radians(lon)
        lat = np.radians(lat)
        if sun_lon is not None:
            sun_lon = np.radians(sun_lon)

    if sun_lon is not None:
        # sun centered
        lambdas = np.mod(np.mod(-(lon - sun_lon - 1.5 * np.pi), 2 * np.pi) + 2 * np.pi, 2 * np.pi)
    else:
        lambdas = lon
    lambdas = np.array(lambdas)

    # Make longitude -pi:pi but make sure pi -> pi and not -pi
    inds = lambdas == np.pi
    lambdas = np.mod(lambdas + np.pi, 2 * np.pi) - np.pi
    lambdas[inds] = np.pi

    # hammer transform
    norm = np.sqrt(1 + np.cos(lat) * np.cos(lambdas * 0.5))
    hx = 2 * np.cos(lat) * np.sin(lambdas * 0.5) / norm
    hy = np.sin(lat) / norm

    return hx, hy

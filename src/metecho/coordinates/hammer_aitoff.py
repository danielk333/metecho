import numpy as np


def ecliptic_to_hammer(lon, lat, sun_lon=None, radians=False):
    if not radians:
        lon = np.radians(lon)
        lat = np.radians(lat)
        if sun_lon is not None:
            sun_lon = np.radians(sun_lon)

    if sun_lon is not None:
        # sun centered 
        lambdas = np.mod(np.mod(-(lon - sun_lon - 1.5*np.pi), 2*np.pi) + 2*np.pi, 2*np.pi)
    else:
        lambdas = lon
    lambdas = np.array(lambdas)

    # Make longitude -pi:pi but make sure pi -> pi and not -pi
    inds = lambdas == np.pi
    lambdas = np.mod(lambdas + np.pi, 2*np.pi) - np.pi
    if len(lambdas.shape) == 0:
        if inds:
            lambdas = np.pi
    else:
        lambdas[inds] = np.pi

    # hammer transform
    norm = np.sqrt(1 + np.cos(lat)*np.cos(lambdas*0.5))
    hx = 2*np.cos(lat)*np.sin(lambdas*0.5)/norm
    hy = np.sin(lat)/norm

    return hx, hy

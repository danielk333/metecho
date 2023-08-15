import numpy as np
import astropy.units as units
from astropy.coordinates import EarthLocation


def ecef_to_enu(lat, lon, degrees=True):
    """ECEF coordinate system to local ENU (east,north,up), not including translation.

    :param float lat: Latitude on the ellipsoid
    :param float lon: Longitude on the ellipsoid
    :param numpy.ndarray ecef: (3,n) array x,y and z coordinates in ECEF.
    :param bool radians: If :code:`True` then all values are given in radians instead of degrees.
    :rtype: numpy.ndarray
    :return: (3,3) rotation matrix.
    """
    mx = enu_to_ecef(lat, lon, degrees=degrees)
    return np.linalg.inv(mx)


def enu_to_ecef(lat, lon, degrees=True):
    """ENU (east/north/up) to ECEF coordinate system conversion, not including translation.

    :param float lat: Latitude on the ellipsoid
    :param float lon: Longitude on the ellipsoid
    :param bool radians: If :code:`True` then all values are given in radians instead of degrees.
    :rtype: numpy.ndarray
    :return: (3,3) rotation matrix.
    """
    if degrees:
        lat, lon = np.radians(lat), np.radians(lon)

    mx = np.array(
        [
            [-np.sin(lon), -np.sin(lat) * np.cos(lon), np.cos(lat) * np.cos(lon)],
            [np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat) * np.sin(lon)],
            [0, np.cos(lat), np.sin(lat)],
        ]
    )
    return mx


def geodetic_to_ITRS(lat, lon, alt, degrees=True, ellipsoid=None):
    """Use `astropy.coordinates.EarthLocation` to transform from geodetic to ITRS."""

    if degrees:
        lat, lon = np.radians(lat), np.radians(lon)

    cord = EarthLocation.from_geodetic(
        lon=lon * units.rad,
        lat=lat * units.rad,
        height=alt * units.m,
        ellipsoid=ellipsoid,
    )
    x, y, z = cord.to_geocentric()

    pos = np.empty((3,), dtype=np.float64)

    pos[0] = x.to(units.m).value
    pos[1] = y.to(units.m).value
    pos[2] = z.to(units.m).value

    return pos


def ITRS_to_geodetic(x, y, z, degrees=True, ellipsoid=None):
    """Use `astropy.coordinates.EarthLocation` to transform from geodetic to ITRS.

    :param float x: X-coordinate in ITRS
    :param float y: Y-coordinate in ITRS
    :param float z: Z-coordinate in ITRS
    :param bool radians: If :code:`True` then all values are given in radians instead of degrees.
    :param str/None ellipsoid: Name of the ellipsoid model used for geodetic
    coordinates, for default value see Astropy `EarthLocation`.
    :rtype: numpy.ndarray
    :return: (3,) array of longitude, latitude and height above ellipsoid
    """

    cord = EarthLocation.from_geocentric(
        x=x * units.m,
        y=y * units.m,
        z=z * units.m,
    )
    lon, lat, height = cord.to_geodetic(ellipsoid=ellipsoid)

    llh = np.empty((3,), dtype=np.float64)

    if degrees:
        u_ = units.deg
    else:
        u_ = units.rad
    llh[0] = lat.to(u_).value
    llh[1] = lon.to(u_).value
    llh[2] = height.to(units.m).value

    return llh

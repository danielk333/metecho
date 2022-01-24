
import logging

logger = logging.getLogger(__name__)

logger.debug('Importing astropy')
try:
    import astropy
except ImportError:
    astropy = None

if astropy is not None:
    import astropy.coordinates as coords
    from astropy.time import Time, TimeDelta
    import astropy.units as units


def local(t, epoch, ra, dec, lon, lat, height=0.0):
    '''Calculate the local coordinates and velocity of meteor shower radiant,
    including velocity shift due to Earth rotation rate.

    Args:
        t (numpy.ndarray): Time in seconds relative the epoch at which to evaluate the radiant.
        epoch (astropy.time.Time, float): If not given as `astropy.time.Time` instance, 
            Epoch is treated as an UTC fractional Modified Julian Date
        lon (float): Longitude in degrees of the local observer
        lat (float): Latitude in degrees of the local observer
        ra (float): Right ascension in degrees of the meteor shower radiant in J2000 GCRS coordinates
        dec (float): Declination in degrees of the meteor shower radiant in J2000 GCRS coordinates
        vel (float): Geocentric velocity in meters per second of the meteor shower radiant
        lat (height, optional): Height in meters above the ellipsoid of the local observer, defaults to `0`
        **kwargs: All additional keyword arguments are passed on to the `RawDataInterface` instantiation.


    '''
    if astropy is None:
        raise ImportError('astropy import failed, install extras to use this function')

    if not isinstance(epoch, Time):
        epoch = Time(epoch, format='mjd', scale='utc')
    times = epoch + TimeDelta(t, format='sec')

    observer = coords.EarthLocation.from_geodetic(
        lon=lon*units.deg,
        lat=lat*units.deg,
        height=height*units.m,
        ellipsoid = None,
    )

    local = coords.AltAz(
        obstime = times,
        location = observer,
    )

    radiant = coords.SkyCoord(
        ra*units.deg, 
        dec*units.deg, 
        frame='gcrs'
    )

    return radiant.transform_to(local)

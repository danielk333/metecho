import logging
import pathlib
import requests

logger = logging.getLogger(__name__)

logger.debug('Importing astropy')
try:
    import astropy
except ImportError:
    astropy = None

if astropy is not None:
    from astropy.coordinates import EarthLocation, AltAz, SkyCoord
    from astropy.time import Time
    import astropy.units as units

import numpy as np
import pandas

IAU_SHOWER_URL = 'http://www.ta3.sk/IAUC22DB/MDC2007/Etc/streamfulldata.txt'
IAU_DEFAULT_LOCATION = pathlib.Path.home() / 'tmp' / 'iau_meteoroid_stream_data.txt'


def download_streams(target_path=None):
    logger.info('Downloading IAU meteoroid streams list...')

    if target_path is None:
        if not IAU_DEFAULT_LOCATION.parent.is_dir():
            IAU_DEFAULT_LOCATION.parent.mkdir()
        target_path = IAU_DEFAULT_LOCATION

    data = requests.get(IAU_SHOWER_URL, allow_redirects=True).text

    with open(target_path, 'w') as fh:
        fh.write(data)

    return target_path


def read_streams_data(path):
    # discover file format
    lines = []
    with open(path, 'r') as fh:
        last_row = 0
        for line in fh:
            lines.append(line.strip())
            last_row += 1
            if len(line) > 0 and line.startswith('+'):
                break

        names = lines[-3][1:].split('  ')
        names = [x.strip() for x in names if len(x) > 0]

    meta = '\n'.join(lines)

    data = pandas.read_csv(path, sep="|", names=names, skiprows=last_row)

    # Convert certain columns to numeric
    conv = [
        's', 'LaSun', 'Ra', 'De', 'dRa', 
        'dDe', 'Vg', 'a', 'q', 'e', 'peri', 
        'node', 'inc', 'N', 'Group', 'CG', 
    ]
    for key in conv:
        if key not in data.columns:
            continue
        data[key] = pandas.to_numeric(data[key], errors='coerce')

    return data, meta


def get_streams_data(path = None):
    if path is None:
        path = IAU_DEFAULT_LOCATION
    if not path.is_file():
        download_streams(target_path=path)
    return read_streams_data(path)


def local_radiant():
    if astropy is None:
        raise ImportError('astropy import failed, cannot ')

    cord = EarthLocation.from_geodetic(
        lon=19*units.deg, 
        lat=69*units.deg, 
        height=200*units.m,
        ellipsoid = None,
    )
    x0 = cord.get_itrs(Time('1980-01-02')).cartesian.xyz.to(units.m).value
    x1 = np.array([x.to(units.m).value for x in cord.to_geocentric()])
    print(type(x0), x0.shape)
    print(x0)
    print(x1)
    print(x0-x1)

    locale = EarthLocation(lat=0*units.degree, lon=90*units.degree, height=0*units.m)
    altaz_cord = AltAz(location=locale, obstime=Time('J2000'))
    point = SkyCoord(az=90*units.degree, alt=0*units.degree, frame=altaz_cord)

    print(locale)
    print(altaz_cord)
    print(point)
    print(point.itrs)
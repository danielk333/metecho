import logging
import pathlib
import requests

try:
    import pandas
except ImportError:
    pandas = None

logger = logging.getLogger(__name__)

IAU_SHOWER_URL = 'http://www.ta3.sk/IAUC22DB/MDC2007/Etc/streamfulldata.txt'
IAU_DEFAULT_LOCATION = pathlib.Path.home() / 'tmp' / 'iau_meteoroid_stream_data.txt'


def download_streams(target_path=None):
    logger.info('Downloading IAU meteoroid streams list...')

    if target_path is None:
        target_path = IAU_DEFAULT_LOCATION
    if not target_path.parent.is_dir():
        target_path.parent.mkdir(exist_ok=True, parents=True)
    
    data = requests.get(IAU_SHOWER_URL, allow_redirects=True).text

    with open(target_path, 'w') as fh:
        fh.write(data)

    return target_path


def read_streams_data(path):
    '''
    '''
    if pandas is None:
        raise ImportError('pandas import failed, install extras to use this function')

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
    strip = [
        'shower name', 'Code', 'activity', 
        'Parent body', 'Ote', 'LT', 
    ]
    for key in conv:
        if key not in data.columns:
            continue
        data[key] = pandas.to_numeric(data[key], errors='coerce')

    for key in strip:
        if key not in data.columns:
            continue
        data[key] = data[key].str.strip()

    return data, meta


def get_streams_data(path = None):
    if path is None:
        path = IAU_DEFAULT_LOCATION
    if not path.is_file():
        download_streams(target_path=path)
    return read_streams_data(path)

import pathlib
import logging
import sys

import metecho

if len(sys.argv) < 3:
    raise RuntimeError('Need path to a MUI file and output to perform conversion')

in_path = pathlib.Path(sys.argv[1])
out_path = pathlib.Path(sys.argv[2])

if not out_path.is_dir():
    raise ValueError(f'Output path "{out_path}" is not a directory or does not exist')

if not in_path.is_file():
    raise ValueError(f'Input path "{in_path}" does not exist')

handler = logging.StreamHandler(sys.stdout)

for name in logging.root.manager.loggerDict:
    if name.startswith('metecho'):
        print(f'logger: {name}')

logger = logging.getLogger('metecho')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

metecho.profiler.enable('metecho')

files = metecho.data.mu.convert_MUI_to_h5(
    [in_path], 
    output_location = str(out_path),
    skip_existing = False,
)

for file in files:
    logger.info(f'"{file}" created')

print(metecho.profiler)

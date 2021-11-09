import pathlib
import logging
import sys

import matplotlib.pyplot as plt

import metecho

handler = logging.StreamHandler(sys.stdout)

for name in logging.root.manager.loggerDict:
    if name.startswith('metecho'):
        print(f'logger: {name}')

logger = logging.getLogger('metecho')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


base_path = pathlib.Path('/home/danielk/IRF/data/MU_TEST_DATA_SET/MUI/')

h5_mu_file = base_path / '2009/06/27/2009-06-27T09.54.05.690000000.h5'

if not h5_mu_file.is_file():
    files = metecho.data.mu.convert_MUI_to_h5(
        [base_path / 'MUI.090627.095404'], 
        output_location = str(base_path),
        skip_existing = False,
    )

    print(files)


raw = metecho.data.RawDataInterface(h5_mu_file)

metecho.plot.rti(raw, output_path=base_path / f'2009/06/27/{".".join(raw.path.name.split(".")[:-1]) + ".png"}')

plt.show()
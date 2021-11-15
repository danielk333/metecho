import pathlib
import logging
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import metecho
import metecho.generalized_matched_filter as mgmf

metecho.profiler.init('full', True)
metecho.profiler.start('full')


handler = logging.StreamHandler(sys.stdout)

for name in logging.root.manager.loggerDict:
    if name.startswith('metecho'):
        print(f'logger: {name}')

logger = logging.getLogger('metecho')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

metecho.profiler.enable('metecho')

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
raw.data = raw.data[:,:,100:101]

transmitted_waveform = mgmf.signal_model.barker_code_13(1, oversampling=2)

matched_filter_output = mgmf.xcorr.xcorr_echo_search(
    raw,
    -35e3,
    100e3,
    100.0,
    transmitted_waveform,
)

metecho.profiler.stop('full')
print(metecho.profiler)

metecho.plot.gmf(np.squeeze(matched_filter_output))

plt.show()
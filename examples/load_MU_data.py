'''
Load MU radar data
===================
'''
import pathlib
import logging
import sys

import matplotlib.pyplot as plt

import metecho

try:
    HERE = pathlib.Path(__file__).parent.resolve()
except NameError:
    HERE = pathlib.Path('.').parent.resolve()

handler = logging.StreamHandler(sys.stdout)

for name in logging.root.manager.loggerDict:
    if name.startswith('metecho'):
        print(f'logger: {name}')

logger = logging.getLogger('metecho')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

metecho.profiler.enable('metecho')

h5_mu_file = HERE / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'

raw = metecho.data.RawDataInterface(h5_mu_file)

print(metecho.profiler)

metecho.plot.rti(raw, log=True)

plt.show()

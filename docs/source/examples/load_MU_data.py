'''
Load MU radar data
===================
'''
import pathlib
import matplotlib.pyplot as plt

import metecho

try:
    HERE = pathlib.Path(__file__).parent.resolve()
except NameError:
    HERE = pathlib.Path('.').parent.resolve()


h5_mu_file = HERE / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'

raw = metecho.data.RawDataInterface(h5_mu_file)

metecho.plot.rti(raw, log=True)

plt.show()

'''
Running a matched filter
=========================
'''

import pathlib
import matplotlib.pyplot as plt

import metecho
import metecho.generalized_matched_filter as mgmf

try:
    HERE = pathlib.Path(__file__).parent.resolve()
except NameError:
    HERE = pathlib.Path('.').parent.resolve()

h5_mu_file = HERE / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'

raw = metecho.data.RawDataInterface(h5_mu_file)

transmitted_waveform = metecho.signal_model.phase_coding.barker_code_13(raw.data.shape[raw.axis["pulse"]], oversampling=2)

matched_filter_output = mgmf.xcorr.xcorr_echo_search(
    raw,
    -35e3,
    100e3,
    100.0,
    transmitted_waveform,
    full_gmf_output=True
)


fig = plt.figure(figsize=(12, 8))
spec = fig.add_gridspec(3, 2)
axes = [
    fig.add_subplot(spec[ind, 0])
    for ind in range(3)
]
ax = fig.add_subplot(spec[:, 1])

metecho.plot.rti(raw, log=True, index_axis=True, ax=ax)
metecho.plot.gmf(matched_filter_output, ax=axes)

plt.show()

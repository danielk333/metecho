"""
Load MU radar data
===================
"""
import pathlib
import numpy as np
import matplotlib.pyplot as plt
import scipy.constants
import pickle

import metecho
import metecho.generalized_matched_filter as mgmf


# path = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/manda_zenith_4.00v_CP@vhf/20230815_15/19580750.mat.bz2")
# file = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/analysis/19580750.mat_gmf.pickle")

path = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/manda_zenith_4.00v_CP@vhf/20230815_15/19580942.mat.bz2")
file = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/analysis/19580942.mat_gmf.pickle")


raw = metecho.data.RawDataInterface(
    path,
    backend="eiscat_vhf_matlab",
)

with open(file, "rb") as f:
    matched_filter_output = pickle.load(f)

fig = plt.figure(figsize=(12, 8))
spec = fig.add_gridspec(3, 2)
axes = [
    fig.add_subplot(spec[ind, 0])
    for ind in range(3)
]
ax = fig.add_subplot(spec[:, 1])

metecho.plot.rti(raw, log=True, index_axis=False, ax=ax)
metecho.plot.gmf(np.arange(700), matched_filter_output, raw.meta, ax=axes, index_axis=False)

plt.show()

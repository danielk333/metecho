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

clobber = False
out_path = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/analysis")
par_file = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/manda_zenith_4.00v_CP@vhf_information/20230815/145628/manda_va.par")

# paths = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/manda_zenith_4.00v_CP@vhf/20230815_15").glob("*.mat*")
# paths = list(paths)

base_path = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/manda_zenith_4.00v_CP@vhf/20230815_15")
paths = [
    "19581412.mat.bz2",
    "19580942.mat.bz2",
    "19580750.mat.bz2",
    "19580990.mat.bz2",
    "19581192.mat.bz2",
    "19581859.mat.bz2",
    "19581859.mat.bz2",
]
paths = [base_path / pth for pth in paths]


freq = 223.4e6
min_v = -100e3
max_v = 30e3
min_doppler = (min_v/scipy.constants.c)*freq
max_doppler = (max_v/scipy.constants.c)*freq
steps_doppler = 2000
step_doppler = (max_doppler - min_doppler)/steps_doppler
print("Doppler limits:")
print(min_doppler, max_doppler, step_doppler)

for file in paths:
    print(file)
    gmf_output = out_path / f"{file.stem}_gmf.pickle"
    if gmf_output.exists() and not clobber:
        continue

    raw = metecho.data.RawDataInterface(
        file,
        backend="eiscat_vhf_matlab",
        par_file=par_file,
    )

    raw_plot = out_path / f"{file.stem}_raw.png"
    if not raw_plot.exists() or clobber:
        fig, ax = plt.subplots(figsize=(12, 8))
        metecho.plot.rti(raw, log=True, index_axis=False, ax=ax)
        fig.savefig(raw_plot)
        plt.close(fig)

    codes = np.tile(raw.meta["code"], (int(raw.data.shape[2]//raw.meta["code"].shape[0]), 1))

    matched_filter_output = mgmf.xcorr.xcorr_echo_search(
        raw,
        min_doppler,
        max_doppler,
        step_doppler,
        codes,
        full_gmf_output=False,
        threads=6,
    )
    if not gmf_output.exists() or clobber:
        with open(gmf_output, "wb") as f:
            pickle.dump(matched_filter_output, f)

    gmf_plot = out_path / f"{file.stem}_gmf.png"
    if not gmf_plot.exists() or clobber:
        fig = plt.figure(figsize=(12, 8))
        spec = fig.add_gridspec(3, 2)
        axes = [
            fig.add_subplot(spec[ind, 0])
            for ind in range(3)
        ]
        ax = fig.add_subplot(spec[:, 1])

        metecho.plot.rti(raw, log=True, index_axis=False, ax=ax)
        metecho.plot.gmf(np.arange(raw.data.shape[2]), matched_filter_output, raw.meta, index_axis=False, ax=axes)

        fig.savefig(gmf_plot)
        plt.close(fig)

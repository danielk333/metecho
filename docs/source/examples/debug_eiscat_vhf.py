"""
Load MU radar data
===================
"""
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
]
paths = [base_path / pth for pth in paths]

pulse = 20
code_offset = 10

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
    raw = metecho.data.RawDataInterface(
        file,
        backend="eiscat_vhf_matlab",
        par_file=par_file,
    )
    codes = np.tile(raw.meta["code"], (int(raw.data.shape[2]//raw.meta["code"].shape[0]), 1))

    raw.data = raw.data[:, :, pulse:(pulse + 1)]

    outputs = []    
    for offset in range(code_offset):
        _code = codes[(pulse - offset):(pulse - offset + 1), :]
        matched_filter_output = mgmf.xcorr.xcorr_echo_search(
            raw,
            min_doppler,
            max_doppler,
            step_doppler,
            _code,
            full_gmf_output=False,
        )
        outputs.append(matched_filter_output)
    
    Tipp = raw.meta["T_ipp"]
    Ts = raw.meta["T_measure_start"]
    fs = raw.meta["frequency"]
    Tsmp = raw.meta['T_samp']

    gmf_o = []
    for ambig, out in enumerate(outputs):
        r = (out["best_start"]*Tsmp + Ts + Tipp*ambig)*0.5*scipy.constants.c*1e-3
        v = (out["best_doppler"]/fs)*scipy.constants.c*1e-3
        gmf_o.append([np.abs(out["best_peak"]), r, v])
    gmf_o = np.array(gmf_o)

    fig, axes = plt.subplots(3, 1, sharex="all")
    axes[0].plot(-np.arange(code_offset), gmf_o[:, 0, 0])
    axes[0].set_ylabel("GMF peak [1]")
    axes[1].plot(-np.arange(code_offset), gmf_o[:, 1, 0])
    axes[1].set_ylabel("True r [km]")
    axes[2].plot(-np.arange(code_offset), gmf_o[:, 2, 0])
    axes[2].set_ylabel("LOS v [km/s]")

    r = gmf_o[2, 1, 0]
    v = gmf_o[2, 2, 0]
    fig.suptitle(f"Analysis using previous radar codes: r={r:.1f} km, dop={v:.1f} km/s")

    axes[2].set_xlabel("Range ambiguity")












# import pathlib
# import numpy as np
# import matplotlib.pyplot as plt
# import scipy.constants
# import pickle

# import metecho
# import metecho.generalized_matched_filter as mgmf

# clobber = True
# out_path = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/analysis")
# par_file = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/manda_zenith_4.00v_CP@vhf_information/20230815/145628/manda_va.par")
# # paths = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/manda_zenith_4.00v_CP@vhf/20230815_15").glob("*.mat*")
# # paths = list(paths)
# # file = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/manda_zenith_4.00v_CP@vhf/20230815_15/19580750.mat.bz2")
# file = pathlib.Path("/home/danielk/data/EISCAT/radar-school-2023/manda_zenith_4.00v_CP@vhf/20230815_15/19580942.mat.bz2")

# freq = 223.4e6
# min_v = -100e3
# max_v = 100e3
# min_doppler = (min_v/scipy.constants.c)*freq
# max_doppler = (max_v/scipy.constants.c)*freq
# steps_doppler = 2000
# step_doppler = (max_doppler - min_doppler)/steps_doppler
# print(min_doppler, max_doppler, step_doppler)

# raw = metecho.data.RawDataInterface(
#     file,
#     backend="eiscat_vhf_matlab",
#     par_file=par_file,
# )
# metecho.plot.rti(raw, log=True, index_axis=True)

# T_ipp = raw.meta["T_ipp"]
# T_meas = raw.meta["T_measure"]
# T_start = raw.meta["T_measure_start"]

# ambigs = np.arange(5)
# for ambig in ambigs:
#     r0 = (T_start + T_ipp*ambig)*0.5e-3*scipy.constants.c
#     r1 = (T_start + T_ipp*ambig + T_meas)*0.5e-3*scipy.constants.c
#     print(f"Range interval {ambig}: {int(r0)} km -> {int(r1)} km")

# exit()

# codes = np.tile(raw.meta["code"], (int(raw.data.shape[2]//raw.meta["code"].shape[0]), 1))
# code_ids = np.tile(np.arange(raw.meta["code"].shape[0]), (int(raw.data.shape[2]//raw.meta["code"].shape[0]), 1)).flatten()

# # cut to speed up
# # raw.data = raw.data[:, :, 2190:2192]
# # codes = codes[2190:2192, :]
# raw.data = raw.data[:, :, 2616:2617]
# codes = codes[2616:2617, :]

# matched_filter_output = mgmf.xcorr.xcorr_echo_search(
#     raw,
#     min_doppler,
#     max_doppler,
#     step_doppler,
#     codes,
#     full_gmf_output=True,
# )
# gmf_o = matched_filter_output["gmf_output"]
# # fig, ax = plt.subplots()
# # ax.pcolormesh(np.log10(np.abs(gmf_o[:,:,0]))*10)
# # plt.show()
# # code 73
# # but it should be 56

# fig = plt.figure(figsize=(12, 8))
# spec = fig.add_gridspec(3, 2)
# axes = [
#     fig.add_subplot(spec[ind, 0])
#     for ind in range(3)
# ]
# ax = fig.add_subplot(spec[:, 1])

# metecho.plot.rti(raw, log=True, index_axis=True, ax=ax)
# metecho.plot.gmf(matched_filter_output, ax=axes)

# gmf_o = matched_filter_output["gmf_output"]
# fig, ax = plt.subplots()
# gmf_val = np.abs(gmf_o[:,:,0])
# ax.pcolormesh(gmf_val)

# dop_maxes = np.max(gmf_val, axis=1)
# print(len(dop_maxes))
# best_dop_ind = np.argmax(dop_maxes)

# fig, ax = plt.subplots()
# ax.plot(np.abs(gmf_val[best_dop_ind, :]))

# plt.show()
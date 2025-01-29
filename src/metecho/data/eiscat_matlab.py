import logging
import bz2

import numpy as np
import scipy.io as sio

from . import raw_data

logger = logging.getLogger(__name__)


@raw_data.backend_validator("eiscat_vhf_matlab")
def validate_matlab(path):
    return path.name.endswith(".mat.bz2")


@raw_data.backend_loader("eiscat_vhf_matlab")
def load_matlab(path, declutter=150, par_file=None, tlan_file=None):
    # TODO: read this from tlan and par files
    meta = {}

    dat = sio.loadmat(bz2.open(path))
    raw = dat["d_raw"]
    ch1 = raw[:len(raw)//2]
    ch2 = raw[len(raw)//2:]

    # tx1 = ch1[:32768]
    # tx2 = ch2[:32768]

    rx1 = ch1[32768:]
    rx2 = ch2[32768:]

    # import matplotlib.pyplot as plt
    # fig, axes = plt.subplots(2,1)
    # axes[0].plot(np.real(tx1[0:1080]), '-b')
    # axes[0].plot(np.imag(tx1[0:1080]), '--b')

    # axes[1].plot(np.real(rx1[0:1080]), '-b')
    # axes[1].plot(np.imag(rx1[0:1080]), '--b')
    # plt.show()

    rx = rx1 + rx2

    samples_per_pulse = 942
    pulses = len(rx1)//samples_per_pulse

    data = np.empty((1, samples_per_pulse, pulses), dtype=np.complex64)
    offset = 0
    for ind in range(pulses):
        data[0, :, ind] = rx[offset:(offset + samples_per_pulse), 0]
        offset += samples_per_pulse

    meta["T_samp"] = 1.2e-6
    meta["T_ipp"] = 1.5e-3
    meta["T_measure"] = (samples_per_pulse - declutter)*meta["T_samp"]
    meta["T_measure_start"] = 343e-6 - 73e-6 + declutter*meta["T_samp"]
    meta["frequency"] = 223.4e6
    meta["file_start"] = None
    meta["file_stop"] = None

    code = None
    if par_file is not None:
        code_nr = 128
        code_len = 61
        code = np.empty((code_nr*code_len,), dtype=np.float64)
        with open(par_file, "r") as f:
            for lineno, line in enumerate(f.readlines()):
                if lineno < 24:
                    continue
                code[lineno - 24] = float(line.strip())
            code = code.reshape(code_nr, code_len, order="C")
        code = np.kron(code, np.ones(2))

    meta["code"] = code
    meta["filename"] = str(path)

    data = data[:, declutter:, :].astype(np.complex128)
    return data, {"channel": 0, "sample": 1, "pulse": 2}, meta

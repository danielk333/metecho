import matplotlib.pyplot as plt
import h5py
import logging
import numpy as np

logger = logging.getLogger(__name__)


def rti(filepath, output_filepath=""):
    """
    Simple function to check the data. Filepath needs a h5 file.
    """
    try:
        h5file = h5py.File(filepath, 'r')
    except FileNotFoundError:
        logger.exception(f'Could not open file: {filepath}. File does not exist.')
        return

    dset = h5file["data"]
    powsum = np.abs(np.sum(dset, axis=0))**2
    """
    Sets pyplot to classic rendering, then renders the powersum unto it. We then add
    a colorbar and the y and x-label before saving it. At the moment it only saves
    to plot.png.
    """
    plt.style.use('classic')
    plt.pcolormesh(powsum)
    plt.colorbar()
    plt.ylabel('signal strength')
    plt.xlabel('time')
    plt.savefig(output_filepath + 'plot.png')
    plt.close('all')

import matplotlib.pyplot as plt
import h5py
import logging
import numpy as np

logger = logging.getLogger(__name__)


def rti(file,
        output_filepath="",
        axis_font_size=8,
        title_font_size=12,
        tick_font_size=12,
        title='',
        index_axis=1,
        ):
    """
    Simple function to plot the information of a h5-file.
    """
    try:
        logger.debug(f'Opening file {file}')
        h5file = h5py.File(file, 'r')
    except FileNotFoundError:
        logger.exception(f'Could not open file: {file}. File does not exist.')
        return

    """
    File opened, starting to set pyplot settings. Starting with closing the other pyplots as to not render
    over anything else
    """
    plt.close('all')
    dset = h5file["data"]
    powsum = np.abs(np.sum(dset, axis=0))**2

    """
    Sets pyplot to classic rendering, then renders the powersum unto it. We then add
    a colorbar and the y and x-label before saving it. At the moment it only saves
    to plot.png.
    """
    plt.pcolormesh(powsum)

    if index_axis:
        plt.xlabel('IPP [1]', fontsize=axis_font_size)
        plt.ylabel('Sample [1]', fontsize=axis_font_size)
    else:
        plt.xlabel('$t$ [s]', fontsize=axis_font_size)
        plt.ylabel('$h$ [km]', fontsize=axis_font_size)

    if title == '':
        # Uppdatera när jag vet hur jag ska stoppa in radarnamnet
        title = f'{h5file.attrs["filename"]} - {h5file.attrs["record_start_time"]}'

    plt.suptitle(title, fontsize=title_font_size)
    plt.colorbar(label='Power [1]')
    plt.xticks(fontsize=tick_font_size)
    plt.yticks(fontsize=tick_font_size)

    plt.savefig(output_filepath + title.replace(':', '.') + '.png')
    plt.close('all')

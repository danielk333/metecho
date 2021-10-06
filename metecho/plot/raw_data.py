import matplotlib.pyplot as plt
import h5py
import logging
import numpy as np
import sys

from .general import basic_matplotlib_kw

logger = logging.getLogger(__name__)

@basic_matplotlib_kw
def rti(ax,
        raw_data,
        axis_font_size=15,
        title_font_size=11,
        tick_font_size=11,
        title='',
        index_axis=1,
        ):
    """
    Simple function to plot the information of a h5-file.
    """


    """
    File opened, starting to set pyplot settings. Presuming that the user doesn't have any other
    pyplots open.
    """
    summed = raw_data.data
    for axis in ['channel', 'polarization']:
        if raw_data.axis[axis] is not None:
            summed = np.sum(summed, axis=raw_data.axis[axis])

    powsum = np.abs(summed)**2

    """
    Sets pyplot to classic rendering, then renders the powersum unto it. We then add
    a colorbar and the y and x-label before saving it. At the moment it only saves
    to plot.png.
    """

    pmesh = ax.pcolormesh(powsum)

    if index_axis:
        ax.set_xlabel('IPP [1]', fontsize=axis_font_size)
        ax.set_ylabel('Sample [1]', fontsize=axis_font_size)
    else:
        ax.set_xlabel('$t$ [s]', fontsize=axis_font_size)
        ax.set_ylabel('$h$ [km]', fontsize=axis_font_size)

    if title == '':
        # Uppdatera när jag vet hur jag ska stoppa in radarnamnet
        title = f'{raw_data.path.name} - {raw_data.meta.get("start_time", "")}'

    ax.set_title(title, fontsize=title_font_size)
    cbar = plt.colorbar(pmesh)
    cbar.set_label('Power [1]', size=axis_font_size)
    cbar.ax.tick_params(labelsize=tick_font_size)

    for ax_label in ['x', 'y']:
        ax.tick_params(axis=ax_label, labelsize=tick_font_size)

    return ax
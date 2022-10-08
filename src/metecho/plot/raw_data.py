import matplotlib.pyplot as plt
import logging
import numpy as np
import copy
import scipy.constants as constants

from .general import basic_matplotlib_kw

logger = logging.getLogger(__name__)


@basic_matplotlib_kw(subplot_shape=None)
def rti(ax,
        raw_data,
        axis_font_size=15,
        title_font_size=11,
        tick_font_size=11,
        title='',
        index_axis=True,
        log=False,
        colorbar=True,
        pcolormesh_kw={},
        ):
    """
    Simple function to plot the range-time intensity information of complex raw voltage data.
    """

    """
    File opened, starting to set pyplot settings. Presuming that the user doesn't have any other
    pyplots open.
    """
    summed = raw_data.data
    remove_axis = copy.deepcopy(raw_data.DATA_AXIS)
    remove_axis.remove('sample')
    remove_axis.remove('pulse')
    for axis in remove_axis:
        if raw_data.axis[axis] is not None:
            summed = np.sum(summed, axis=raw_data.axis[axis])

    powsum = np.log10(np.abs(summed)**2) if log else np.abs(summed)**2

    """
    Sets pyplot to classic rendering, then renders the powersum unto it. We then add
    a colorbar and the y and x-label before saving it. At the moment it only saves
    to plot.png.
    """

    if index_axis:
        X, Y = np.meshgrid(
            np.arange(summed.shape[1]), 
            np.arange(summed.shape[0]),
        )
        ax.set_xlabel('IPP', fontsize=axis_font_size)
        ax.set_ylabel('Sample', fontsize=axis_font_size)
    else:
        X, Y = np.meshgrid(
            np.arange(summed.shape[1])*raw_data.meta['T_ipp'],
            0.5e-3*(np.arange(summed.shape[0])*raw_data.meta['T_samp'] + raw_data.meta['T_measure_start'])*constants.c,
        )
        ax.set_xlabel('Time [s]', fontsize=axis_font_size)
        ax.set_ylabel('Range [km]', fontsize=axis_font_size)

    pmesh = ax.pcolormesh(X, Y, powsum, **pcolormesh_kw)

    if title == '':
        # Uppdatera när jag vet hur jag ska stoppa in radarnamnet
        title = f'{raw_data.path.name} - {raw_data.meta.get("start_time", "")}'

    ax.set_title(title, fontsize=title_font_size)
    if colorbar:
        cbar = plt.colorbar(pmesh, ax=ax)
        cbar.set_label('Power [arbitrary units]', size=axis_font_size)
        cbar.ax.tick_params(labelsize=tick_font_size)

    for ax_label in ['x', 'y']:
        ax.tick_params(axis=ax_label, labelsize=tick_font_size)

    return ax, [pmesh]

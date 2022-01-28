import matplotlib.pyplot as plt
import h5py
import logging
import numpy as np
import sys
import copy

from .general import basic_matplotlib_kw

logger = logging.getLogger(__name__)


@basic_matplotlib_kw(subplot_shape=(3, 1))
def gmf(axes,
        filter_output,
        axis_font_size=15,
        title_font_size=11,
        tick_font_size=11,
        title='',
        index_axis=1,
        ):
    """
    Plots the GMF output that uses only doppler and delay
    """

    """
    if index_axis:
        ax.set_xlabel('Delay [1]', fontsize=axis_font_size)
        ax.set_ylabel('Doppler [1]', fontsize=axis_font_size)
    else:
        ax.set_xlabel('Range [km]', fontsize=axis_font_size)
        ax.set_ylabel('Velocity [km/s]', fontsize=axis_font_size)
    """

    axes[0].plot(filter_output["best_start"])
    axes[1].plot(filter_output["best_peak"])
    axes[2].plot(filter_output["best_doppler"])

    for ax in axes:
        ax.set_xlabel('IPP [1]', fontsize=axis_font_size)
        for ax_label in ['x', 'y']:
            ax.tick_params(axis=ax_label, labelsize=tick_font_size)

    if title == '':
        title = f'GMF output'

    axes[0].set_title(title, fontsize=title_font_size)
    """
    cbar = plt.colorbar(pmesh)
    cbar.set_label('Power [1]', size=axis_font_size)
    cbar.ax.tick_params(labelsize=tick_font_size)
    """

    return ax

import matplotlib.pyplot as plt
import scipy.constants
import h5py
import logging
import numpy as np
import sys
import copy

from .general import basic_matplotlib_kw

logger = logging.getLogger(__name__)


@basic_matplotlib_kw(subplot_shape=(3, 1))
def gmf(axes,
        ipps,
        filter_output,
        raw_data_meta,
        axis_font_size=15,
        title_font_size=11,
        tick_font_size=11,
        title='',
        index_axis=1,
        ):
    """
    Plots the GMF output that uses only doppler and delay
    """
    t_axis = ipps
    if index_axis:
        axes[0].plot(filter_output["best_start"])
        axes[2].plot(filter_output["best_doppler"])
        
        axes[0].set_ylabel("Start sample [1]")
        axes[2].set_ylabel("Doppler [Hz]")
    else:
        Tipp = raw_data_meta["T_ipp"]
        t_axis = t_axis.astype(np.float64)*Tipp
        Ts = raw_data_meta["T_measure_start"]
        fs = raw_data_meta["frequency"]
        Tsmp = raw_data_meta['T_samp']
        axes[0].plot(t_axis, (filter_output["best_start"]*Tsmp + Ts)*0.5*scipy.constants.c*1e-3)
        axes[2].plot(t_axis, (filter_output["best_doppler"]/fs)*scipy.constants.c*1e-3)

        axes[0].set_ylabel("Range [km]")
        axes[2].set_ylabel("Doppler [km/s]")

    axes[1].plot(t_axis, filter_output["best_peak"])
    axes[1].set_ylabel("GMF peak value [1]")

    for ax in axes:
        if index_axis:
            ax.set_xlabel('IPP [1]', fontsize=axis_font_size)
        else:
            ax.set_xlabel('IPP [s]', fontsize=axis_font_size)
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

    return ax, []

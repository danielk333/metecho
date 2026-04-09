import numpy.typing as npt
import pyorb


def gmf(axes: npt.NDArray, t: npt.NDArray, kep: npt.NDArray) -> None:
    """
    Args:
        axes: Axes to plot on
        t: Array of seconds, this will be the x-axis of each plot
        kep: TODO

    """

    axis_labels = [
        "$a$ [AU]",
        "$e$ [1]",
        "$i$ [deg]",
        "$\\omega$ [deg]",
        "$\\Omega$ [deg]",
        "$\\nu$ [deg]",
    ]
    scale = [1 / pyorb.AU] + [1] * 5

    axes = axes.flatten()
    for i in range(6):
        ax = axes[i]
        ax.plot(t / 3600.0, kep[i, :] * scale[i], "-b")
        ax.set_xlabel("Time [h]")
        ax.set_ylabel(axis_labels[i])

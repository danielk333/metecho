import pyorb

from .general import basic_matplotlib_kw


@basic_matplotlib_kw(subplot_shape=(2, 3))
def gmf(axes, t, kep):
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

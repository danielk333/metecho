from configparser import ConfigParser
from pathlib import Path
from typing import Optional

import hardtarget
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib.axes import Axes
from radardef.components import DataLoader

from metecho.events.types import Echo, Events


def plot_events(
    data: DataLoader,
    config: ConfigParser,
    echo: Echo,
    events: Events,
    save_as_image: bool = False,
    save_location: Optional[str | Path] = None,
) -> None:
    """
    Plot event detections along with the raw data.
    """

    # Calculate start and end sample of search
    start_samp = echo.ipp_offset * data.experiment.ipp_samps
    end_samp = echo.max_peak.shape[0] * data.experiment.ipp_samps + start_samp

    # Create a 3x3 grid that's 16 times 9 inches big
    fig, axs = plt.subplots(3, 3)
    fig.set_size_inches(16, 9)

    # Create a 2 by 1 plot and replace axis 2 and 3 with it.
    long_plot = axs[1, 0].get_gridspec()
    for ax in axs[0, 1:]:
        ax.remove()
    long_plot_ax = fig.add_subplot(long_plot[0, 1:])

    # Create title
    event_save = f"Events saved: {len(events.meteors)}" if len(events.meteors) > 0 else "No events found"
    fig.suptitle(
        f"{data.path.name}, Matches={len(events.meteor_indicies)}, \
        Non-transient coherent detection ({echo.doppler_coherrence}, {echo.start_coherrence}),\
        {event_save}",
        fontsize=18,
        fontweight="bold",
        wrap=True,
    )

    plot_highlight_match(
        axs[0, 0],
        events.meteor_indicies,
        np.abs(echo.max_peak),
        "IPP [1]",
        "Xcorr Match",
        config,
    )

    long_plot_ax, mesh = hardtarget.plotting.rti(
        long_plot_ax,
        data,
        start_time=start_samp * data.experiment.t_samp_usec,
        end_time=end_samp * data.experiment.t_samp_usec,
        relative_time=True,
        colorbar=False,
        log=True,
    )

    plot_highlight_match(
        axs[1, 0],
        events.meteor_indicies,
        echo.tot_pow,
        "IPP [1]",
        "Total Power",
        config,
    )
    plot_highlight_match(
        axs[1, 1],
        events.meteor_indicies,
        echo.start_std,
        "IPP [1]",
        "Range moving STD",
        config,
    )
    plot_highlight_match(
        axs[1, 2],
        events.meteor_indicies,
        echo.doppler_std,
        "IPP [1]",
        "Doppler shift moving STD",
        config,
    )

    # Create x-axis for each ipp
    pulse_ind = np.arange((end_samp - start_samp) / data.experiment.ipp_samps)

    axs[2, 0].plot(pulse_ind, events.detection_per_index)
    axs[2, 0].set_xlabel("IPP [1]")
    axs[2, 0].set_ylabel("Event Criteria met")

    plot_highlight_match(
        axs[2, 1],
        events.meteor_indicies,
        echo.max_pow_ind,
        "IPP [1]",
        "Range start",
        config,
    )
    plot_highlight_match(
        axs[2, 2],
        events.meteor_indicies,
        echo.best_doppler,
        "IPP [1]",
        "Doppler shift match",
        config,
    )

    # TODO: Can this be remade?
    start_ipps = [event.start_ipp for event in events.meteors]
    end_ipps = [event.end_ipp for event in events.meteors]

    colors = plt.cm.rainbow(np.linspace(0, 1, len(events.meteors)))

    for rows in axs:
        for ax in rows:
            for start, stop, color in zip(start_ipps, end_ipps, colors):
                ax.axvspan(start, stop, facecolor=color, alpha=0.4)

    for start, stop, color in zip(start_ipps, end_ipps, colors):
        long_plot_ax.axvspan(start, stop, facecolor=color, alpha=0.4)

    # fig.tight_layout()
    if save_as_image and save_location:
        save_location = Path(save_location)
        if "." in str(save_location):
            save_location = save_location.parent
        if not save_location.is_dir():
            save_location.mkdir(parents=True)
        save_location = save_location / (data.path.name + ".png")
        fig.savefig(save_location)

    plt.show()


def plot_highlight_match(
    ax: Axes, matches: npt.NDArray, data: npt.NDArray, xlabel: str, ylabel: str, config: ConfigParser
) -> Axes:
    """
    Takes a set a of data and plots it on a graph, then marks all the points with matches.
    """

    data_filt = np.zeros(len(data), dtype=bool)
    data_xaxis = np.arange(len(data))
    data_filt[matches] = True

    color_filter = []
    for ind in data_filt:
        if ind:
            color_filter.append(config["General"]["match_found"])
        else:
            color_filter.append(config["General"]["match_not_found"])
    ax.plot(data_xaxis, data)
    ax.scatter(data_xaxis, data, marker=".", c=color_filter)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)

    return ax

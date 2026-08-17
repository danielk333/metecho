import argparse
import logging
from pathlib import Path

from radardef.components import DataLoader
from radardef.radar_def import RadarDef
from radardef.tools.mpi_tools import get_mpi

from metecho.events import event_search
from metecho.plot import plot_events

from .commands import add_command

logger = logging.getLogger(__name__)


def main(args: argparse.Namespace) -> None:

    if args.plot_output:
        plot_save = True
        plot_output = Path(args.plot_output).resolve()
    else:
        plot_save = False
        plot_output = None

    comm = get_mpi()

    if comm.rank == 0:
        data = RadarDef().load_data(args.data)
    else:
        data = None

    data = comm.bcast(data, root=0)

    events, echo, noise = event_search(
        data,
        Path(args.config) if args.config else None,
        start_time=args.start_time,
        end_time=args.end_time,
        relative_time=args.relative_time,
        progress=args.progress,
        output=args.output,
        comm=comm,
    )

    comm.barrier()

    if args.plot and comm.rank == 0:
        plot_events(
            echo,
            events,
            data if isinstance(data, DataLoader) else None,
            plot_save,
            plot_output,
        )


def parser_build(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Adds mandatory and optional positional arguments to the parser."""

    parser.add_argument(
        "-Po",
        "--plot-output",
        default="",
        help="The location where you want to save event search plots",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="The directory to where you want to save events",
    )
    parser.add_argument(
        "-P",
        "--plot",
        action="store_true",
        help="Shows plots of the files as it runs. Warning: \
                        Currently it will pause upon each render which must be closed for it to continue.",
    )
    parser.add_argument(
        "-Ps",
        "--plot-save",
        action="store_true",
        help="Saves image to the output folder if set.",
    )
    parser.add_argument(
        "-q",
        "--sequential",
        action="store_true",
        help="Make sure raw data files are analyzed sequentially and events \
                        spanning multiple files are correctly identified.",
    )
    parser.add_argument(
        "-b",
        "--best_data",
        action="store_true",
        help="Stores best data in pickle if set.",
    )
    parser.add_argument("--config", default=None, type=str, help="path to event search config file, optional")
    parser.add_argument("-s", "--start_time", default=None, type=str)
    parser.add_argument("-e", "--end_time", default=None, type=str)
    parser.add_argument("--relative_time", action="store_true")
    parser.add_argument("-p", "--progress", action="store_true", help="enable progress bar")
    parser.add_argument("data", help="path to directory to analyse")
    return parser


add_command(
    name="event_search",
    function=main,
    parser_build=parser_build,
    # command_help="Searches radar data to look for signs of meteor events.",
)

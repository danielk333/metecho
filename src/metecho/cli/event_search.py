import argparse
import logging
from pathlib import Path

from hardtarget.process.process import DataLoader
from radardef.radar_def import RadarDef

from metecho.data_handling.store_events import store_events
from metecho.events import Events, event_search, generate_event_search_config
from metecho.plot import plot_events

from .. import tools
from .commands import add_command

logger = logging.getLogger(__name__)

try:
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
except ImportError:

    class COMM_WORLD:
        rank = 0
        size = 1

        def barrier(self) -> None:
            pass

    comm = COMM_WORLD()


@tools.MPI_target_arg(0)
def find_events(file: str | Path, args: argparse.Namespace) -> Events:

    config = generate_event_search_config(file_input=args.config)

    data_loader = RadarDef().load_data(file)

    data: DataLoader | Path
    if data_loader:
        data = data_loader
    else:
        data = Path(file)

    events, echo = event_search(
        data,
        config,
        start_time=int(args.start_time) if args.relative_time else args.start_time,
        end_time=int(args.end_time) if args.relative_time else args.end_time,
        relative_time=args.relative_time,
        progress=args.progress,
    )

    if args.plot:
        plot_events(
            echo,
            events,
            data if isinstance(data, DataLoader) else None,
            args.plot_save,
            args.plot_output,
        )

    return events


def main(args: argparse.Namespace) -> None:

    if args.plot_output:
        args.plot_save = True
        args.plot_output = Path(args.plot_output).resolve()

    # if save_results.is_dir():
    #    raise ValueError(f'Output results path "{save_results}" is a directory, not a file-path')

    events = find_events(args.files, args, MPI=comm.size > 1, MPI_root=0)

    if args.output:
        if comm.rank == 0:
            output_dir = Path(args.output).resolve()
            if not output_dir.exists():
                output_dir.mkdir(parents=True)

            for x in events:
                store_events(x, output_dir)

        comm.barrier()


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
    parser.add_argument(
        "files",
        nargs="+",
        help="Input the locations of the files (or folders) you want analyzed.",
    )
    return parser


add_command(
    name="event_search",
    function=main,
    parser_build=parser_build,
    # command_help="Searches radar data to look for signs of meteor events.",
)

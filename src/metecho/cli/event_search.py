import argparse
import logging
import os
import pickle
from pathlib import Path

from radardef.radar_def import RadarDef

from metecho.events.types import Events

from .. import events, tools
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

    config = events.generate_event_search_config()

    data = RadarDef().load_data(file)

    if not data:
        raise FileNotFoundError(f"Not possible to load {file}")

    return events.event_search(
        data,
        config,
        start_time=args.start_time,
        end_time=args.end_time,
        plot=args.plot,
        save_as_image=args.plot_save,
        save_location=args.plot_output,
    )


def main(args: argparse.Namespace) -> None:
    default_folder = Path(os.getcwd()) / "output"

    if len(args.output) == 0:
        args.output = default_folder / "events.pickle"
    if len(args.plot_output) == 0:
        args.plot_output = default_folder / "plots"
    else:
        args.plot_save = True
        args.plot_output = Path(args.plot_output).resolve()

    save_results = Path(args.output).resolve()
    if save_results.is_dir():
        raise ValueError(f'Output results path "{save_results}" is a directory, not a file-path')

    # paths = raw_data_file_list(output_dir, args)

    events = find_events(args.files, args, MPI=comm.size > 1, MPI_root=0)

    if comm.rank == 0:
        if not save_results.parent.exists():
            save_results.parent.mkdir(parents=True)

        with open(save_results, "wb") as fh:
            pickle.dump(events, fh)

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
        default="",
        help="The location (including file name) where you want to save event lists",
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
    parser.add_argument("-s", "--start_time", default=None, type=int)
    parser.add_argument("-e", "--end_time", default=None, type=int)
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

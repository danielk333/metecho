from pathlib import Path
import os
import logging
import pickle

from .. import data
from .. import tools
from .. import events
from .. import signal_model
from .commands import add_command

logger = logging.getLogger(__name__)

try:
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
except ImportError:

    class COMM_WORLD:
        rank = 0
        size = 1

        def barrier(self):
            pass

    comm = COMM_WORLD()


def raw_data_file_list(output_dir, cli_logger, args):
    if args.radar.lower() == "mu":
        backend = "mu_h5"
    else:
        raise ValueError(f'Radar "{args.radar}" not supported by find_events function')

    paths = []
    for path in args.files:
        path = Path(path).resolve()
        if path.is_dir():
            data_store = data.DataStore(
                path,
                include_convertable=args.convert,
            )
            paths += [file for file, backend in data_store.get_files()]

            if args.convert:
                paths += data_store.convert(
                    output_dir, backend, MPI=comm.size > 1, MPI_root=-1
                )
        else:
            input_fmt = data.check_if_convertable(path)
            if input_fmt is not None and args.convert:
                paths += data.convert(
                    [path],
                    output_dir,
                    backend=backend,
                    input_format=input_fmt,
                    MPI=comm.size > 1,
                    MPI_root=-1,
                )[0]
                continue

            backend_fmt = data.check_if_raw_data(path)
            if backend_fmt is not None:
                paths.append(path)
            else:
                cli_logger.warning(
                    f'Input path "{path}" was not convertable (or conversions are not enabled) \
                    nor a file of a supported raw data format and therefor skipped'
                )

    return paths


@tools.MPI_target_arg(0)
def find_events(file, args, cli_logger):
    cli_logger.info(f"Handling {file}")
    if args.radar.lower() == "mu":
        backend = "mu_h5"
        config = events.generate_event_search_config()
    else:
        raise ValueError(f'Radar "{args.radar}" not supported by find_events function')

    raw = data.RawDataInterface(file, backend=backend)

    signal = signal_model.phase_coding.barker_code_13(
        raw.data.shape[raw.axis["pulse"]],
        2,
    )

    event_list, nonhead, best_data, noise = events.search(
        raw,
        config,
        None,
        signal,
        plot=args.plot,
        save_as_image=args.plot_save,
        save_location=args.plot_output,
    )
    if args.best_data:
        return [event_list, nonhead, best_data, noise]
    else:
        return [event_list, nonhead, None, noise]


def main(args, cli_logger):
    default_folder = Path(os.getcwd()) / "output"

    if len(args.output) == 0:
        args.output = default_folder / "events.pickle"
    if len(args.convert_output) == 0:
        args.convert_output = default_folder / "convert"
    if len(args.plot_output) == 0:
        args.plot_output = default_folder / "plots"
    else:
        args.plot_save = True
        args.plot_output = Path(args.plot_output).resolve()

    if args.convert:
        output_dir = Path(args.convert_output).resolve()

        logger.debug(f'Setting output path and converting files to "{output_dir}"')
        if comm.rank == 0:
            output_dir.mkdir(exist_ok=True)
        comm.barrier()
    else:
        output_dir = None

    save_results = Path(args.output).resolve()
    if save_results.is_dir():
        raise ValueError(
            f'Output results path "{save_results}" is a directory, not a file-path'
        )

    cli_logger.info("Getting file list...")
    paths = raw_data_file_list(output_dir, cli_logger, args)

    results = find_events(paths, args, cli_logger, MPI=comm.size > 1, MPI_root=0)

    if comm.rank == 0:
        if not save_results.parent.exists():
            save_results.parent.mkdir(parents=True)

        with open(save_results, "wb") as fh:
            pickle.dump(results, fh)
        cli_logger.info(f"Saved results to pickle at {save_results}")

    comm.barrier()


def parser_build(parser):
    parser.add_argument(
        "-Co",
        "--convert-output",
        default="",
        help="The location where you want to save converted files",
    )
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
        "-C",
        "--convert",
        action="store_true",
        help="Convert files if possible to supported backend formats",
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
    parser.add_argument(
        "radar", choices=["MU"], help="The radar that performed the observations"
    )
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
    command_help="Searches radar data to look for signs of meteor events.",
)

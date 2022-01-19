from pathlib import Path
import os
import metecho
import logging
import pickle

from .. import data
from .. import tools
from .. import events
from .main import add_command

logger = logging.getLogger(__name__)


@tools.profiling.timeing(f'{__name__}')
def raw_data_file_list(args, output_dir, radar, cli_logger):
    if radar.lower() == 'mu':
        backend = 'mu_h5'
    else:
        raise ValueError(f'Radar "{radar}" not supported by find_events function')

    paths = []
    for path in args.files:
        path = Path(path).resolve()
        if path.is_dir():
            data_store = metecho.data.DataStore(
                path, 
                include_convertable = args.convert,
            )
            paths += [file for file, backend in data_store.get_files()]

            if args.convert:
                paths += data_store.convert(output_dir, backend)
        else:
            paths.append(path)

    return paths


@tools.profiling.timeing(f'{__name__}')
def find_events(file, plot, radar, args):
    if radar.lower() == 'mu':
        backend = 'mu_h5'
        config = events.generate_event_search_config()
    else:
        raise ValueError(f'Radar "{radar}" not supported by find_events function')

    raw = data.RawDataInterface(file, backend=backend)

    signal = metecho.generalized_matched_filter.signal_model.barker_code_13(
        raw.data.shape[raw.axis['pulse']],
        2,
    )

    event_list, nonhead, best_data, noise = events.search(
        raw, 
        config, 
        None, 
        signal, 
        plot=plot, 
        save_as_image=args.save, 
        save_location=args.output,
    )
    if args.best_data:
        return [event_list, nonhead, best_data, noise]
    else:
        return [event_list, nonhead, None, noise]


@tools.profiling.timeing(f'{__name__}')
def main(args, cli_logger):

    output_dir = Path(args.converted_output).resolve()
    if args.convert:
        logger.debug(f'Setting output path and converting files to "{output_dir}"')
        output_dir.mkdir(exist_ok=True)

    paths = raw_data_file_list(args, output_dir, cli_logger)

    results = []
    for path in paths:
        logger.debug(f"Handling {path.resolve()}")
        ret = find_events(path, args.plot)
        results.append(ret)

    save_results = Path(args.output).resolve()
    if save_results.is_dir():
        raise ValueError(f'Output results path "{save_results}" is a directory, not a file-path')

    if not save_results.parent.exists():
        save_results.parent.mkdir(parents=True)

    with open(save_results, "wb") as fh:
        pickle.dump(results, fh)

    cli_logger.info(f'Saved results to pickle at {save_results}')


parser = add_command(
    name='event_search',
    function=main,
    command_help='Searches radar data to look for signs of meteor events.',
)

parser.add_argument("files", nargs='+',
                    help="Input the locations of the files (or folders) you want analyzed.")
parser.add_argument('radar',
                    default='MU', choices=['MU'],
                    help='The radar that performed the observations')
parser.add_argument("-co", "--converted_output",
                    default=Path(os.path.realpath(__file__)).parent / "output",
                    help="The location where you want to save converted files and look for cached files")
parser.add_argument("-o", "--output",
                    default=Path(os.path.realpath(__file__)).parent / "output" / "events.pickle",
                    help="The location (including file name) where you want to save analyzed data")
parser.add_argument("-p", "--plot", action="store_true",
                    help="Shows plots of the files as it runs. Warning: \
                    Currently it will pause upon each render which must be closed for it to continue.")
parser.add_argument("-s", "--save",
                    action="store_true",
                    help="Saves image to the output folder if set.")
parser.add_argument("-q", "--sequential",
                    action="store_true",
                    help="Make sure raw data files are analyzed sequentially and events \
                    spanning multiple files are correctly identified.")
parser.add_argument("-b", "--best_data",
                    action="store_true",
                    help="Stores best data in pickle if set.")

import sys
from pathlib import Path
import os
import metecho
import logging
import pickle
import argparse

metecho_log = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)

logger = logging.getLogger('metecho')
logger.setLevel(logging.WARNING)
logger.addHandler(handler)

metecho.profiler.enable('metecho')

parser = argparse.ArgumentParser(description='Searches radar data to look for signs of meteor events.')
parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="count", default=0)
parser.add_argument("files", nargs='+',
                    help="Input the locations of the files (or folders) you want analyzed.")
parser.add_argument("-co", "--converted_output",
                    default=Path(os.path.realpath(__file__)).parent / "output",
                    help="The location where you want to save converted files and look for cached files")
parser.add_argument("-o", "--output",
                    default=Path(os.path.realpath(__file__)).parent / "output" / "save.p",
                    help="The location (including file name) where you want to save analyzed data")
parser.add_argument("-p", "--plot", action="store_true",
                    help="Shows plots of the files as it runs. Warning: \
                    Currently it will pause upon each render which must be closed for it to continue.")
parser.add_argument("-s", "--save",
                    action="store_true",
                    help="Saves image to the output folder if set.")
parser.add_argument("-b", "--best_data",
                    action="store_true",
                    help="Stores best data in pickle if set.")


args = parser.parse_args()

if args.verbose > 0:
    for name in logging.root.manager.loggerDict:
        if name.startswith('metecho'):
            print(f'logger: {name}')

if args.verbose > 1:
    print("Logging level set to debug")
    logger.setLevel(logging.DEBUG)


@metecho.tools.profiling.timeing(f'{__name__}', enabled=True)
def convert_files(save_dir, curr):
    save_dir.mkdir(exist_ok=True)

    metecho_log.debug(f'Setting output path and creating directories at location {save_dir}')
    metecho_log.debug("Trying to convert MUI files to h5 files.")

    h5_files = metecho.data.mu.convert_MUI_to_h5(
        [curr.resolve()],
        save_dir,
        skip_existing=True,
        MPI=True,
    )
    return [file for converted in h5_files for file in converted]


@metecho.tools.profiling.timeing(f'{__name__}', enabled=True)
def find_events(file, plot):
    raw = metecho.data.RawDataInterface(file)
    config = metecho.events.generate_event_search_config()
    signal = metecho.generalized_matched_filter.signal_model.barker_code_13(
        raw.data.shape[raw.axis['pulse']], 2)
    events, nonhead, best_data, noise = metecho.events.search(
        raw, config, None, signal, plot=plot, save_as_image=args.save, save_location=args.output[0])
    if args.best_data:
        return [events, nonhead, best_data, noise]
    else:
        return [events, nonhead, None, noise]


@metecho.tools.profiling.timeing(f'{__name__}', enabled=True)
def metecho_main(files, save_dir, plot):
    results = []
    file_name = Path(file_name)
    if file_name.is_file():
        if args.verbose > 0:
            print(f"Handling file {file_name.resolve()}")
        try:
            metecho_log.debug("Found file, trying to open.")
            results.append(find_events(file_name.resolve(), plot))

        except ValueError:
            metecho_log.debug("File was not a h5 a supported file. Trying to convert.")
            split_name = file_name.name.split(".")
            if len(split_name) == 3 and split_name[0] == "MUI":
                metecho_log.debug("Searching for cached files.")
                cached_files = save_dir / ("20" + split_name[1][0:2]) / \
                    split_name[1][2:4] / split_name[1][4:6]
                files = list(cached_files.glob('*.h5'))
                if files == []:
                    metecho_log.debug("None found, converting files.")
                    files = convert_files(save_dir, file_name)
                else:
                    metecho_log.debug("Found already existing files, using those.")
            else:
                files = convert_files(save_dir, file_name)
            metecho_log.debug("Analyzing output h5 files.")
            for file in files:
                results.append(find_events(file, plot))
    elif file_name.is_dir():
        if args.verbose > 0:
            print(f"Handling folder {file_name.resolve()}")
        metecho_log.debug("Finding h5 files.")
        files = list(file_name.glob('*.h5'))
        if files == []:
            metecho_log.debug("None found, finding MUI files.")
            files = list(file_name.glob('MUI.*.*'))
        if files == []:
            metecho_log.warning("Didn't find any MUI nor h5 files. Returning.")
            return
        for file in files:
            metecho_log.debug(f"Handling {file.resolve()}")
            results += metecho_main(file, save_dir, plot)
    return results


output_dir = Path(args.converted_output[0]).resolve()
results = metecho_main(
    [Path(file) for file in args.files], 
    output_dir, 
    args.plot,
)

save_results = Path(args.output[0]).resolve()
if save_results.is_dir():
    raise ValueError(f'Output results path "{save_results}" is a directory, not a file-path')

if not save_results.parent.exists():
    save_results.parent.mkdir(parents=True)

with open(save_results, "wb") as fh:
    pickle.dump(results, fh)

print(f'Saved results to pickle at {save_results}')
if args.verbose > 0:
    print(metecho.profiler)

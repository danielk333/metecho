import sys
from pathlib import Path
import os
import metecho
import logging

metecho_log = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
for name in logging.root.manager.loggerDict:
    if name.startswith('metecho'):
        print(f'logger: {name}')

logger = logging.getLogger('metecho')
logger.setLevel(logging.WARNING)
logger.addHandler(handler)

metecho.profiler.enable('metecho')


@metecho.tools.profiling.timeing(f'{__name__}')
def convert_files(save_dir, curr):
    save_dir.mkdir(exist_ok=True)
    metecho_log.debug(f'Setting output path and creating directories at location {save_dir}')
    metecho_log.debug("Trying to convert MUI files to h5 files.")
    h5_files = metecho.data.mu.convert_MUI_to_h5(
        [curr.resolve()],
        skip_existing=False,
        output_location=save_dir,
        MPI=True,
    )
    return [file for converted in h5_files for file in converted]


@metecho.tools.profiling.timeing(f'{__name__}')
def find_events(file):
    raw = metecho.data.RawDataInterface(file)
    config = metecho.events.generate_event_search_config()
    signal = metecho.generalized_matched_filter.signal_model.barker_code_13(
        raw.data.shape[raw.axis['pulse']], 2)
    events, nonhead, best_data, noise = metecho.events.search(
        raw, config, None, signal, plot=False)
    return events


@metecho.tools.profiling.timeing(f'{__name__}')
def metecho_main(file_name, results, indents=0):
    curr = Path(file_name)
    if curr.is_file():
        print(("\t" * indents) + f"Handling file {curr.resolve()}")
        try:
            metecho_log.debug("Found file, trying to open.")
            results.append(find_events(curr.resolve()))

        except ValueError:
            metecho_log.debug("File was not a h5 a supported file. Trying to convert.")
            save_dir = Path(os.path.realpath(__file__)).parent / "output"
            split_name = curr.name.split(".")
            if len(split_name) == 3 and split_name[0] == "MUI":
                metecho_log.debug("Searching for cached files.")
                cached_files = save_dir / ("20" + split_name[1][0:2]) / \
                    split_name[1][2:4] / split_name[1][4:6]
                files = list(cached_files.glob('*.h5'))
                if files == []:
                    metecho_log.debug("None found, converting files.")
                    files = convert_files(save_dir, curr)
                else:
                    metecho_log.debug("Found already existing files, using those.")
            else:
                files = convert_files(save_dir, curr)
            metecho_log.debug("Analyzing output h5 files.")
            for file in files:
                results.append(find_events(file))
    elif curr.is_dir():
        print('\t' * indents + f"Handling folder {curr.resolve()}")
        metecho_log.debug("Finding h5 files.")
        files = list(curr.glob('*.h5'))
        if files == []:
            metecho_log.debug("None found, finding MUI files.")
            files = list(curr.glob('MUI.*.*'))
        if files == []:
            metecho_log.warning("Didn't find any MUI nor h5 files. Returning.")
            return
        for file in files:
            metecho_log.debug(f"Handling {file.resolve()}")
            metecho_main(file, results, indents + 1)


results = []

for argument in sys.argv[1:]:
    metecho_main(argument, results)

flatten_result = [item for sublist in results for item in sublist]
print(f'Found a total of {len(flatten_result)} events!')
print(metecho.profiler)

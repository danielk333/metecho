import pathlib
import sys

import metecho

metecho.profiler.init('full', True)
metecho.profiler.start('full')

if len(sys.argv) < 3:
    raise RuntimeError('Need path to a MUI file and output to perform conversion')

in_path = pathlib.Path(sys.argv[1])
out_path = pathlib.Path(sys.argv[2])

if not out_path.is_dir():
    raise ValueError(f'Output path "{out_path}" is not a directory or does not exist')

if not in_path.is_file():
    raise ValueError(f'Input path "{in_path}" does not exist')

metecho.debug()

# We can also use the converter as all converters should be registered for use
print('Avalible converters:')
print(metecho.data.list_converters())

print('\n\nConverting directly with converter...\n\n')
files = metecho.data.mu.convert_MUI_to_h5(
    [in_path], 
    out_path,
    skip_existing = False,
)

for file in files[0]:
    print(f'"{pathlib.Path(file).name}" created')

print('\n\nConverting using the converter library...\n\n')

files = metecho.data.convert(
    [in_path], 
    out_path,
    backend = 'mu_h5',
    skip_existing = False,
)

for file in files[0]:
    print(f'"{pathlib.Path(file).name}" created')

metecho.profiler.stop('full')
print(metecho.profiler)

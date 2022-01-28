'''
Using the DataStore
===================
'''
import pathlib
import logging
import sys

import metecho

import matplotlib.pyplot as plt

metecho.profiler.init('full', True)
metecho.profiler.start('full')

try:
    HERE = pathlib.Path(__file__).parent.resolve()
except NameError:
    HERE = pathlib.Path('.').parent.resolve()

handler = logging.StreamHandler(sys.stdout)

for name in logging.root.manager.loggerDict:
    if name.startswith('metecho'):
        print(f'logger: {name}')

logger = logging.getLogger('metecho')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

metecho.profiler.enable('metecho')

data_path = HERE / 'data'

print('The example directory tree')
print(metecho.data.directory_tree(data_path))

data_store = metecho.data.DataStore(data_path)

print(data_store.tree(clean=True))
print(data_store)

print('Including files that are convertable')
data_store.include_convertable = True
data_store.reload()
print(data_store.tree(clean=True))

for file, backend in zip(data_store._file_list, data_store._backend_list):
    print(f'{file.name}: {backend}')

factory = data_store.factory(selection=[1, 2])
print(factory)

fig, axes = plt.subplots(2, 1)
for ind, raw in enumerate(factory):
    print(f'"{raw.path.name}" loaded from factory')
    metecho.plot.rti(raw, ax=axes[ind])


def filt(path, backend): 
    return path.name == '2009-06-27T09.54.04.100000000.h5'


print('Results from filtering a datastore')
factory = data_store.factory(path_backend_filter=filt)
for raw in factory:
    print(raw.path)

metecho.profiler.stop('full')
print(metecho.profiler)

plt.show()

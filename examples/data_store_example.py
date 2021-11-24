import pathlib
import logging
import sys

import metecho

import matplotlib.pyplot as plt

metecho.profiler.init('full', True)
metecho.profiler.start('full')

HERE = pathlib.Path(__file__).parent.resolve()

handler = logging.StreamHandler(sys.stdout)

for name in logging.root.manager.loggerDict:
    if name.startswith('metecho'):
        print(f'logger: {name}')

logger = logging.getLogger('metecho')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

metecho.profiler.enable('metecho')

data_path = HERE / 'data' / 'MU_h5'

print('The example directory tree')
print(metecho.data.directory_tree(data_path))

data_store = metecho.data.DataStore(data_path)

print(data_store.tree(clean=True))
print(data_store)

factory = data_store.factory(selection=[1, 2])
print(factory)

fig, axes = plt.subplots(2, 1)
for ind, raw in enumerate(factory):
    print(f'"{raw.path.name}" loaded from factory')
    metecho.plot.rti(raw, ax=axes[ind])

print(metecho.profiler)

plt.show()

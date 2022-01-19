'''
Listing directory contents
===========================
'''

import pathlib
import metecho

try:
    HERE = pathlib.Path(__file__).parent.resolve()
except NameError:
    HERE = pathlib.Path('.').parent.resolve()

data_path = HERE / 'data'

print(metecho.data.directory_tree(data_path))

print(metecho.data.directory_tree(
    data_path,
    filter_function = lambda x: x.suffix == '.h5' or x.name.startswith('MUI'),
))

print(metecho.data.directory_tree(
    data_path,
    level = 2,
    filter_function = lambda x: x.suffix == '.h5' or x.name.startswith('MUI'),
))

print(metecho.data.directory_tree(
    data_path,
    filter_function = lambda x: x.suffix == '.h5' or x.name.startswith('MUI'),
    length_limit = 5,
))

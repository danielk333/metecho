import pathlib
import metecho

data_path = pathlib.Path('/home/danielk/data/MU')

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

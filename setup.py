import setuptools
from distutils.core import Extension
import pathlib
import codecs

HERE = pathlib.Path(__file__).resolve().parents[0]


def get_version(path):
    with codecs.open(path, 'r') as fp:
        for line in fp.read().splitlines():
            if line.startswith('__version__'):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
        else:
            raise RuntimeError("Unable to find version string.")


libxcorr = Extension(
    name='metecho.clibmet',
    sources=[
        'src/clibmet/libxcorr/libxcorr.c',
    ],
    include_dirs=['src/clibmet/libxcorr/'],
)


setuptools.setup(
    version=get_version(HERE / 'src' / 'metecho' / 'version.py'),
    package_dir={
        "": "src"
    },
    packages=setuptools.find_packages(where="src"),
    ext_modules=[libxcorr],
)

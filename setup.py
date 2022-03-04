import setuptools
import codecs
import pathlib
from distutils.core import Extension

HERE = pathlib.Path(__file__).resolve().parents[0]

with open('README.md', 'r') as fh:
    long_description = fh.read()


def get_version(path):
    '''Read version from python version file
    
    Code originally from:
    https://packaging.python.org/guides/single-sourcing-package-version/#single-sourcing-the-version
    '''
    with codecs.open(path, 'r') as fp:
        for line in fp.read().splitlines():
            if line.startswith('__version__'):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
        else:
            raise RuntimeError("Unable to find version string.")


libxcorr = Extension(
    name='metecho.generalized_matched_filter.libxcorr',
    sources=['src/libxcorr/libxcorr.c'],
    include_dirs=['src/libxcorr/'],
)


setuptools.setup(
    version=get_version(HERE / 'src' / 'metecho' / 'version.py'),
    ext_modules=[libxcorr],
)

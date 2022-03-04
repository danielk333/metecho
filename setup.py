import setuptools
from distutils.core import Extension

libxcorr = Extension(
    name='metecho.generalized_matched_filter.libxcorr',
    sources=['src/libxcorr/libxcorr.c', 'src/libxcorr/libxcorr.h'],
)

setuptools.setup(
    ext_modules=[libxcorr],
)

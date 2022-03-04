import setuptools
from distutils.core import Extension

libxcorr = Extension(
    name='metecho.generalized_matched_filter.libxcorr',
    sources=['src/libxcorr/libxcorr.c'],
    include_dirs=['src/libxcorr/'],
)

setuptools.setup(
    package_dir={
        "": "src"
    },
    packages=setuptools.find_packages(where="src"),
    ext_modules=[libxcorr],
)

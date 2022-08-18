import setuptools
from distutils.core import Extension

libxcorr = Extension(
    name='metecho.clibmet',
    sources=[
        'src/clibmet/libxcorr/libxcorr.c',
        'src/clibmet/libdoa/libdoa.c',
    ],
    include_dirs=['src/libxcorr/'],
)

setuptools.setup(
    package_dir={
        "": "src"
    },
    packages=setuptools.find_packages(where="src"),
    ext_modules=[libxcorr],
)

# Welcome to Metecho's documentation!

!!! Warning
    This repository is a porting/refactoring work in progress: do not use any of the source code until a official release has been drafted.

## Introduction

Metecho (Radar meteor echo analysis toolbox) is a library to support meteor analysis. At time writing this
it supports event search and some simple meteor models.

## Installation

To install, ensure dependencies `gcc`, `libfftw3-dev`, and `libhdf5-dev` are
installed for the C implementations and/or `cuda` for the GPU implementations.
The subpackage hardtarget is dependent on these.

```bash
   pip install metecho
```

or the nightly build

```bash
   git clone --branch develop git@github.com:danielk333/metecho.git
   cd metecho
   pip install .
```

Read the CLI description

```bash
   metecho -h
```

## Usage

### Scripting

See the `/examples` folder for examples.

### CLI

The package also has a command line interface bound to `metecho`:

```
usage: metecho [-h] [-p] [-v] {event_search,plot} ...

Radar meteor echo analysis toolbox

positional arguments:
  {event_search,plot}  Avalible command line interfaces
    event_search
    plot

options:
  -h, --help           show this help message and exit
  -p, --profiler       Run profiler
  -v, --verbose        Increase output verbosity
```

## Getting Help

If you have questions about using metecho please open a [GitHub Issue](https://github.com/danielk333/metecho/issues) or email the [metecho
developers](mailto:daniel.kastinen@irf.se)

## Contributing

Please refer to the style and contribution guidelines documented in the
[IRF Software Contribution Guide](https://danielk.developer.irf.se/software_contribution_guide/).
Generally external code-contributions are made trough a "Fork-and-pull"
workflow, while internal contributions follow the branching strategy outlined
in the contribution guide.

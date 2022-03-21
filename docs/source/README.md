## WORK IN PROGRESS PACKAGE

This repository is a porting/refactoring work in progress: do not use any of the source code until a official release has been drafted.

## Installation

- Clone this repository 
- Go to the directory where you cloned it
- Run `pip install .`

## Usage

### Scripting

See the `/examples` folder that is also included as package data for scripting or the examples gallery in the web-documentation.

### CLI

The package also has a command line interface bound to `metecho`:

```
usage: metecho [-h] [-p] [-v] {convert,event_search} ...

Radar meteor echo analysis toolbox

positional arguments:
  {convert,event_search}
                        Avalible command line interfaces
    convert             Convert the target files to a supported backend format
    event_search        Searches radar data to look for signs of meteor events.

optional arguments:
  -h, --help            show this help message and exit
  -p, --profiler        Run profiler
  -v, --verbose         Increase output verbosity
```

## Contributing

Please refer to the style and contribution guidelines documented in the 
[IRF Software Contribution Guide](https://danielk.developer.irf.se/software_contribution_guide/). 
Generally external code-contributions are made trough a "Fork-and-pull" 
workflow, while internal contributions follow the branching strategy outlined 
in the contribution guide.
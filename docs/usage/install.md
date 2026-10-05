# Install

---

!!! note
    metecho installation is only supported on Linux

---

## Prerequisites

The subpackage hardtarget depends on `gcc`, `libhdf5-dev`, and `libfftw3-dev`.

```bash
    sudo apt install gcc libfftw3-dev libhdf5-dev
```

It is recommended to install metecho in a virtual environment, e.g. `virtualenv` or `conda`.

```bash
    $ python3.X -m venv venv
    $ source venv/bin/activate
    $ pip install --upgrade pip
```

---

## Installation from PyPi

```bash

    $ pip install metecho
```

---

## Installation from Git

Basic install.

```bash

    $ git clone git@github.com:danielk333/metecho.git
    $ cd metecho
    $ pip install .
```

Nightly build.

```bash

    $ git clone --branch develop git@github.com:danielk333/metecho.git
    $ cd hardtarget
    $ pip install .
```

Full developer install.

```bash

    $ pip install -e .[all]
```

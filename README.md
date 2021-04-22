[![Build Status](https://github.com/UCBerkeleySETI/blimpy/workflows/Test%20Blimpy/badge.svg)](https://github.com/UCBerkeleySETI/blimpy/actions)
[![Documentation Status](https://readthedocs.org/projects/blimpy/badge/?version=latest)](https://blimpy.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/UCBerkeleySETI/blimpy/branch/master/graph/badge.svg)](https://codecov.io/gh/UCBerkeleySETI/blimpy)
 [![JOSS status](http://joss.theoj.org/papers/e58ef21f0a924041bf9438fd75f8aed0/status.svg)](http://joss.theoj.org/papers/e58ef21f0a924041bf9438fd75f8aed0)

# Breakthrough Listen I/O Methods for Python
 
 - [Introduction](#introduction)
 - [Dependency Installation](#dependency-installtion)
 - [blimpy Installation](#blimpy-installation)
 - [Developer Installation](#developer-installation)
 - [Using blimpy inside Docker](#using-blimpy-inside-docker)
 - [Command line utilities](#command-line-utilities)
 - [Reading blimpy filterbank files in .fil or .h5 format](#reading-blimpy-filterbank-files-in-fil-or-h5-format)
 - [Reading guppi raw files](#reading-guppi-raw-files)
 - [Further reading](#further-reading)
 - [Data archive](#data-archive)
 - [Bugs and feature requests](#bugs-and-feature-requests)


## [Introduction](#introduction)
This README file details the installation instructions for Breakthrough Listen I/O Methods for Python (blimpy). Developers should also read [CONTRIBUTING](./CONTRIBUTING.md).

### Filterbank + Raw file readers
This repository contains Python 2/3 readers for interacting with [Sigproc filterbank](http://sigproc.sourceforge.net/sigproc.pdf) (.fil), HDF5 (.h5) and [guppi raw](https://baseband.readthedocs.io/en/stable/guppi/) (.raw) files, as used in the [Breakthrough Listen](https://seti.berkeley.edu) search for intelligent life.

## [Dependency Installation](#dependency-installation)
The installation can fail if a system dependency is not installed. Please refer to the [dependencies.txt](./dependencies.txt) file for a list of system dependencies. If the Operating System is not Debian/Ubuntu, please refer to the install instructions for your Operating System.

### Debian/Ubuntu dependencies
For Debian/Ubuntu systems, make sure that `curl` is installed and you have `sudo` access. Install the required system dependencies with the following command:
```
curl https://raw.githubusercontent.com/UCBerkeleySETI/blimpy/master/dependencies.txt | xargs -n 1 sudo apt install --no-install-recommends -y
```

### Python dependencies
blimpy requires `numpy`, `h5py`, `astropy`, `scipy`, `hdf5plugin`and `matplotlib` packages; the installation will attempt to automatically install them.

Please note, when manually undertaking an installation of h5py it generally needs to be installed using the following:
```
python3 -m pip install --no-binary=h5py h5py
```

## [blimpy Installation](#blimpy-installation)

### Virtualenv based installation
For Virtualenv based installations please ensure you have configured a Virtualenv (i.e. `python3 -m venv my_env`) and that it is activated (i.e. `source my_env/bin/activate`). Once the Virtualenv is activated, it may be necessary to execute `PATH=${PATH}:${VIRTUAL_ENV}/bin` to easily access the command line utilities.
```
python3 -m pip install blimpy
```

### (Optional) User based installation
```
python3 -m pip install blimpy --user
```

### (Optional) Install the latest release from the repository
The latest release can be installed via `pip` directly from this repository:
```
python3 -m pip install -U git+https://github.com/UCBerkeleySETI/blimpy
```
Add `--user` to the end of the above command if using a user based installation.

## [Developer Installation](#developer-installation)
The latest version of the development code can be installed by cloning the Github [repo](https://github.com/UCBerkeleySETI/blimpy) and running:

### Virtualenv based installation
```
python3 setup.py install
```

### (Optional) User based installation
```
python3 setup.py install --user
```

### (Optional) Install using PyPI
```
python3 -m pip install -U https://github.com/UCBerkeleySETI/blimpy/tarball/master
```
Add `--user` to the end of the above command if using a user based installation.

### Unit tests
To install the packages needed to run the unit tests, use the following:

#### Virtualenv based installation
```
python3 -m pip install -e '.[full]'
```

#### (Optional) User based installation
```
python3 -m pip install --no-use-pep517 --user -e '.[full]'
```

## [Using blimpy inside Docker](#using-blimpy-inside-docker)
The blimpy Docker images are pushed to a public repository after each successful build on Travis CI (Continuous Integration).

If you have Docker installed, you can run the following commands to pull our images, which have the environment and dependencies all ready set up.
```
docker pull fx196/blimpy:py3_kern_stable
```

Here is a [more complete guide](./docker_guide.md) on using blimpy in Docker.

## [Command line utilities](#command-line-utilities)
After installation, some command line utilities will be installed:
- `watutil`, Read/write/plot an .h5 file or a .fil file.
- `rawutil`, Plot data in a guppi raw file.
- `fil2h5`, Convert a .fil file into .h5 format.
- `h52fil`, Convert an .h5 file into .fil format.
- `bldice`, Dice a smaller frequency region from (either from/to .h5 or .fil).
- `matchfils`, Check if two .fil files are the same.
- `calcload`, Calculate the Waterfall max_load value needed to load the data array for a given file.
- `rawhdr`, Display the header fields of a raw guppi file.

Use the `-h` flag to any of the above command line utilities to display their available arguments.

## [Reading blimpy filterbank files in .fil or .h5 format](#reading-blimpy-filterbank-files-in-fil-or-h5-format)
The `blimpy.Waterfall`  provides a Python API for interacting with filterbank data. It supports all BL filterbank data products; see this [example Jupyter notebook](https://github.com/UCBerkeleySETI/blimpy/blob/master/examples/voyager.ipynb) for an overview.

From a Python, iPython or Jupiter notebook environments.

```python
from blimpy import Waterfall
fb = Waterfall('/path/to/filterbank.fil')
#fb = Waterfall('/path/to/filterbank.h5') #works the same way
fb.info()
data = fb.data
```

## [Reading guppi raw files](#reading-guppi-raw-files)
The [Guppi Raw format](https://github.com/UCBerkeleySETI/breakthrough/blob/master/doc/RAW-File-Format.md) can be read using the `GuppiRaw` class from `guppi.py`:

```python
from blimpy import GuppiRaw
gr = GuppiRaw('/path/to/guppirawfile.raw')

header, data = gr.read_next_data_block()
```

or

```python
from blimpy import GuppiRaw
gr = GuppiRaw('/path/to/guppirawfile.raw')

for header, data_x, data_y in gr.get_data():
    # process data
```

Note: most users should start analysis with filterbank files, which are smaller in size and have been generated from the guppi raw files.

## [Further reading](#further-reading)
A detailed overview of the data formats used in Breakthrough Listen can be found in our [data format paper](https://ui.adsabs.harvard.edu/abs/2019arXiv190607391L/abstract). 

## [Data archive](#data-archive)
An archive of data files from the Breakthrough Listen program are provided at [seti.berkeley.edu/opendata](http://seti.berkeley.edu/opendata).

## [Bugs and feature requests](#bugs-and-feature-requests)

Bugs and feature requests should be submitted using [blimpy issues](https://github.com/UCBerkeleySETI/blimpy/issues).

## If you have any feedback or questions, please lets us know!

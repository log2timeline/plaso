# Developing in a Virtualenv

For development purposes, Plaso can be installed using a Python virtual
environment (venv).

**Note that this is intended for development use only, and if you aren't
comfortable debugging package installation, this is not for you.**

Plaso requires Python 3.10 or later.

## Fedora

### Install venv

The venv module is included with the Python 3 package on Fedora (or
equivalent):
```
sudo dnf install python3
```

### Installing build dependencies

**TODO add more text**

## Ubuntu

### Installing venv

To install venv on Ubuntu (or equivalent) run:
```
sudo apt install python3-venv
```

### Installing build dependencies

**TODO add more text**
```
sudo apt install libyaml-dev liblzma-dev
```

## MacOS

### Installing venv

The venv module is included with Python 3. To install Python 3.10 or later,
either download it from https://www.python.org/downloads/ or, using
[homebrew](https://brew.sh/), run:

```bash
brew install python@3
```

### Installing build dependencies

**TODO**

## Setting up Plaso in a virtualenv

1. Create a virtualenv called 'plasoenv' `python3 -m venv plasoenv`
1. Activate the virtualenv: `source ./plasoenv/bin/activate`
1. Update pip (Note that using pip outside virtualenv is not recommended as it
ignores your systems package manager.): `pip install --upgrade pip`
1. Install Plaso and its Python requirements in editable mode
    ```bash
    # Where 'plaso' is your local Plaso source directory
    cd plaso
    pip install -e .
    ```
1. Install the test dependencies (see test_dependencies.ini): `pip install fakeredis`
1. Once you finish your development session, deactivate virtualenv: `deactivate`

# Developing in a Virtualenv

For development purposes, Plaso can be installed using virtualenv.

**Note that this is intended for development use only, and if you aren't 
comfortable debugging package installation, this is not for you.**

## Fedora Core

### Install virtualenv

To install virtualenv on Fedora Core (or equivalent) run:
```
sudo dnf install python-virtualenv
```

### Installing build dependencies

**TODO add more text**

## Ubuntu

### Installing virtualenv

To install virtualenv on Ubuntu (or equivalent) run:
```
sudo apt-get install python-virtualenv
```

### Installing build dependencies

**TODO add more text**
```
sudo apt-get install libyaml-dev liblzma-dev
```

## MacOS

### Installing virtualenv
**TODO**

### Installing build dependencies

**TODO**


## Setting up Plaso in a virtualenv

1. Create a virtualenv called 'plasoenv' `virtualenv plasoenv`
1. Activate the virtualenv: `source ./plasoenv/bin/activate`
1. Update pip (Note that using pip outside virtualenv is not recommended as it 
ignores your systems package manager.): `pip install --upgrade pip`
1. Install the Python requirements
    ```bash
    # Where 'plaso' is your local Plaso source directory
    cd plaso
    curl -O https://raw.githubusercontent.com/log2timeline/plaso/master/requirements.txt
    pip install -r requirements.txt
    ```
1. Once you finish you development session, deactivate virtualenv: `deactivate`

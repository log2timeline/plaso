# Setting up plaso in virtualenv

For development purposes, Plaso can be installed using virtualenv.

**Note that this is intended for development use only, and if you aren't comfortable debugging package installation, this is not for you.**

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

## Setting up plaso in virtualenv

To create a virtualenv:
```
virtualenv plasoenv
```

To activate the virtualenv:
```
source ./plasoenv/bin/activate
```

**Note that using pip outside virtualenv is not recommended since it ignores your systems package manager.**

```
pip install --upgrade pip
```

```
curl -O https://raw.githubusercontent.com/log2timeline/plaso/master/requirements.txt
pip install -r requirements.txt
```

To install Python modules from source:
```
VENVDIR=`readlink -f plasoenv`
${VENVDIR}/bin/python setup.py build
${VENVDIR}/bin/python setup.py install
```

To deactivate the virtualenv run:
```
deactivate
```

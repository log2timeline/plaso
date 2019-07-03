# Developing in a Virtualenv

For development purposes, Plaso can be installed using virtualenv.

**Note that this is intended for development use only, and if you aren't
comfortable debugging package installation, this is not for you.**

## Fedora

### Install virtualenv

To install virtualenv on Fedora (or equivalent) run:
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

If you have `pip` setup on your system, you can install
`virtualenv` using:

```bash
pip install virtualenv
```

To install `pip`, either install a version of Python 3.6+ or,
using [homebrew](https://brew.sh/), run:

```bash
brew install python@3
```

### Installing build dependencies

**TODO**

The `pycrypto` dependency requires the `gmp` library. This is
installable with homebrew:

```bash
brew install gmp
```

Skip ahear to running the `virtualenv plasoenv` command below
before continuing as you need to setup the virtualenv first.

Once setup, we need to add the paths for the system to locate
the `gmp` library by running the below command to append to our
virtual environment `activate` script:

```bash
echo export CFLAGS="-I/usr/local/include -L/usr/local/lib" >> ./plasoenv/bin/activate
```

At this point you can activate the virtual environment and resume
the virtualenv setup instructions below.

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

# Developing on Ubuntu

To download the latest version of Plaso you'll need to install the git tools:
```
sudo apt-get install git
```

Checkout the plaso source from the git repo:
```
git clone https://github.com/log2timeline/plaso.git
```

To be able to run the plaso [development release](Releases-and-roadmap.md) on Ubuntu or equivalent you'll have to have installed the [dependencies](Dependencies.md).

Check if you have all the dependencies installed and have the right minimum version:
```
python utils/check_dependencies.py
```

**Note that some dependencies are actively under development and can be frequently updated, therefore we recommend checking the status of the dependencies regularly.**

## Update frequently
If you really want to run the development release, aka "Bleeding Edge", make sure to update frequently.

To update plaso:
```
git pull origin master
```

If you are using a "github fork" your origin is pointing your fork not the main plaso git repo:
```
git remote -v
origin	https://github.com/log2timeline/plaso (fetch)
origin	https://github.com/log2timeline/plaso (push)
```

Add an upstream remote that you can use to sync your fork:
```
git remote add upstream https://github.com/log2timeline/plaso.git
git pull --rebase upstream master
```

We provide packaged versions of the dependencies via the [l2tbinary project](https://github.com/log2timeline/l2tbinaries/blob/master/README.md). However it is possible that the dependencies are not fully up to date therefore we also provide a build script as part of [l2tdevtools project](https://github.com/log2timeline/l2tdevtools) to do unattended bulk builds.

## Development tools
If you intend to do development on plaso you'll also need to install some development tools:

* PyLint
* Python Mock

### PyLint
Currently plaso development uses PyLint version 1.6.x. 

Remove any older version of PyLint.
```
sudo apt-get remove pylint
```

For pylint 1.6.x the following additional dependencies are required:
* https://pypi.python.org/pypi/astroid
* https://pypi.python.org/pypi/lazy-object-proxy
* https://pypi.python.org/pypi/logilab-common
* https://pypi.python.org/pypi/wrapt

Download and build the python-wrapt Debian package:
**TODO describe**

Download and build the python-lazy-object-proxy Debian package:
**TODO describe**

Download and build the python-logilab-common Debian package:
```
hg clone http://hg.logilab.org/logilab/common
cd common
dpkg-buildpackage -rfakeroot
cd ..
```

Since you're building from development branch it can be possible that you need to disable any failing tests.
Either report these as bugs to the PyLint project or fix them yourself.

Download and build the python-astroid Debian package:
```
hg clone https://bitbucket.org/logilab/astroid
cd astroid
dpkg-buildpackage -rfakeroot
cd ..
```

Download and build the pylint Debian package:
```
hg clone https://bitbucket.org/logilab/pylint
cd pylint
dpkg-buildpackage -rfakeroot
cd ..
```

Install the python-wrapt, python-lazy-object-proxy, python-logilab-common, python-astroid and pylint Debian packages:
```
sudo dpkg -i python-wrapt python-lazy-object-proxy python-logilab-common_0.60.0-1_all.deb python-astroid_1.0.1-1_all.deb pylint_1.6.5-1_all.deb
```

### Python Mock
To install Python Mock run:
```
sudo apt-get install python-mock
```

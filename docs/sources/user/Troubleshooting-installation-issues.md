# Troubleshooting installation issues

General advice:

* search the contents of this page and troubleshooting pages referenced
* search the issue tracker including closed issues, maybe someone else encountered the same issue before you
* search the discuss mailing list, maybe someone else encountered the same issue before you
* file an issue or ask on the discuss mailing list, **make sure to add as much relevant details as possible**

## Ubuntu

Installing the plaso on Ubuntu should be a breeze if you follow the
instructions [here](Ubuntu-Packaged-Release.md), however sometimes there can be
conflicting packages installed that cause plaso not to run properly. Most often
this is caused by either some unsupported versions of packages being installed
or if for some reason some of the dependencies was installed from source at
some point and those dependencies are out of date.

If you are having trouble getting plaso to run on your computer after following
the installation instructions one of the best first steps is to check if all
dependencies are met. One way of doing that is to run the dependency check of
the installed Plaso package:

```bash
$ python3 -c 'from plaso import dependencies; dependencies.CheckDependencies()'
```

Or, from the root of a Plaso source checkout, run the check dependency script:

```bash
$ python3 utils/check_dependencies.py
```

The output should be something on these lines:

```
Checking availability and versions of dependencies.
[OK]		acstore version: 20260411
[OK]		artifacts version: 20260421
[OK]		bencode
...
```

A `[FAILURE]` status indicates that the dependency is missing or that its
version is not supported, for example:

```
[FAILURE]	missing: pyewf.
```

First make sure all currently installed packages are up-to-date by running:

```bash
$ sudo apt update
$ sudo apt upgrade
```

Then re-run the check dependencies script. If that still hasn't fixed the issue
then you need check each of the dependencies with an error status.

One way of doing so is to use IPython to determine the location of the Python
module on your system.

```
$ ipython
Python ...
Type "copyright", "credits" or "license" for more information.
...

In [1]: import pyewf

In [2]: pyewf.get_version()
Out[2]: '20140608'

In [3]: pyewf.__file__
Out[3]: '/usr/lib/python3/dist-packages/pyewf.so'
```

Import the Python module of the dependency that was showing an error status.
Check its version, if it is part of the [libyal](https://github.com/libyal)
collection use the ``LIBRARY.get_version()`` to get the version information,
other Python modules can store their version information differently, a
commonly used convention is ``LIBRARY.__version__``.

If the version is an out-of-date version you can use the ``LIBRARY.__file__``
to determine out where the Python module is located on your system.

The Python module can originate from another Debian package or from a source
installation. If this is originating from a source installation one way of
removing it is to simply delete that particular file (or .egg directory),
however the preferred method is to uninstall source installation properly if
possible.

To find out which package a Python module belongs to run:

```bash
$ dpkg -S /usr/lib/python3/dist-packages/pyewf.so
libewf-python3: /usr/lib/python3/dist-packages/pyewf.so
```

Another example here is *pyparsing*:

```
In [1]: import pyparsing

In [2]: pyparsing.__version__
Out[2]: '3.2.0'

In [3]: pyparsing.__file__
Out[3]: '/usr/lib/python3/dist-packages/pyparsing/__init__.py'

```

In this case the Python module is a package directory, to find out which
package it belongs to run:

```bash
$ dpkg -S /usr/lib/python3/dist-packages/pyparsing/__init__.py
python3-pyparsing: /usr/lib/python3/dist-packages/pyparsing/__init__.py
```

Once the package has been identified that contains the out-of-date dependency
the next step is to see if it is truly at the latest version.

```
$ apt-cache policy python3-pyparsing
python3-pyparsing:
  Installed: 3.2.0-1
  Candidate: 3.2.0-1
  Version table:
     3.3.0-1 500
        500 REPO
 *** 3.2.0-1 600
        600 REPO
        100 /var/lib/dpkg/status
```

Here you can see an example of *python3-pyparsing* that has version **3.2.0-1**
installed instead of version **3.3.0-1**, while Plaso requires version 3.3.0 or
later. To correct this you may have to specifically indicate the version you
want to install.

```bash
$ sudo apt install python3-pyparsing=3.3.0-1
```

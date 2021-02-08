# Troubleshooting installation issues

## Ubuntu

Installing the plaso on Ubuntu should be a breeze if you follow the
instructions [here](Ubuntu-Packaged-Release.md), however sometimes there can be
conflicting packages installed that cause plaso not to run properly. Most often
this is caused by either some unsupported versions of packages being installed
or if for some reason some of the dependencies was installed from source at
some point and those dependencies are out of date.

If you are having trouble getting plaso to run on your computer after following
the installation instructions one of the best first steps is to check if all
dependencies are met. One way of doing that is to download the check dependency
script and run it.

```bash
$ wget https://raw.githubusercontent.com/log2timeline/plaso/main/utils/check_dependencies.py
$ python check_dependencies.py
```

The output should be something on these lines:

```
Checking availability and versions of plaso dependencies.
[OK]		Crypto version: 2.6.1
[OK]		artifacts version: 20180827
[OK]		bencode
...
```

An `[ERROR]` status indicates that the version of the dependency is not
supported.

First make sure all currently installed packages are up-to-date by running:

```bash
$ sudo apt-get update
$ sudo apt-get upgrade
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
Out[2]: u'20140608'

In [3]: pyewf.__file__
Out[3]: '/usr/lib/python3.7/dist-packages/pyewf.so'
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
$ dpkg -S /usr/lib/python3.7/dist-packages/pyewf.so
libewf-python: /usr/lib/python3.7/dist-packages/pyewf.so
```

Another example here is *pyparsing*:

```
In [1]: import pyparsing

In [2]: pyparsing.__version__
Out[2]: '2.0.3'

In [3]: pyparsing.__file__
Out[3]: '/usr/lib/python3.7/dist-packages/pyparsing.pyc'

```

In this case the Python module is the ".pyc" file, which is not included in the
dpkg package:

```bash
$ dpkg -S /usr/lib/python3.7/dist-packages/pyparsing.pyc
dpkg-query: no path found matching pattern /usr/lib/python3.7/dist-packages/pyparsing.pyc
```

".pyc" is a "compiled" version of the Python code ".py", these are typically
not distributed by packages but generated on your system at installation or
first execution time. Therefore in order to find out which package this Python
module belongs to remove the final "c" so it becomes ".py" instead of ".pyc",
e.g.:

```bash
$ dpkg -S /usr/lib/python3.7/dist-packages/pyparsing.py
python-pyparsing: /usr/lib/python3.7/dist-packages/pyparsing.py
```

Once the package has been identified that contains the out-of-date dependency
the next step is to see if it is truly at the latest version.

```
$ apt-cache policy python-pyparsing
python-pyparsing:
  Installed: 2.0.2-1
  Candidate: 2.0.2-1
  Version table:
     2.0.3-1 0
        500 REPO
 *** 2.0.2-1 0
        600 REPO
        100 /var/lib/dpkg/status
```

Here you can see an example of *python-pyparsing* that has version **2.0.2-1**
installed instead of version **2.0.3-1**, which is required by Plaso. To
correct this you may have to specifically indicate the version you want to
install.

```bash
$ sudo apt-get install python-pyparsing=2.0.3-1
```

### Common package conflicts

#### PyParsing

The following traceback:

```
=======================
Traceback (most recent call last):
File "/usr/bin/log2timeline.py", line 28, in <module>
from plaso.frontend import frontend
File "/usr/lib/python3.7/dist-packages/plaso/frontend/frontend.py", line 36, in <module>
...
pyparsing.lineEnd())
TypeError: __call__() takes exactly 2 arguments (1 given)
========================
```

This is indicative that you are running an old version of pyparsing. Please
make sure you are using the latest version, see what is available using:

```bash
$ apt-cache policy python-pyparsing
```

And install the latest version.

#### libewf

There are some packages that declare **libewf2** as one of their dependencies.
This is an out dated version of the [libewf](https://github.com/libyal/libewf)
library provided by your distribution.

See for instance [this issue](https://github.com/log2timeline/plaso/issues/301).

The solution here is to remove the **libewf2** package from the system and
replace it with the **libewf**  package from the GIFT PPA.

```bash
$ sudo apt-get remove libewf2
```

Note that this may remove other packages as well that depend on **libewf2**,
which are likely to be out dated as well.

```bash
$ sudo apt-get install libewf libewf2=20140608-1
```

Installing **libewf2** from the GIFT PPA prevents your package manager
installing its own version of the libewf2 package when it does not need to,
since the necessary files are already provided by the **libewf** package.

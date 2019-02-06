# Building and Installing Dependencies on MacOS 

This page contains detailed instructions on how to build and install dependencies on Mac OS X.

There are multiple ways to install the dependencies on Ubuntu:

* Prepackaged dependencies;
* Using the [log2timeline devtools](https://github.com/log2timeline/devtools) to batch build most of the dependencies;
* Manual build of the dependencies.

**Note that if you have a non-Apple version of Python installed e.g. downloaded from Python.org, MacPorts or equivalent. You may very likely will have issues with version mismatches between the Apple versions and the non-Apple version of Python. It is therefore recommended to stick with the Apple versions of Python.**

## Prepackaged dependencies

[Moved](Dependencies.md#macos)

## Batch build

[Moved](Dependencies.md#batch-build)

## Manual build
It is impossible for us to support all flavors of Mac OS X out there, so if you want smooth sailing, we recommend sticking with the supported version or live with the fact that a manual build of the dependencies can be a tedious task.

For ease of maintenance the following instructions use as much pkg packages as possible. Note that the resulting pkg packages are not intended for public redistribution.

Alternative installation methods like installing directly from source, using easy_install or pip are [not recommended](https://stackoverflow.com/questions/3220404/why-use-pip-over-easy-install) because when not maintained correctly they can mess up your setup more easily than using rpm packages.

First create a build root directory:
```
mkdir plaso-build/
```

### Build essentials
Make sure the necessary building tools and development packages are installed on the system:

* Python 2.7 (or a later 2.x version)
* Python setuptools or distutils
* XCode
  * Command Line Tools
* Cython

#### Cython
Download the latest source package from: http://cython.org/#download

To build pkg files run the following command from the build root directory:
```
tar -zxvf Cython-0.23.1.tar.gz
cd Cython-0.23.1
python setup.py install --root=$PWD/tmp --install-data=/usr/local 
pkgbuild --root tmp --identifier org.cython.cython --version 0.23.1 --ownership recommended ../cython-0.23.1.pkg
cd ..
```

To install the required pkg files run:
```
sudo installer -target / -pkg cython-0.23.1.pkg
```

### Python modules
The following instructions apply to the following dependencies:

Name | Download URL | Identifier | Comments | Dependencies
--- | --- | --- | --- | --- 
artifacts | https://github.com/ForensicArtifacts/artifacts/releases | com.github.ForensicArtifacts.artifacts | |
bencode | https://pypi.python.org/pypi/bencode | org.python.pypi.bencode | |
biplist | https://pypi.python.org/pypi/biplist | org.python.pypi.biplist | |
dateutil | https://pypi.python.org/pypi/python-dateutil | com.github.dateutil.dateutil | |
google-apputils | https://pypi.python.org/pypi/google-apputils | com.github.google.google-apputils | |
PyParsing | http://sourceforge.net/projects/pyparsing/files/ | net.sourceforge.pyparsing | |
pytz | https://pypi.python.org/pypi/pytz | org.python.pypi.pytz | |
pyzmq | https://pypi.python.org/pypi/pyzmq | com.github.zeromq.pyzmq | Needs Cython to build |
requests | https://github.com/kennethreitz/requests/releases | com.github.kennethreitz.requests | Make sure to click on: "Show # newer tags" |
six | https://pypi.python.org/pypi/six#downloads | org.python.pypi.six | |
yara-python | https://github.com/VirusTotal/yara-python | | 

#### Building a PKG
To build pkg files run the following commands from the build root directory.

First extract the package:
```
tar -zxvf package-1.0.0.tar.gz 
```

Next change into the package source directory and have setup.py build and install the package:
```
cd package-1.0.0/
python setup.py install --root=$PWD/tmp --install-data=/usr/local 
```

This will install package in:
```
tmp
```

Next create a pgk
```
pkgbuild --root tmp --identifier $IDENTIFIER --version 1.0.0 --ownership recommended ../package-1.0.0.pkg
cd ..
```

Where ` $IDENTIFIER` contains an unique identifier for the package e.g. com.github.ForensicArtifacts.artifacts for artifacts.

To install the required pkg files run:
```
sudo installer -target / -pkg package-1.0.0.pkg
```

### dfVFS
The dfVFS build instructions can be found [here](https://github.com/log2timeline/dfvfs/wiki/Building). Note that for dfVFS to function correctly several dependencies, like pytsk, mentioned later in a section of this page, are required.

Download the latest source package from: https://github.com/log2timeline/dfvfs/releases

To build pkg files run the following command from the build root directory:
```
tar xfvz dfvfs-20140219.tar.gz
cd dfvfs-20140219/
python setup.py install --root=$PWD/tmp --install-data=/usr/local
pkgbuild --root tmp --identifier com.github.log2timeline.dfvfs --version 20140219 --ownership recommended python-dfvfs-20140219.pkg
cd ..
```

To install the required pkg files run:
```
sudo installer -target / -pkg python-dfvfs-20140219.pkg
```

#### gnureadline
Download the latest source package from: https://pypi.python.org/pypi/gnureadline

To build pkg files run the following command from the build root directory:
```
tar xfv gnureadline-6.3.3.tar.gz 
cd gnureadline-6.3.3
python setup.py install --root=$PWD/tmp --install-data=/usr/local 
pkgbuild --root tmp --identifier org.python.pypi.gnureadline --version 6.3.3 --ownership recommended ../gnureadline-6.3.3.pkg
```

To install the required pkg files run:
```
sudo installer -target / -pkg gnureadline-6.3.3.pkg
```

### libyal
The following instructions apply to the following dependencies:

Name | Download URL | Comments | Dependencies
--- | --- | --- | --- 
libbde | https://github.com/libyal/libbde | | libfuse
libesedb | https://github.com/libyal/libesedb | |
libevt | https://github.com/libyal/libevt | |
libevtx | https://github.com/libyal/libevtx | |
libewf | https://github.com/libyal/libewf | | libfuse, zlib
libfsntfs | https://github.com/libyal/libfsntfs | |
libfvde | https://github.com/libyal/libfvde | | libfuse, zlib
libfwsi | https://github.com/libyal/libfwsi | |
liblnk | https://github.com/libyal/liblnk | |
libmsiecf | https://github.com/libyal/libmsiecf | |
libolecf | https://github.com/libyal/libolecf | | libfuse
libqcow | https://github.com/libyal/libqcow | | libfuse, zlib
libregf | https://github.com/libyal/libregf | | libfuse
libscca | https://github.com/libyal/libscca | |
libsigscan | https://github.com/libyal/libsigscan | |
libsmdev | https://github.com/libyal/libsmdev | |
libsmraw | https://github.com/libyal/libsmraw | | libfuse
libvhdi | https://github.com/libyal/libvhdi | | libfuse
libvmdk | https://github.com/libyal/libvmdk | | libfuse, zlib
libvshadow | https://github.com/libyal/libvshadow | | libfuse

Install the following dependencies for building libyal:

* zlib
* bzip2

**TODO: describe building dependencies.**

Since the build process for the libyal libraries is very similar, the following paragraph provides building libevt as an example. For more details see the build instructions of the individual projects e.g. https://github.com/libyal/libevt/wiki/Building.

Note that there is also a script to batch build the libyal dependencies more information here: https://github.com/log2timeline/l2tdevtools/wiki/Build-script

#### Example: libevt and Python-bindings
Download the latest source package from: https://github.com/libyal/libevt/releases

**Note that Mac OS X 10.11 (El Capitan) disallows installation in /usr by default, hence we use /usr/local**

To build pkg files run the following command from the build root directory:
```
tar xfvz libevt-alpha-20130415.tar.gz
cd libevt-alpha-20130415
./configure --disable-dependency-tracking --prefix=/usr/local --enable-python --with-pyprefix
make && make install DESTDIR=$PWD/osx-pkg
mkdir -p $PWD/osx-pkg/usr/share/doc/libevt
cp LICENSE $PWD/osx-pkg/usr/share/doc/libevt
pkgbuild --root osx-pkg --identifier com.github.libyal.libevt --version 20130415 --ownership recommended ../libevt-20130415.pkg
```

To install the required pkg files run:
```
sudo installer -target / -pkg libevt-20130415.pkg
```

### Libyaml and Python-bindings
Download the latest source package from: http://pyyaml.org/download/libyaml/ (or http://pyyaml.org/wiki/LibYAML)

**Note that Mac OS X 10.11 (El Capitan) disallows installation in /usr by default, hence we use /usr/local**

To build pkg files run the following command from the build root directory:
```
tar xfvz yaml-0.1.6.tar.gz
cd yaml-0.1.6
./configure --prefix=/usr/local
make
make install DESTDIR=$PWD/osx-pkg
pkgbuild --root osx-pkg --identifier org.pyyaml.yaml --version 0.1.6 --ownership recommended ../libyaml-0.1.6.pkg
cd ..
```

To install the required pkg files run:
```
sudo installer -target / -pkg libyaml-0.1.6.pkg
```

Download the latest source package from: http://pyyaml.org/wiki/PyYAML

To build pkg files run the following command from the build root directory:
```
tar xfvz PyYAML-3.11.tar.gz
cd PyYAML-3.11/
python setup.py install --root=$PWD/tmp --install-data=/usr/local 
pkgbuild --root tmp --identifier org.pyyaml.yaml.python --version 3.11 --ownership recommended ../python-yaml-3.11.pkg
```

To install the required pkg files run:
```
sudo installer -target / -pkg python-yaml-3.11.pkg
```

### Liblzma and Python-bindings
Download the latest source package from: http://tukaani.org/xz/

**Note that Mac OS X 10.11 (El Capitan) disallows installation in /usr by default, hence we use /usr/local**

To build pkg files run the following command from the build root directory:
```
tar xfvz xz-5.2.3.tar.gz
cd xz-5.2.3
./configure --prefix=/usr/local
make
make install DESTDIR=$PWD/osx-pkg
pkgbuild --root osx-pkg --identifier org.tukaani.xz --version 5.2.3 --ownership recommended ../xz-5.2.3.pkg
cd ..
```

To install the required pkg files run:
```
sudo installer -target / -pkg xz-5.2.3.pkg
```

Download the latest source package from: https://pypi.python.org/pypi/pyliblzma

To build pkg files run the following command from the build root directory:
```
tar xfvz pyliblzma-0.5.3.tar.gz
cd pyliblzma-0.5.3/
python setup.py install --root=$PWD/tmp --install-data=/usr/local 
pkgbuild --root tmp --identifier org.python.pypi.pyliblzma --version 0.5.3 --ownership recommended ../python-lzma-0.5.3.pkg
```

To install the required pkg files run:
```
sudo installer -target / -pkg python-lzma-0.5.3.pkg
```

### Pefile
Download the latest source package from: https://github.com/erocarrera/pefile/releases

**TODO describe manual fixes**

To build pkg files run the following command from the build root directory:
```
tar -zxvf pefile-1.2.10-139.tar.gz
cd pefile-pefile-1.2.10-139/
python setup.py install --root=$PWD/tmp --install-data=/usr/local 
pkgbuild --root tmp --identifier com.github.erocarrer.pefile --version 1.2.10-139 --ownership recommended ../python-pefile-1.2.10-139.pkg
cd ..
```

To install the required pkg files run:
```
sudo installer -target / -pkg python-pefile-1.2.10-139.pkg
```

### Pyparsing
Remove an outdated version of pyparsing distributed by Max OS X:

```
sudo rm /System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/pyparsing*
```

**Note that Mac OS X 10.11 (El Capitan) disallows removing these files.**

On El Capitan we recommend overriding PYTHONPATH:
```
PYTHONPATH=/Library/Python/2.7/site-packages/ log2timeline.py
```

Which you can alias e.g.
```
alias log2timeline.py="PYTHONPATH=/Library/Python/2.7/site-packages/ log2timeline.py"
```

To be able to remove the files you'll have to disable System Integrity Protection (SIP or rootless).

### Psutil
Download the latest source package from: https://pypi.python.org/pypi/psutil/#downloads

To build pkg files run the following command from the build root directory:
```
tar xvfz psutil-1.2.1.tar.gz
cd psutil-1.2.1/
python setup.py install --root=$PWD/tmp --install-data=/usr/local 
pkgbuild --root tmp --identifier org.python.pypi.psutil --version 1.0 --ownership recommended ../python-psutil-1.2.1.pkg
cd ..
```

To install the required pkg files run:
```
sudo installer -target / -pkg python-psutil-1.2.1.pkg
```

### Pytsk
The build and install Pytsk see:

* https://github.com/py4n6/pytsk/wiki/Building#using-mac-os-x-pkgbuild

### SQLite
**TODO describe**

### Optional dependencies for output modules
#### elasticsearch-py
Download the latest source package from: https://github.com/elastic/elasticsearch-py

**TODO: describe**

#### XlsxWriter
Download the latest source package from: https://github.com/jmcnamara/XlsxWriter/releases

To build pkg files run the following command from the build root directory:
```
tar zxfv XlsxWriter-RELEASE_0.7.3.tar.gz
cd XlsxWriter-RELEASE_0.7.3/
python setup.py install --root=$PWD/tmp --install-data=/usr/local 
pkgbuild --root tmp --identifier com.github.jmcnamara.xlsxwriter --version 0.7.3 --ownership recommended ../python-xlsxwriter-0.7.3.pkg
cd ..
```

To install the required pkg files run:
```
sudo installer -target / -pkg python-xlsxwriter-1.0.pkg
```

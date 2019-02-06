# Building and Installing Dependencies on Windows 

This page contains detailed instructions on how to build and install dependencies on Windows.

There are multiple ways to install the dependencies on Windows:

* Prepackaged dependencies;
* Using the [log2timeline devtools](https://github.com/log2timeline/devtools) to batch build most of the dependencies;
* Manual build of the dependencies.

## Prepackaged dependencies

[Moved](Dependencies.md#windows)

## Batch build

[Moved](Dependencies.md#batch-build)

## Manual build

For ease of maintenance the following instructions use as much MSI package files as possible via "Programs and Features". Note that the resulting MSI files are not intended for public redistribution.

**Note that when making MSI packages, make sure the remove the previous versions before installing the newer version.**

Alternative installation methods like installing directly from source, using easy_install or pip are [not recommended](https://stackoverflow.com/questions/3220404/why-use-pip-over-easy-install) because when not maintained correctly they can mess up your setup more easily than using MSIs. E.g. easy_installer and pip do not always remove older versions, though Python distutil generated MSI packages don't detect and remove previous versions either it is less likely you'll end up with multiple different versions of the same package installed side-by-side.

If you run into problems building, installing or running the dependencies first check: [Troubleshooting](Troubleshooting-Windows.md).

### Build essentials

Make sure the necessary building tools and development packages are installed on the system:

* [Python 2.7 Windows installation](http://python.org/download/)
* [Python setup tools](http://pypi.python.org/pypi/setuptools/)
* [Microsoft Visual Studio C++ Compiler](https://wiki.python.org/moin/WindowsCompilers)
* Cython

**Note that plaso itself is platform independent but if you use a 64-bit version of Python all of the dependencies should be compiled as 64-bit.**

First create a build root directory:
```
C:\plaso-build\
```

#### Cython

Download the latest source package from: http://cython.org/#download

To build the MSI file run the following commands from the build root directory:
```
tar xfv Cython-0.23.1.tar.gz
cd Cython-0.23.1
C:\Python27\python.exe setup.py bdist_msi
cd ..
```

This will create a MSI in the dist sub directory e.g.:
```
dist\Cython-0.23.1.win32-py2.7.msi
```

Install the MSI.

### Python modules

The following instructions apply to the following dependencies:

Name | Download URL | Comments | Dependencies
--- | --- | --- | --- 
artifacts | https://github.com/ForensicArtifacts/artifacts/releases | |
bencode | https://pypi.python.org/pypi/bencode | |
biplist | https://pypi.python.org/pypi/biplist | |
dateutil | https://pypi.python.org/pypi/python-dateutil | |
dfdatetime | https://github.com/log2timeline/dfdatetime/releases | |
dfvfs | https://github.com/log2timeline/dfvfs/releases | |
dfwinreg | https://github.com/log2timeline/dfwinreg/releases | |
google-apputils | https://pypi.python.org/pypi/google-apputils | |
pefile | https://github.com/erocarrera/pefile/releases | |
psutil | https://pypi.python.org/pypi/psutil | |
PyParsing | http://sourceforge.net/projects/pyparsing/files/ | 2.0.3 or later 2.x version |
pytsk | https://github.com/py4n6/pytsk/releases | |
pytz | https://pypi.python.org/pypi/pytz | |
PyYAML | http://pyyaml.org/wiki/PyYAML | |
pyzmq | https://pypi.python.org/pypi/pyzmq | Needs Cython to build |
requests | https://github.com/kennethreitz/requests/releases | Make sure to click on: "Show # newer tags" | 
six | https://pypi.python.org/pypi/six#downloads | |
yara-python | https://github.com/VirusTotal/yara-python | | 
XlsxWriter | https://github.com/jmcnamara/XlsxWriter/releases | |

#### Building a MSI

Setup.py allows you to easily build a MSI in most cases. This paragraph contains a generic description of building a MSI so we do not have to repeat this for every dependency.

To build a MSI file from package-1.0.0.tar.gz run the following commands from the build root directory.

First extract the package:
```
tar zxvf package-1.0.0.tar.gz
```

If you are not familiar with extracting tar files on Windows see: [How to unpack a tar file in Windows](https://wiki.haskell.org/How_to_unpack_a_tar_file_in_Windows)

Next change into the package source directory and have setup.py build a MSI:
```
cd package-1.0.0\
C:\Python27\python.exe setup.py bdist_msi
```

This will create a MSI in the dist sub directory e.g.:
```
dist\package-1.0.0.win32.msi
```

Note that the actual MSI file name can vary per package.

To install the MSI from the command line:
```
msiexec.exe /i dist\package-1.0.0.win32.msi /q
```

### libyal

The following instructions apply to the following dependencies:

Name | Download URL | Comments | Dependencies
--- | --- | --- | --- 
libbde | https://github.com/libyal/libbde | | 
libesedb | https://github.com/libyal/libesedb | |
libevt | https://github.com/libyal/libevt | |
libevtx | https://github.com/libyal/libevtx | |
libewf | https://github.com/libyal/libewf-legacy | | zlib
libfsntfs | https://github.com/libyal/libfsntfs | |
libfvde | https://github.com/libyal/libfvde | | 
libfwnt | https://github.com/libyal/libfwnt | |
libfwsi | https://github.com/libyal/libfwsi | |
liblnk | https://github.com/libyal/liblnk | |
libmsiecf | https://github.com/libyal/libmsiecf | |
libolecf | https://github.com/libyal/libolecf | | 
libqcow | https://github.com/libyal/libqcow | | 
libregf | https://github.com/libyal/libregf | | 
libscca | https://github.com/libyal/libscca | |
libsigscan | https://github.com/libyal/libsigscan | |
libsmdev | https://github.com/libyal/libsmdev | |
libsmraw | https://github.com/libyal/libsmraw | | 
libvhdi | https://github.com/libyal/libvhdi | | 
libvmdk | https://github.com/libyal/libvmdk | | 
libvshadow | https://github.com/libyal/libvshadow | | 

Install the following dependencies for building libyal:

* zlib

**TODO: describe building dependencies.**

Since the build process for the libyal libraries is very similar, the following paragraph provides building libevt as an example. For more details see the build instructions of the individual projects e.g. https://github.com/libyal/libevt/wiki/Building.

Note that there is also a script to batch build the libyal dependencies more information here: https://github.com/log2timeline/l2tdevtools/wiki/Build-script

#### Example: libevt and Python-bindings

Download the latest source package from: https://github.com/libyal/libevt/releases

Extract the source package:
```
tar xfv libevt-alpha-20131013.tar.gz
```

Next change into the package source directory and have setup.py build a MSI:
```
cd libevt-20131013
C:\Python27\python.exe setup.py bdist_msi
```

This will create a MSI in the dist sub directory e.g.:
```
dist\pyevt-20131013.1.win32-py2.7.msi
```

Install the MSI.

### pysqlite

By default Python 2.7 comes with pysqlite 2.6.0 which works fine in combination with sqlite3 version 3.7.8.

Follow the instructions below if you wish to update pysqlite to a newer version.

Download the latest source package from: https://pypi.python.org/pypi/pysqlite

**TODO: describe what changes are necessary to get this working, DLL import and find the sqlite3.h include header.**

To build the MSI file run the following commands from the build root directory:
```
tar xfv pysqlite-2.6.3.tar.gz
cd pysqlite-2.6.3\
cp ..\sqlite3\sqlite3.h src\
cp ..\sqlite3\msvscpp\Release\sqlite3.dll .
cp ..\sqlite3\msvscpp\Release\sqlite3.lib .
C:\Python27\python.exe setup.py bdist_msi
cd ..
```

This will create a MSI in the dist sub directory e.g.:
```
dist\pysqlite-2.6.3.win32.msi
```

Remove:
```
C:\Python27\DLL\sqlite3.dll
C:\Python27\DLL\_sqlite3.pyd
C:\Python27\Lib\sqlite3\
```

Install the MSI.

Copy sqlite3.dll to:
```
C:\Python27\Lib\site-package\pysqlite2\
```

### pywin32

Download the latest installer from: http://sourceforge.net/projects/pywin32/files/pywin32/

### SQLite

Plaso requires at least sqlite3 version 3.7.8. By default Python 2.7 comes with a far older version that cannot handle newer FireFox sqlite3 database files.

Download the latest source package from: http://www.sqlite.org/download.html

E.g. sqlite-amalgamation-3080100.zip

Extract the source package in the build root directory.

Download the [sqlite3 Visual Studio 2008 solution files](https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg/3rd%20party/build-files/sqlite3-vs2008.zip).

Extract the sqlite3 Visual Studio 2008 solution files in the sqlite-amalgamation source directory.

Open the Microsoft Visual Studio 2008 solution file:
```
C:\plaso-build\sqlite-amalgamation-3080100\msvscpp\sqlite3.sln
```

Build the solution.

If the build is successful copy the SQLite DLL to your Python installation:
```
copy C:\plaso-build\sqlite-amalgamation-3080100\msvscpp\Release\sqlite3.dll C:\Python27\DLLs\
```

### Optional dependencies for output modules
#### elasticsearch-py
Download the latest source package from: https://github.com/elastic/elasticsearch-py

**TODO: describe**

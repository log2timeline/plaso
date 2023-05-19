## Packaging with PyInstaller

**Note that packaging with PyInstaller is no longer a supported build method.
You are expected to be able to debug and fix build issues yourself.**

To create a Windows packaged release from the development release you also need:

* PyInstaller

### PyInstaller

Download the latest source from:

```
git clone -b master git://github.com/pyinstaller/pyinstaller.git
```

**Note that setup.py build and install is currently disabled, so we need to run
PyInstaller from its download directory.**

#### Microsoft Visual C++ Redistributable Package

If you're building with Visual Studio note that for some reason PyInstaller
does not include the Microsoft Visual C++ run-time DLLs you can find them here:
[The latest supported Visual C++ downloads](https://learn.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-160)

### Preparations

If you are intending to build a PyInstaller packaged release make sure the
dependencies are up to date.

You can easility update the dependencies with the l2tdevtools
[update script](https://github.com/log2timeline/l2tdevtools/wiki/Update-script).

To update or install install dependencies with l2tdevtools run the following
command from the l2tdevtools source directory:

```
set PYTHONPATH=.
C:\Python3\python.exe tools\update.py --preset plaso --track stable
```

### Packaging

Download a copy of the [make_release.ps1](https://raw.githubusercontent.com/log2timeline/l2tdevtools/main/data/pyinstaller/make_release.ps1)
script. The easiest is to git clone l2tdevtools:

```
git clone https://github.com/log2timeline/l2tdevtools.git
```

First check if the make_release.ps1 script is configured correctly for your
build environment.

From the Plaso source directory run the following commands:

Build Plaso with PyInstaller:

```
..\l2tdevtools\data\pyinstaller\make_release.ps1
```

This will create: `plaso-<version>-<architecture>.zip`

To do a very rudimentary test to see if the packaged binaries work run:

```
..\l2tdevtools\data\pyinstaller\make_check.bat
```

#### Packaging win32 on amd64

To create a win32 build on an amd64 system make sure you've installed the 32-bit version of Python 3.7.

From the l2tdevtools source directory run:

```
set PYTHONPATH=.
C:\Python3 (x86)\python.exe tools\update.py --machine-type x86 --preset plaso --track stable
```

From the Plaso source directory run:

```
..\l2tdevtools\data\pyinstaller\make_release.ps1 -Architecture win32
```

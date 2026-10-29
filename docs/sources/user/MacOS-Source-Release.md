# MacOS Source release

**WARNING: these instructions assume you are comfortable troubleshooting Python
module installation issues. If not we strongly encourage using the Docker
installation instead.**

To install the "Source code" release of Plaso on Mac OS you need to download the
latest version from https://github.com/log2timeline/plaso/releases/latest

For the purposes of this guide it will use 20261025 to represent the latest
Plaso release in the examples below. However, you will need to adjust this
based on the latest version available from the link above.

Under the latest release you should see four links to different packages, you
will need to download the "**Source code (tar.gz)**" package file, for example
https://github.com/log2timeline/plaso/archive/20261025.tar.gz

Extract the source code:

```
cd /tmp
tar zxf ~/Downloads/plaso-20261025.tar.gz
```

In some cases, Mac OS will automatically ungzip the downloaded file. In which
case, untar with:

```
cd /tmp
tar xf ~/Downloads/plaso-20261025.tar
```

XCode Command Line Tools is required. It can be installed with:

```
xcode-select --install
```

Python 3.10 or later is required. If python3 is not already installed, it can
be downloaded from https://www.python.org/downloads/

## Install Plaso contained within a virtual environment

Plaso can be installed within a virtual environment so that dependency packages
are not installed system-wide.

Create a virtual environment to install Plaso into (in this instance, it is
named "plaso_env" created under the home directory):

```
python3 -m venv ~/plaso_env
```

Activate the virtual environment:

```
source ~/plaso_env/bin/activate
```

Install Plaso and its dependencies:

```
cd /tmp/plaso-20261025/
pip install .
```

To deactivate the virtual environment:

```
deactivate
```

*In order to run Plaso, the virtual environment needs to be activated.*

## Troubleshooting

Some Python dependencies fail to compile with the error:

```
  clang: warning: no such sysroot directory: '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.14.sdk' [-Wmissing-sysroot]
  ...
  #include <stdio.h>
           ^~~~~~~~~
  1 error generated.
  error: command 'clang' failed with exit status 1
```

It is likely that the Python interpreter was built using a specific Mac OS SDK.
Make sure that version of the Mac OS SDK is installed on your system, in the
example above this is Mac OS SDK 10.14.

Yara-python fails to build with the error:

```
    In file included from yara/libyara/libyara.c:45:
    yara/libyara/crypto.h:38:10: fatal error: 'openssl/crypto.h' file not found
    #include <openssl/crypto.h>
             ^~~~~~~~~~~~~~~~~~
    1 error generated.
    error: command 'clang' failed with exit status 1
    ----------------------------------------
```

Make sure you have openssl installed:

```
brew install openssl@3
```

And your build environment knows where to find its development files:

```
export CFLAGS="-I$(brew --prefix openssl@3)/include ${CFLAGS}";
export LDFLAGS="-L$(brew --prefix openssl@3)/lib ${LDFLAGS}";
```

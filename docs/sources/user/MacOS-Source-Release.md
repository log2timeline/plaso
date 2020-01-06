# MacOS Source Release

To install the source release of plaso on MacOS you need to download the latest version from https://github.com/log2timeline/plaso/releases

Attached to the most recent release (as of this time version 20190708) is a "Source code (tar.gz)" file.

Extract the source code:
```
cd /tmp
tar zxf ~/Downloads/plaso-20190708.tar.gz
```

In some cases, MacOS will automatically ungzip the downloaded file. In which case, untar with:
```
cd /tmp
tar xf ~/Downloads/plaso-20190708.tar
```

XCode Command Line Tools is required. It can be installed with:
```
xcode-select --install
```

If python3 is not already installed, it can be downloaded from https://www.python.org/downloads/

## Install plaso contained within a virtual environment

Plaso can be installed within a virtual environment so that dependency packages are not installed system-wide.
To do this, install Virtualenv:
```
sudo pip3 install virtualenv
```

Create a virtual environment to install plaso into (in this instance, it's named "plaso_env" created under the home directory):
```
virtualenv -p python3 ~/plaso_env
```

Activate the virtual environment:
```
source ~/plaso_env/bin/activate
```

Install the plaso dependencies:
```
cd /tmp/plaso-20190708/
pip install -r requirements.txt
```

Install plaso:
```
python setup.py build
python setup.py install
```

To deactivate the virtual environment:
```
deactivate
```

*In order to run plaso, the virtual environment needs to be activated.*

## Install plaso system-wide

Install the plaso dependencies:
```
cd /tmp/plaso-20190708/
sudo pip3 install -r requirements.txt
```

Install plaso:
```
python3 setup.py build
sudo python3 setup.py install
```

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

It is likely that the Python interpreter was built using a specific MacOS SDK.
Make sure that version of the MacOS SDK is installed on your system, in the
example above this is MacOS SDK 10.14.


Pycrypto fails to build with the error:

```
    src/_fastmath.c:36:11: fatal error: 'gmp.h' file not found
    # include <gmp.h>
              ^~~~~~~
    1 error generated.
    error: command 'clang' failed with exit status 1
    ----------------------------------------
```

Make sure you have gmp installed:

```
brew install gmp
```

And your build environment knows where to find its development files:

```
export CFLAGS="-I/usr/local/include ${CFLAGS}";
export LDFLAGS="-L/usr/local/lib ${LDFLAGS}";
```


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
brew install openssl
```

And your build environment knows where to find its development files:

```
export CFLAGS="-I/usr/local/opt/openssl@1.1/include ${CFLAGS}";
export LDFLAGS="-L/usr/local/opt/openssl@1.1/lib ${LDFLAGS}";
```


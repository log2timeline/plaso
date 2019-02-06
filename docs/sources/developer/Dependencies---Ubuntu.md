# Building and Installing Dependencies on Ubuntu

This page contains detailed instructions on how to build and install dependencies on Ubuntu. Some of these instructions should also work on Ubuntu like systems like Debian or Linux Mint.

There are multiple ways to install the dependencies on Ubuntu:

* Using the GIFT PPA to install prepackaged versions of the dependencies;
* Using the [log2timeline devtools](https://github.com/log2timeline/devtools) to batch build most of the dependencies;
* Manual build of the dependencies.

## Prepackaged dependencies

[Moved](Dependencies.md#ubuntu)

## Batch build

[Moved](Dependencies.md#batch-build)

## Manual build
It is impossible for us to support all flavors of Ubuntu out there, so if you want smooth sailing, we recommend sticking with the supported version or live with the fact that a manual build of the dependencies can be a tedious task.

For ease of maintenance the following instructions use as much deb package files as possible. Note that the resulting deb files are not intended for public redistribution.

Alternative installation methods like installing directly from source, using easy_install or pip are [not recommended](https://stackoverflow.com/questions/3220404/why-use-pip-over-easy-install) because when not maintained correctly they can mess up your setup more easily than using deb packages.

First create a build root directory:
```
mkdir plaso-build/
```

Next make sure your installation is up to date:
```
sudo apt-get update
sudo apt-get upgrade
```

### Build essentials
Make sure the necessary building tools and development packages are installed on the system:
```
sudo apt-get install build-essential autotools-dev libsqlite3-dev python-dev debhelper devscripts fakeroot quilt git mercurial python-setuptools libtool automake
```


### Python modules
The following instructions apply to the following dependencies:

Name | Download URL | Comments | Dependencies
--- | --- | --- | --- 
artifacts | https://github.com/ForensicArtifacts/artifacts/releases | Comes with dpkg files |
bencode | https://pypi.python.org/pypi/bencode | |
biplist | https://pypi.python.org/pypi/biplist | |
dateutil | https://pypi.python.org/pypi/python-dateutil | |
google-apputils | https://pypi.python.org/pypi/google-apputils | |
PyParsing | http://sourceforge.net/projects/pyparsing/files/ | 2.0.3 or later 2.x version |
pytz | https://pypi.python.org/pypi/pytz | |
PyYAML | http://pyyaml.org/wiki/PyYAML | |
pyzmq | https://pypi.python.org/pypi/pyzmq | Needs Cython to build |
requests | https://github.com/kennethreitz/requests/releases | Make sure to click on: "Show # newer tags" | 
six | https://pypi.python.org/pypi/six#downloads | |
yara-python | https://github.com/VirusTotal/yara-python | | 

Some of these Python modules can be directly installed via apt-get:
```
sudo apt-get install python-yaml
```

#### Building a deb
First extract the package:
```
tar zxvf package-1.0.0.tar.gz
```

Next change into the package source directory:
```
cd package-1.0.0\
```

Some of the Python modules come with dpkg files stored in ```config/dpkg```. For those Python modules copy the dpkg files to a debian sub directory:
```
cp -rf config/dpkg debian
```

For those that don't come with dpkg files you can use [dpkg-generate.py](https://github.com/log2timeline/l2tdevtools/blob/master/tools/dpkg-generate.py) to generate them e.g.:
```
PYTHONPATH=l2tdevtools l2tdevtools/tools/dpkg-generate.py --source-directory=. package
mv dpkg debian
```

Have dpkg-buildpackage build the deb file:
```bash
dpkg-buildpackage -rfakeroot
```

This will create the following files in the build root directory:
```bash
python-package-1.0.0-1_all.deb
```

Note that the actual deb file name can vary per package.

To install the required deb files run:
```bash
sudo dpkg -i python-package-1.0.0-1_all.deb
```

### dfVFS
The dfVFS build instructions can be found [here](https://github.com/log2timeline/dfvfs/wiki/Building). Note that for dfVFS to function correctly several dependencies, like pytsk, mentioned later in a section of this page, are required.

Download the latest source package from: https://github.com/log2timeline/dfvfs/releases

To build deb files run the following command from the build root directory:
```bash
tar xvf dfvfs-20140219.tar.gz 
cd dfvfs-20140219/
cp -rf dpkg debian
dpkg-buildpackage -rfakeroot
cd ...
```

This will create the following files in the build root directory:
```
python-dfvfs_20140219-1_all.deb
```

To install the required deb files run:
```bash
sudo dpkg -i python-dfvfs_20140219-1_all.deb
```

### libyal
The following instructions apply to the following dependencies:

Name | Download URL | Comments | Dependencies
--- | --- | --- | --- 
libbde | https://github.com/libyal/libbde | | libfuse, libcrypto
libesedb | https://github.com/libyal/libesedb | |
libevt | https://github.com/libyal/libevt | |
libevtx | https://github.com/libyal/libevtx | |
libewf | https://github.com/libyal/libewf | | libfuse, libcrypto, zlib
libfsntfs | https://github.com/libyal/libfsntfs | |
libfvde | https://github.com/libyal/libfvde | | libfuse, libcrypto, zlib
libfwsi | https://github.com/libyal/libfwsi | |
liblnk | https://github.com/libyal/liblnk | |
libmsiecf | https://github.com/libyal/libmsiecf | |
libolecf | https://github.com/libyal/libolecf | | libfuse
libqcow | https://github.com/libyal/libqcow | | libfuse, zlib
libregf | https://github.com/libyal/libregf | | libfuse
libscca | https://github.com/libyal/libscca | |
libsigscan | https://github.com/libyal/libsigscan | |
libsmdev | https://github.com/libyal/libsmdev | |
libsmraw | https://github.com/libyal/libsmraw | | libfuse, libcrypto
libvhdi | https://github.com/libyal/libvhdi | | libfuse
libvmdk | https://github.com/libyal/libvmdk | | libfuse, zlib
libvshadow | https://github.com/libyal/libvshadow | | libfuse

Install the following dependencies for building libyal:
```
sudo apt-get install bzip2-dev libfuse-dev libssl-dev zlib1g-dev
```

Since the build process for the libyal libraries is very similar, the following paragraph provides building libevt as an example. For more details see the build instructions of the individual projects e.g. https://github.com/libyal/libevt/wiki/Building.

Note that there is also a script to batch build the libyal dependencies more information here: https://github.com/log2timeline/l2tdevtools/wiki/Build-script

#### Example: libevt and Python-bindings
Download the latest source package from: https://github.com/libyal/libevt/releases

To build deb files run the following command from the build root directory:
```
tar xfv libevt-alpha-20150105.tar.gz
cd libevt-20130923
cp -rf dpkg debian
dpkg-buildpackage -rfakeroot
cd ..
```

This will create the following files in the build root directory:
```
libevt_20150105-1_amd64.deb
libevt-dbg_20150105-1_amd64.deb
libevt-dev_20150105-1_amd64.deb
libevt-python_20150105-1_amd64.deb
libevt-python-dbg_20150105-1_amd64.deb
libevt-tools_20150105-1_amd64.deb
```

To install the required deb files run:
```
sudo dpkg -i libevt_20150105-1_amd64.deb libevt-python_20150105-1_amd64.deb
```

### Libyaml and Python-bindings
To install libyaml and Python-bindings run:
```
sudo apt-get install libyaml-0-2 python-yaml
```

### Pefile
**TODO describe**

### psutil
To install psutil run:
```
sudo apt-get install python-psutil
```

### PySQLite
Install the following dependencies for building PySQLite:
```
sudo apt-get install libsqlite3-dev
```

**TODO describe**

### Pytsk

The build and install Pytsk see:

* https://github.com/py4n6/pytsk/wiki/Building

### Optional dependencies for output modules
#### elasticsearch-py
Download the latest source package from: https://github.com/elastic/elasticsearch-py

**TODO: describe**

#### XlsxWriter
Download the latest source package from: https://github.com/jmcnamara/XlsxWriter/releases

**TODO describe obtaining packing files**

To build deb files run the following command from the build root directory:
```
tar xvf XlsxWriter-RELEASE_0.7.7.tar.gz
cd XlsxWriter-RELEASE_0.7.7
cp -rf config/dpkg debian
dpkg-buildpackage -rfakeroot
cd ..
```

This will create the following files in the build root directory:
```
python-xlsxwriter-0.7.7-1_all.deb
```

To install the required deb files run:
```
sudo dpkg -i python-xlsxwriter-0.7.7-1_all.deb
```

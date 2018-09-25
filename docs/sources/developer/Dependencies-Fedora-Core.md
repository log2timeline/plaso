## Manual build

It is impossible for us to support all flavors of Fedora Core out there, so if you want smooth sailing, we recommend sticking with the supported version or live with the fact that a manual build of the dependencies can be a tedious task.

For ease of maintenance the following instructions use as much rpm package files as possible. Note that the resulting rpm files are not intended for public redistribution.

Alternative installation methods like installing directly from source, using easy_install or pip are [not recommended](https://stackoverflow.com/questions/3220404/why-use-pip-over-easy-install) because when not maintained correctly they can mess up your setup more easily than using rpm packages.

First create a build root directory:

```
mkdir plaso-build/
```

Next make sure your installation is up to date:

```
sudo dnf update
```

### Build essentials

Make sure the necessary building tools and development packages are installed on the system:
```
sudo dnf groupinstall "Development Tools"
sudo dnf install gcc-c++ python-devel python-setuptools rpm-build git mercurial
```

**TODO: move to libyal section.**

For some of the dependent packages you also require:

```
sudo dnf install flex byacc zlib-devel bzip2-devel openssl-devel fuse-devel
```

### Python modules

The following instructions apply to the following dependencies:

Name | Download URL | Comments | Dependencies
--- | --- | --- | --- 
artifacts | https://github.com/ForensicArtifacts/artifacts/releases | |
bencode | https://pypi.python.org/pypi/bencode | |
binplist | https://github.com/google/binplist/releases | |
construct | https://pypi.python.org/pypi/construct#downloads | 2.5.2 or later 2.x version | six
dateutil | https://pypi.python.org/pypi/python-dateutil | |
dpkt | https://pypi.python.org/pypi/dpkt | |
google-apputils | https://pypi.python.org/pypi/google-apputils | |
PyParsing | http://sourceforge.net/projects/pyparsing/files/ | 2.0.3 or later 2.x version |
python-gflags | https://github.com/google/python-gflags/releases | |
pytz | https://pypi.python.org/pypi/pytz | |
PyYAML | http://pyyaml.org/wiki/PyYAML | |
pyzmq | https://pypi.python.org/pypi/pyzmq | Needs Cython to build |
requests | https://github.com/kennethreitz/requests/releases | Make sure to click on: "Show # newer tags" | 
six | https://pypi.python.org/pypi/six#downloads | |
yara-python | https://github.com/VirusTotal/yara-python | | 

Some of these Python modules can be directly installed via dnf:
```
sudo dnf install libyaml pyparsing python-dateutil python-requests python-six PyYAML pytz
```

#### construct - Troubleshooting

**Note the construct package could conflict with Fedora distribute version of construct: python-construct.**

#### DPKT - Troubleshooting

```
ImportError: cannot import name pystone
```

pystone can be found in python-test
```
sudo dnf install python-test
```

#### Building a RPM

Setup.py allows you to easily build a RPM in most cases. This paragraph contains a generic description of building a RPM so we do not have to repeat this for every dependency.

To build a RPM file from package-1.0.0.tar.gz run the following commands from the build root directory.

First extract the package:
```
tar zxvf package-1.0.0.tar.gz
```

Next change into the package source directory and have setup.py build a RPM:
```
cd package-1.0.0\
C:\Python27\python.exe setup.py bdist_rpm
```

This will create a RPM in the dist sub directory e.g.:
```
dist/package-1.0.0-1.noarch.rpm
```

Note that the actual RPM file name can vary per package.

To install the RPM from the command line:
```
sudo dnf install /package-1.0.0/dist/package-1.0.0-1.noarch.rpm
```

### dfVFS

The dfVFS build instructions can be found [here](https://github.com/log2timeline/dfvfs/wiki/Building). Note that for dfVFS to function correctly several dependencies, like pytsk, mentioned later in a section of this page, are required.

Download the latest source package from: https://github.com/log2timeline/dfvfs/releases

To build rpm files run the following command from the build root directory:
```
tar xvf dfvfs-20140219.tar.gz 
cd dfvfs-20140219/
python setup.py bdist_rpm
cd ..
```

To install the required rpm files run:
```
sudo rpm -ivh dfvfs-20140219/dist/dfvfs-20140219-1.noarch.rpm
```

### IPython

By default Fedora 20 comes with IPython 0.13.2. Plaso requires version 1.2.1 or later.

**TODO: describe**

### Hachoir

Download the latest source package from: https://bitbucket.org/haypo/hachoir/wiki/Install/source

You'll need:

* hachoir-core-1.3.3.tar.gz
* hachoir-parser-1.3.4.tar.gz
* hachoir-metadata-1.3.3.tar.gz

To build rpm files run the following command from the build root directory:
```
tar xfv hachoir-core-1.3.3.tar.gz
cd hachoir-core-1.3.3
python setup.py build bdist_rpm
cd ..
```

To install the required rpm files run:
```
sudo rpm -ivh hachoir-core-1.3.3/dist/hachoir-core-1.3.3-1.noarch.rpm
```

To build rpm files run the following command from the build root directory:
```
tar xfv hachoir-parser-1.3.4.tar.gz
cd hachoir-parser-1.3.4
python setup.py build bdist_rpm
cd ..
```

To install the required rpm files run:
```
sudo rpm -ivh hachoir-parser-1.3.4/dist/hachoir-parser-1.3.4-1.noarch.rpm
```
To build rpm files run the following command from the build root directory:
```
tar xfv hachoir-metadata-1.3.3.tar.gz
cd hachoir-metadata-1.3.3
python setup.py build bdist_rpm
cd ..
```

To install the required rpm files run:
```
sudo rpm -ivh hachoir-metadata-1.3.3/dist/hachoir-metadata-1.3.3-1.noarch.rpm
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
sudo dnf install bzip2-devel libfuse-devel openssl-devel zlib-devel
```

Since the build process for the libyal libraries is very similar, the following paragraph provides building libevt as an example. For more details see the build instructions of the individual projects e.g. https://github.com/libyal/libevt/wiki/Building.

Note that there is also a script to batch build the libyal dependencies more information here: https://github.com/log2timeline/l2tdevtools/wiki/Build-script

#### Example: libevt and Python-bindings

Download the latest source package from: https://github.com/libyal/libevt/releases

mv libevt-alpha-20130923.tar.gz libevt-20130923.tar.gz
```
rpmbuild -ta libevt-20130923.tar.gz
```

On a 64-bit version or Fedora 18 this will create the rpm files in the directory:
```
~/rpmbuild/RPMS/x86_64/
```

To install the required rpm files run:
```
sudo rpm -ivh ~/rpmbuild/RPMS/x86_64/libevt-20130923-1.x86_64.rpm ~/rpmbuild/RPMS/x86_64/libevt-python-20130923-1.x86_64.rpm
```

### Pefile

**TODO describe**

### Psutil

Download the latest source package from: https://pypi.python.org/pypi/psutil

To build rpm files run the following command from the build root directory:
```
tar xvf psutil-1.2.1.tar.gz 
cd psutil-1.2.1/
python setup.py bdist_rpm
cd ..
```

To install the required rpm files run:
```
sudo dnf install psutil-1.2.1/dist/psutil-1.2.1.x86_64.rpm
```

#### python-gflags

Download the latest source package from: https://github.com/google/python-gflags/releases

To build rpm files run the following command from the build root directory:
```
tar xvf python-gflags-python-gflags-2.0.tar.gz
cd python-gflags-python-gflags-2.0/
python setup.py bdist_rpm
cd ..
```

To install the required rpm files run:
```
sudo dnf install python-gflags-python-gflags-2.0/dist/python-gflags-2.0-1.noarch.rpm
```

### Pytsk

The build and install Pytsk see:

* https://github.com/py4n6/pytsk/wiki/Building

### Optional dependencies for output modules
#### elasticsearch-py
Download the latest source package from: https://github.com/elastic/elasticsearch-py

**TODO: describe**

#### XlsxWriter

Download the latest source package from: https://github.com/jmcnamara/XlsxWriter/releases

To build rpm files run the following command from the build root directory:
```
tar xvf XlsxWriter-RELEASE_0.7.3.tar.gz
cd XlsxWriter-RELEASE_0.7.3/
python setup.py bdist_rpm
cd ..
```

To install the required rpm files run:
```
sudo dnf install XlsxWriter-RELEASE_0.7.3.tar.gz/dist/XlsxWriter-0.7.3-1.noarch.rpm
```
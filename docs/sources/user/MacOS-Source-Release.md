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

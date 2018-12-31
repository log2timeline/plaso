# Plaso Dependencies

This page contains detailed instructions on how to build and install dependencies.

There are multiple ways to install the dependencies:

* Using [prepackaged dependencies](Dependencies.md#prepackaged-dependencies);
* [Batch build](Dependencies.md#batch-build) most of the dependencies;
* [Manual build](Dependencies.md#manual-build) of the dependencies.

## Optional dependencies

Some dependencies for plaso are optional:

* Timesketch: https://github.com/google/timesketch/blob/master/docs/Installation.md

## Prepackaged dependencies

### Fedora Core

**Note that the instructions in this page assume you are running on Fedora Core 26, 27 or 28. Installing packages from the copr on other versions and/or distributions is not recommended.**

The [GIFT copr](https://copr.fedorainfracloud.org/groups/g/gift/coprs/) contains the necessary packages for running plaso. GIFT copr provides the following tracks:

* stable; track intended for the "packaged release" of plaso and dependencies;
* dev; track intended for the "development release" of plaso;
* testing; track intended for testing newly created packages.

#### Packaged release

To add the stable track to your dnf configuration run:

```bash
sudo dnf install dnf-plugins-core
sudo dnf copr enable @gift/stable
```

To install the dependencies run:

```bash
./config/linux/gift_copr_install.sh
```

#### Development release

To add the dev track to your dnf configuration run:

```bash
sudo dnf install dnf-plugins-core
sudo dnf copr enable @gift/dev
```

To install the dependencies run:

```bash
./config/linux/gift_copr_install.sh include-development include-test
```

For troubleshooting crashes it is recommended to install the following debug symbol packages as well:

```bash
./config/linux/gift_copr_install.sh include-debug
```

### MacOS

The [l2tbinaries](https://github.com/log2timeline/l2tbinaries) contains the necessary packages for running plaso. l2tbinaries provides the following branches:

* master; branch intended for the "packaged release" of plaso and dependencies;
* dev; branch intended for the "development release" of plaso;
* testing; branch intended for testing newly created packages.

The l2tdevtools project provides [an update script](https://github.com/log2timeline/l2tdevtools/wiki/Update-script) to ease the process of keeping the dependencies up to date.

#### Packaged release

To install the release versions of the dependencies run:

```
PYTHONPATH=. python tools/update.py --preset plaso
```

#### Development release

To install the development versions of the dependencies run:

```
PYTHONPATH=. python tools/update.py --preset plaso --track dev
```

### Ubuntu

**Note that the instructions in this page assume you are running on Ubuntu 14.04 or 16.04. Installing packages from the PPA on other versions and/or distributions is not recommended.**

The [GIFT PPA](https://launchpad.net/~gift) contains the necessary packages for running plaso. GIFT PPA provides the following tracks:

* Release (stable); track intended for the "packaged release" of plaso and dependencies;
* Bleeding Edge (dev); track intended for the "development release" of plaso;
* Testing (testing); track intended for testing newly created packages.

To install plaso from the GIFT PPA you'll need to have Ubuntu universe enabled:

```
sudo add-apt-repository universe
sudo apt-get update
```

#### Packaged release

To add the stable track to your apt configuration run:

```
sudo add-apt-repository ppa:gift/stable
```

To install the dependencies run:

```
./config/linux/gift_ppa_install.sh
```

#### Development release

To add the dev track to your apt configuration run:

```
sudo add-apt-repository ppa:gift/dev
```

To install the dependencies run:

```
./config/linux/gift_ppa_install.sh include-development include-test
```

For troubleshooting crashes it is recommended to install the following debug symbol packages as well:

```
./config/linux/gift_ppa_install.sh include-debug
```

### Windows

The [l2tbinaries](https://github.com/log2timeline/l2tbinaries) contains the necessary packages for running plaso. l2tbinaries provides the following branches:

* master; branch intended for the "packaged release" of plaso and dependencies;
* dev; branch intended for the "development release" of plaso;
* testing; branch intended for testing newly created packages.

The l2tdevtools project provides [an update script](https://github.com/log2timeline/l2tdevtools/wiki/Update-script) to ease the process of keeping the dependencies up to date. To run:

The script requires [pywin32](https://github.com/mhammond/pywin32/releases) and [Python WMI](https://pypi.python.org/pypi/WMI/).

#### Packaged release

To install the release versions of the dependencies run:

```
set PYTHONPATH=.

C:\Python27\python.exe tools\update.py --preset plaso
```

#### Development release

To install the development versions of the dependencies run:

```
set PYTHONPATH=.

C:\Python27\python.exe tools\update.py --preset plaso --track=dev
```

## Batch build

**Note that the batch build script is currently still work in progress, but it will build most of the dependencies.**

Set up the [l2tdevtools build script](https://github.com/log2timeline/l2tdevtools/wiki/Build-script).

On Windows run:

```
set PYTHONPATH=.

C:\Python27\python.exe tools\build.py --preset plaso BUILD_TARGET
```

On other platforms run:

```
PYTHONPATH=. python tools/build.py --preset plaso BUILD_TARGET
```

Where `BUILD_TARGET` is the build target for your configuration. If you are unable to find the proper build target we do not recommend using this installation method.

Successfully built packages will be stored in the build directory, which is `build` by default. You can use your preferred installation method to install them.

## Manual build

* Dependencies-Fedora-Core
* Dependencies-Mac-OS-X
* Dependencies---Ubuntu
* Dependencies-Windows

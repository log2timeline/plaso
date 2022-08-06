# Plaso Development Dependencies

This page contains detailed instructions on how to install dependencies for
development.

There are multiple ways to install the dependencies:

* [Using prepackaged dependencies](Development-Dependencies.md#prepackaged-dependencies)
* [Batch build](Development-Dependencies.md#batch-build)
* [Manual build](Development-Dependencies.md#manual-build)

## Prepackaged dependencies

### Fedora

**Note that these instructions assume you are running on Fedora 36.
Installing packages from the copr on other versions and/or distributions
is not recommended.**

The [GIFT copr](https://copr.fedorainfracloud.org/groups/g/gift/coprs/) contains
the necessary packages for running Plaso. GIFT copr provides the following
tracks:

* stable; track intended for the "packaged release" of Plaso and dependencies;
* dev; track intended for development of Plaso;
* testing; track intended for testing newly created packages.

To add the dev track to your dnf configuration run:

```bash
sudo dnf install dnf-plugins-core
sudo dnf copr enable @gift/dev
```

To install the dependencies run:

```bash
./config/linux/gift_copr_install.sh include-development include-test
```

For troubleshooting crashes it is recommended to install the following debug
symbol packages as well:

```bash
./config/linux/gift_copr_install.sh include-debug
```

### MacOS

The [l2tbinaries](https://github.com/log2timeline/l2tbinaries)
repository contains the necessary packages for running Plaso. l2tbinaries
provides the following branches:

* main; branch intended for the "packaged release" of Plaso and dependencies;
* dev; branch intended for development of Plaso;
* testing; branch intended for testing newly created packages.

The l2tdevtools project provides
[an update script](https://github.com/log2timeline/l2tdevtools/wiki/Update-script)
 to ease the process of keeping the dependencies up to date.

To install the development versions of the dependencies run:

```bash
PYTHONPATH=. python tools/update.py --preset plaso --track dev
```

### Ubuntu

**Note that the instructions in this page assume you are running on Ubuntu
22.04. Installing packages from the PPA on other versions and/or distributions
is not recommended.**

The [GIFT PPA](https://launchpad.net/~gift) contains the necessary packages for
running Plaso. The GIFT PPA provides the following tracks:

* Release (stable) track intended for the "packaged release" of Plaso and
its dependencies;
* Bleeding Edge (dev) track intended for development of Plaso;
* Testing (testing) track intended for testing newly created packages.

To install Plaso from the GIFT PPA you'll need to have Ubuntu universe enabled:

```bash
sudo add-apt-repository universe
sudo apt-get update
```

To add the dev track to your apt configuration run:

```bash
sudo add-apt-repository ppa:gift/dev
```

To install the dependencies run:

```bash
./config/linux/gift_ppa_install.sh include-development include-test
```

For troubleshooting crashes it is recommended to install the following debug
symbol packages as well:

```bash
./config/linux/gift_ppa_install.sh include-debug
```

### Windows

The [l2tbinaries](https://github.com/log2timeline/l2tbinaries)
repository contains the necessary packages for running plaso. l2tbinaries
provides the following branches:

* main; branch intended for the "packaged release" of Plaso and dependencies;
* dev; branch intended for the development of Plaso;
* testing; branch intended for testing newly created packages.

The l2tdevtools project provides
[an update script](https://github.com/log2timeline/l2tdevtools/wiki/Update-script)
 to ease the process of keeping the dependencies up to date.

The script requires [pywin32](https://github.com/mhammond/pywin32/releases) and
[Python WMI](https://pypi.org/project/WMI/).

To install the development versions of the dependencies run:

```
set PYTHONPATH=.

C:\Python3\python.exe tools\update.py --preset plaso --track dev
```

## Batch build

**Note that the batch build script is currently still work in progress, but it
will build most of the dependencies.**

Set up the [l2tdevtools build script](https://github.com/log2timeline/l2tdevtools/wiki/Build-script).

On Windows run:

```
set PYTHONPATH=.

C:\Python3\python.exe tools\build.py --preset plaso BUILD_TARGET
```

On other platforms run:

```
PYTHONPATH=. python tools/build.py --preset plaso BUILD_TARGET
```

Where `BUILD_TARGET` is the build target for your configuration. If you can't
identify the proper build target we do not recommend using this installation
method.

Successfully built packages will be stored in the build directory, which is
`build` by default. You can use your preferred installation method to install them.

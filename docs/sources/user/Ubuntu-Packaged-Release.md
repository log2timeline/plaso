# Installing Plaso on Ubuntu

### Ubuntu 22.04 LTS (jammy)

**Note that other versions of Ubuntu are not supported at this time.**

Make sure the universe apt repository is enabled.

```
sudo add-apt-repository universe
```

To install Plaso from the GIFT Personal Package Archive (PPA) add the [GIFT PPA](https://launchpad.net/~gift):

```
sudo add-apt-repository ppa:gift/stable
```

Update and install Plaso:

```
sudo apt-get update
sudo apt-get install plaso-tools
```

### SANS Investigative Forensic Toolkit (SIFT) Workstation

SIFT workstation is an independent project that provides Plaso releases. We
strongly encourage to ensure you are running the latest version of Plaso when
using SIFT.

If you are using SIFT and you have a deployment problem please report that
directory to the [SIFT project](https://github.com/teamdfir/sift).

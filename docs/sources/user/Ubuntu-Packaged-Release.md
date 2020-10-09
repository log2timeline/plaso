# Installing Plaso on Ubuntu

### Ubuntu 18.04 LTS (bionic) and 20.04 LTS (focal)

**Note that other versions of Ubuntu are not supported at this time.**

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

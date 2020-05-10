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

SIFT workstation version 3 is currently using Ubuntu 16.04 and therefore currently not supported by the GIFT PPA.

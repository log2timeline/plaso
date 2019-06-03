# Installing Plaso on Ubuntu

### SANS Investigative Forensic Toolkit (SIFT) Workstation

SIFT workstation version 3 adds the [GIFT PPA](https://launchpad.net/~gift) stable track. All you need to do get the most recent stable release of Plaso is:
```bash
sudo apt-get update
sudo apt-get install plaso-tools
```

### Ubuntu 16.04 and 18.04 LTS

To install plaso from the GIFT Personal Package Archive (PPA) add the [GIFT PPA](https://launchpad.net/~gift):

```bash
sudo add-apt-repository ppa:gift/stable
```

Update and install plaso:

```bash
sudo apt-get update
sudo apt-get install plaso-tools
```

## Problems
See 
### SANS Investigative Forensic Toolkit (SIFT) Workstation

SIFT workstation version 3 adds the [GIFT PPA](https://launchpad.net/~gift) stable track. All you need to do get the most recent stable release of Plaso is:
```
sudo apt-get update
sudo apt-get install python-plaso plaso-tools
```

### Ubuntu 14.04 and 16.04 LTS

To install plaso from the GIFT Personal Package Archive (PPA) you'll need to have Ubuntu universe enabled:

```
sudo add-apt-repository universe
sudo apt-get update
```

Not necessary but we recommend that your installation is up to date:

```
sudo apt-get upgrade
```

Add the [GIFT PPA](https://launchpad.net/~gift):
```
sudo add-apt-repository ppa:gift/stable
```

Update and install plaso:
```
sudo apt-get update
sudo apt-get install python-plaso plaso-tools
```

# Developing on Fedora Core

To download the latest version of Plaso you'll need to install the git tools:
```bash
sudo dnf install git
```

Checkout the plaso source from the git repo:
```bash
git clone https://github.com/log2timeline/plaso.git
```

To be able to run the plaso [development release](Releases-and-roadmap.md) on Fedora Core or equivalent you'll have to have installed the [dependencies](Dependencies.md).

Check if you have all the dependencies installed and have the right minimum version:
```
python utils/check_dependencies.py
```

**Note that some dependencies are actively under development and can be frequently updated, therefore we recommend checking the status of the dependencies regularly.**

## Development tools
If you intend to do development on plaso you'll also need to install some development tools:

* PyLint 1.7.x
* Python Mock

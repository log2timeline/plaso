# Developing on Fedora

To download the latest version of Plaso you'll need to install the git tools:
```bash
sudo dnf install git
```

Checkout the plaso source from the git repo:
```bash
git clone https://github.com/log2timeline/plaso.git
```

## Dependencies

Install the dependencies, using either:
* A [virtualenv](Developing-Virtualenv.html#Fedora)
* The [prepackaged dependencies](Development-Dependencies.html#Fedora).

Check if you have all the dependencies installed and have the right minimum
versions:
```
python utils/check_dependencies.py
```

**Note that some dependencies are actively under development and can be
frequently updated, therefore we recommend checking the status of the
dependencies regularly.**

## Development tools
If you intend to do development on Plaso you'll also need to install some
development tools:

* PyLint 1.9.x
* Python Mock

# Developing on Ubuntu

## Git
To download the latest version of Plaso you'll need to install the git tools:
```
sudo apt-get install git
```

Checkout the Plaso source from the git repo:
```
git clone https://github.com/log2timeline/plaso.git
```

## Dependencies

Install the dependencies, using either:
* A [virtualenv](Developing-Virtualenv.html#Ubuntu)
* The [prepackaged dependencies](Development-Dependencies.html#Ubuntu).

Check if you have all the dependencies installed and have the right minimum
versions:
```
python utils/check_dependencies.py
```

**Note that some dependencies are actively under development and can be
frequently updated, therefore we recommend checking the status of the
 dependencies regularly.**

## Updating your environment.

If you are using a github fork your origin is pointing to your fork and not
the main Plaso git repository. When you run `git remote -v` you might see
something like:
```
origin	https://github.com/Onager/plaso (fetch)
origin	https://github.com/Onager/plaso (push)
```

Add a git remote called 'upstream' that you can use to sync your fork:
```
git remote add upstream https://github.com/log2timeline/plaso.git
git pull --rebase upstream main
```

We provide packaged versions of the dependencies via the [l2tbinaries project](https://github.com/log2timeline/l2tbinaries/blob/main/README.md).
However it is possible that the dependencies are not fully up to date therefore
we also provide a build script as part of [l2tdevtools project](https://github.com/log2timeline/l2tdevtools)
to do unattended bulk builds.

## Development tools
If you intend to do development on Plaso you'll also need to install some
development tools:

* PyLint
* Python Mock

### PyLint
Currently plaso development uses PyLint version 2.6.x.

### Python Mock
To install Python Mock run:
```bash
sudo apt-get install python-mock
```

# Developing on MacOS

## XCode

First install XCode

Next install XCode Command Line Tools:

```bash
xcode-select --install
```

## Git

Install the [git tools](https://git-scm.com/downloads).

Checkout the plaso source from the git repo:

```bash
git clone https://github.com/log2timeline/plaso.git
```

## Dependencies

Install the dependencies in a [virtualenv environment](../user/MacOS-Source-Release.html#install-plaso-contained-within-a-virtual-environment)

Check if you have all the dependencies installed and have the right minimum
version:

```bash
./utils/check_dependencies.py
```

**Note that some dependencies are actively under development and can be
frequently updated, therefore we recommend checking the status of the
dependencies regularly.**

## Development tools

If you intend to do development on plaso you'll also need to install some development tools:

* PyLint 1.9.x
* Python Mock

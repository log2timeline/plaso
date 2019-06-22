# Developing on MacOS

## Git
To download the latest version of Plaso you'll need to install the 
[git tools](http://git-scm.com/downloads).

Checkout the plaso source from the git repo:
```bash
git clone https://github.com/log2timeline/plaso.git
```

## Dependencies

Install the dependencies, using either:
* A [virtualenv](Developing-Virtualenv.html#MacOS)
* The [prepackaged dependencies](Development-Dependencies.html#MacOS).

Check if you have all the dependencies installed and have the right minimum
version:
```bash
./utils/check_dependencies.py
```

**Note that some dependencies are actively under development and can be 
frequently updated, therefore we recommend checking the status of the
dependencies regularly.**

If `check_dependencies.py` keeps indicating it detected an out of date version 
check if the following directory might still contain an older version:
```bash
/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/
```

Apple also ships version 2.0.1 of pyparsing under 
```/System/Library/Frameworks/Python.framework``` which is loaded first, even 
if you have a newer pyparsing installed. You can work around this by specifying 
the PYTHONPATH when you run one of the command line tools - try 
```PYTHONPATH=/Library/Python/2.7/site-packages:$PYTHONPATH ./tools/log2timeline.py --help```
if you're having problems.

## Development tools
If you intend to do development on plaso you'll also need to install some development tools:

* PyLint 1.9.x
* Python Mock

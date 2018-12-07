# Troubleshooting MacOS

## How do I remove a plaso installation

If you installed plaso via the installer script in the .dmg, the Mac OS X package manager can be used to remove a plaso installation. For more information about using the Mac OS X package manager see:

* http://superuser.com/questions/36567/how-do-i-uninstall-any-apple-pkg-package-file

## pyparsing errors

Mac OS-X bundles its own version of pyparsing that is older than the version required by Plaso. Fix this by using the special wrapper scripts (log2timeline**.sh**, et. al.), or if you don't want to do that, manipulate PYTHONPATH so that the newer version is loaded. This is detailed on the [MacOS development page](../developer/Development-release-MacOS.md).

## ImportError: cannot import name dependencies

There can be numerous reasons for imports to fail on Mac OS X here we describe some of the more common ones encountered:

* clashing versions; you have multiple clashing versions installed on your system check the Python site-packages paths such as: `/Library/Python/2.7/site-packages/`, `/usr/local/lib/python2.7/site-packages/`.
* you used `pip` without `virtualenv` and have messed up your site-packages

### You used `pip` without `virtualenv` and have messed up your site-packages

The use of `pip` without `virtualenv` on Mac OS X is **strongly** discouraged, unless you are very familiar with these tools. You might have already messed up your site-packages beyond a state of a timely repair.

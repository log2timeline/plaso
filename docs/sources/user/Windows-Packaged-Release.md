# Windows Packaged Release

To install the Windows Packaged Release plaso you need to download the latest version from https://github.com/log2timeline/plaso/releases for example:

`plaso-20190131-py2.7-amd64.zip`

The name of the ZIP file indicates:

* the architecture of the binaries in the ZIP, which are "win32" or "amd64"
* the Python version of binaries in the ZIP, which are "py2.7" or "py3.6"

Since the binaries were build using Visual Studio you will need to install the corresponding version of the Visual C++ Redistributable package.

* Python 2.7 Visual Studio 2008
* Python 3.6 Visual Studio 2017

The Visual C++ Redistributable package can be obtain from [Microsoft Download Center](https://www.microsoft.com/en-us/search/Results.aspx?q=Microsoft%20Visual%20C%2B%2B%20Redistributable%20Package&form=DLC).

Extract the ZIP file and you're ready to log2timeline.

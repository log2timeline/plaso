To install the MacOS packaged release of plaso you need to download the latest version from https://github.com/log2timeline/plaso/releases

Attached to the most recent release (as of this time version 20170930) is a DMG file.

The DMG file can be either opened by double clicking it or by using the command line.

```
hdiutil attach plaso-20170930_macosx-10.12.dmg
```

The terminal has to be used to install the tool itself.

```
cd /Volumes/plaso-20170930
sudo ./install.sh
```

Then the DMG can be unmounted either via the GUI or the command line:
```
hdiutil detach /Volumes/plaso-20170930
```

## Mac OS X 10.11 (El Capitan) and higher
Note that Mac OS X 10.11 (El Capitan) comes with pyparsing 2.0.1 and disallows removing these files by default. To be able to remove the files you'll have to disable System Integrity Protection (SIP or rootless), which is not recommended since some system scripts can depend on this version of pyparsing.

Alternatively you can override PYTHONPATH e.g.:
```
PYTHONPATH=/Library/Python/2.7/site-packages/ log2timeline.py
```

Which you can alias e.g.
```
alias log2timeline.py="PYTHONPATH=/Library/Python/2.7/site-packages/ log2timeline.py"
```

Or use the shell script helpers provided in the DMG e.g.
```
log2timeline.sh
```

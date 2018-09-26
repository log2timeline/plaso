# Troubleshooting on Windows 

## Plaso keeps telling me SQLite3 is too old

The Python installation bundles its own version of SQLite3 that is older than the version required by Plaso. Fix this by

* Removing the old version of SQLite3:
```
C:\Python27\DLL\sqlite3.dll
C:\Python27\DLL\_sqlite3.pyd
C:\Python27\Lib\sqlite3\
```
* Installing a newer version of SQLite3, if not already installed.

Also see: Dependencies-Windows.md#pysqlite

## Not a valid Win32 application

When I load one of the Python modules I get:
```
ImportError: DLL load failed: %1 is not a valid Win32 application.
```

This means your Python interpreter (on Windows) cannot load a python module since the module is not a valid Win32 DLL file. One cause of this could be mismatch between a 64-bit Python and 32-bit build module (or vice versa).

## Unable to find an entry point in DLL

When I try to import one of the Python-bindings or run the PyInstaller build I get:
```
ImportError: DLL load failed: The specified procedure could not be found. 
```

Make sure the DLL is built for the right WINAPI version, check the value of WINVER of your build.

## setup.py and build errors

### Cannot open input file 'kernel32.lib'

When I try to build one of the Python-bindings in 64-bit with Microsoft Visual Studio 2010 express I get:
```
fatal error LNK1181: cannot open input file 'kernel32.lib'
```

Make sure "Platform Toolset" is set to: "Windows7.1SDK"

### Unable to find vcvarsall.bat

When running setup.py I get:
```
error: Unable to find vcvarsall.bat
```

Make sure the environment variable VS90COMNTOOLS is set, e.g. for Visual Studio 2010:
```
set VS90COMNTOOLS=%VS100COMNTOOLS%
```

Or set it to a path:
```
set VS90COMNTOOLS="C:\Program Files (x86)\Microsoft Visual Studio 10.0\Common7\Tools\"
```

### ValueError: [u'path'] when running setup.py

When running setup.py I get:
```
ValueError: [u'path']
```

Try running the command from the "Windows SDK 7.1" or "Visual Studio" Command Prompt.

### I'm getting linker "unresolved externals" errors when running setup.py

If you're building a 64-bit version of a python binding Visual Studio 2010 express make sure to use "Windows SDK 7.1 Command Prompt".


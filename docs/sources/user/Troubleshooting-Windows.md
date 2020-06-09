# Troubleshooting on Windows

## Not a valid Win32 application

When I load one of the Python modules I get:
```
ImportError: DLL load failed: %1 is not a valid Win32 application.
```

This means your Python interpreter (on Windows) cannot load a Python module since the module is not a valid Win32 DLL file. One cause of this could be mismatch between a 64-bit Python and 32-bit build module (or vice versa).

## Unable to find an entry point in DLL

When I try to import one of the Python-bindings I get:
```
ImportError: DLL load failed: The specified procedure could not be found.
```

Make sure the DLL is built for the right WINAPI version, check the value of WINVER of your build.

## setup.py and build errors

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

If you're building a 64-bit version of a Python binding Visual Studio 2010 express make sure to use "Windows SDK 7.1 Command Prompt".


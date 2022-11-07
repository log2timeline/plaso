# Troubleshooting

This page contains instructions that can be used to assist you in debugging
potential issues with Plaso and its dependencies.

## Quick list

1. Check the [commit history](https://github.com/log2timeline/plaso/commits/main) and [issue tracker](https://github.com/log2timeline/plaso/issues?q=is%3Aissue) if the bug has already been fixed;
2. If you are running the development release make sure Plaso and dependencies are up to date, see: [Developers Guide](developer/Developers-Guide.md)
3. If you are experiencing an issue that cannot directly be attributed to some broken code e.g. the test are getting killed, check your system logs it might be a problem with resources available to Plaso;
4. Try to isolate the error, see below.

If everything fails create a new issue on the [issue tracker](https://github.com/log2timeline/plaso/issues).
Please provide as much detailed information as possible, keep in mind that:

* we cannot fix errors based on vague descriptions;
* we cannot look into your thoughts or on your systems;
* we cannot easily isolate errors if you keep changing your test environment.

Hence please provide us with the following details:

* What steps will reproduce the problem?
  * What output did you expect?
  * What do you see instead?
* The output of `log2timeline.py --troubles`, which provide:
  * The Python version including operating system and architecture
  * The path to plaso/log2timeline
  * The version of plaso/log2timeline
  * Information about dependencies
* Are you processing a storage media image, if so which format, a directory or on an individual file?
* Were you able to isolate the error to a specific file? Is it possible to share the file with the developer?
* Any additional information that could be of use e.g. build logs, error logs, debug logs, etc.

**Note that the github issue tracker uses [markdown](https://docs.github.com/en/github/writing-on-github/getting-started-with-writing-and-formatting-on-github)
and thus please escape blocks of error output accordingly.**

Also see the sections below on how to troubleshoot issues of a specific nature.

### Performance related issues

* On what type of media is your source data stored? What type of media are you writing to?
  * A local disk, a removable disk or network storage?
  * Both removable media and network storage can add additional latency to reads and writes making overall processing slow. It is recommended to at least write to local low-latency media.
* Are you seeing workers being killed?
  * Respawning of workers creates more overhead and slower processing times.
  * Workers being killed typically indicates one of the parser misbehaving. If the worker is consuming a high amount of memory, also see section "High memory usage" below.
* Are you running Plaso in a VM or Docker container?

## Isolating errors

The most important part of troubleshooting is isolating the error.

Can you run the tests successfully?

```bash
$ python run_tests.py
...
----------------------------------------------------------------------
Ran 585 tests in 66.530s

OK
```

If an error occurs when processing a storage media image try to run with the
storage image media file and/or the file system directly mounted. Mounting the
storage image media file will bypass libraries (modules) supporting the storage
image media format. Running [source_analyzer.py](https://github.com/open-source-dfir/dfvfs-snippets/blob/main/scripts/source_analyzer.py)
can help pinpointing the issue, e.g.

```bash
PYTHONPATH=. python scripts/source_analyzer.py --no-auto-recurse
```

Try:

* logging to a log file `log2timeline.py --log-file=log2timeline.log ...`;
* running in debug mode `log2timeline.py --debug ...`;
* running in single process mode this will bypass any issues with multi processing `log2timeline.py --single-process ...`;
* mounting the file system as well to bypass libraries (modules) supporting the file system, e.g. the SleuthKit and pytsk;
* running in single process and debug mode, see section below.

## Producing debug logs

To produce debugging logs, run log2timeline like so: `log2timeline.py
--log-file=log2timeline_problem.log.gz --debug`. This will create multiple,
gzip-compressed log files. There will be one called log2timeline_problem.log.gz
containing logs from the main log2timeline process, and one log file for each
worker process.

Note that the .gz file suffix is important, as it triggers Plaso to compress
the log output. In an uncompressed form, the logs are very large. The
compressed logs can be reviewed with unzip tools like `zless` and `zgrep`.

## Import errors

It sometimes happen that the tests fail with an import error e.g.

```bash
ImportError: Failed to import test module:
plaso.parsers.winreg_plugins.shutdown_test
Traceback (most recent call last):
  File "/usr/lib64/python3.7/unittest/loader.py", line 254, in _find_tests
    module = self._get_module_from_name(name)
  File "/usr/lib64/python3.7/unittest/loader.py", line 232, in
_get_module_from_name
    __import__(name)
  File "./plaso/parsers/__init__.py", line 4, in <module>
    from plaso.parsers import asl
ImportError: cannot import name asl
```

This does not necessarily mean that the code cannot find the asl module. The
import error can mask an underlying issue. Try running the following commands
in a Python shell:

```bash
$ python
import sys
sys.path.insert(0, u'.')
import plaso
```

It also sometimes means that you have multiple versions of Plaso installed on
your system and Python tries to import for the wrong one.

## Crashes, hangs and tracebacks

In the context of Plaso crashes and tracebacks have different meanings:

* crash; an error that causes an abrupt termination of the program you were running e.g. a segfault (SIGSEGV)
* traceback; the back trace of an error that was caught by an exception handler that can cause a termination of the program you were running

### A worker segfault-ing

Since Plaso relies on several compiled dependencies it is possible that a
worker segfault (SIGSEGV).

As part of the 1.3 pre-release bug hunting a SIGSEGV signal handler was added
however this process turned out, as expected, unreliable. However it added an
interesting side effect that is very useful for debugging. If the SIGSEGV
signal handler is enable the worker process typically remains in the "running"
state but stops producing event object. What happens under the hood is that the
SIGSEGV signal is caught but the worker is unable to cleanly terminate. Because
of this "frozen" state of the worker it is very easy to attach a debugger e.g.
`gdb python -p PID`.

A `kill -11 PID` however seems to be cleanly handled by the SIGSEGV signal
handler and puts the worker into "error" status.

### A worker gives a killed status

This typically indicates that the worker was killed (SIGKILL) likely by an
external process e.g the Out Of Memory (OOM) killer.

Your system logs might indicate why the worker was killed.

### Which processes are running

The following command help you determine which Plaso processes are running on
your system:

Linux:

```bash
top -p `ps -ef | grep log2timeline.py | grep python | awk '{ print $2 }' | tr '\n' ',' | sed 's/,$//'`
```

MacOS:

```bash
ps aux | grep log2timeline.py | grep python | awk '{print $2}' | tr '\n' ',' | sed 's/,$//'
```

### Analyzing crashes with single process and debug mode

In single process and debug mode `log2timeline.py --debug --single-process ...`
log2timeline will run a Python debug shell (pdb) when an uncaught Python
exception is raised.

Use:

* `w` to print the frames.
* `u` to go up one frame or `d` to go down one frame.
* `l` to print source code of the current frame.

Note that typically the top-level (oldest) frame will contain the exception:

```python
p exception
```

Note that inside pdb you can run any Python commands including loading new
libraries e.g. for troubleshooting. You can prepend commands with an
exclamation mark (!) to indicate that you want to run a Python command as an
opposed to a debug shell one.

To print the attributes of the current object you are looking for.

```python
!self.__dict__
```

To print the current argument stack to see what arguments are available to you.

```python
args
```

### Analyzing crashes with gdb

Once you have isolated the file that causes the crash and you cannot share the
file you can generate a back trace that can help us fix the error.

First make sure you have the debug symbols installed.

Then run Plaso as a single process with gdb:

```bash
gdb --ex r --args log2timeline.py --single-process -d docs/sources/Troubleshooting.md --storage-file timeline.plaso file_that_crashes_the_tool
```

To generate a back trace:

```bash
bt
```

Note that often the first 10 lines of the back trace are sufficient information.

An alternative approach is to attach a debugger to it once the program is
running:

```bash
gdb python -p PID
```

Where PID is the process identifier of the program. Once the debugger is
attached continue running:

```
c
```

Wait until the crash occurs and generate a back trace.

Also see: [DebuggingWithGdb](https://wiki.python.org/moin/DebuggingWithGdb),
[gdb Support](https://devguide.python.org/advanced-tools/gdb/).

## High memory usage

Plaso consists of various components. It can happen that one of these
components uses a lot of memory or even leaks memory. In these cases it is
important to isolate the error, see before, to track down what the possible
culprit is. Also see: [Profiling memory usage](developer/Profiling.md#profiling-memory-usage)

Plaso limits the memory usage on a per process basis and has multiple options
to control enforced memory limits such as `--process_memory_limit`. Use these
with caution. If a process exceeds the memory limit, typically, a MemoryError
exception is thrown.

Note that Guppy support has been removed but the linked article might be
instructional for [troubleshooting Plaso memory issues](http://blog.kiddaland.net/2014/11/troubleshooting-plaso-issues-memory.html).

## MacOS specific issues

### PyParsing errors

MacOS bundles its own version of PyParsing that is older than the version
required by Plaso. Fix this by using the special wrapper scripts
(log2timeline**.sh**, et. al.), or if you don't want to do that, manipulate
PYTHONPATH so that the newer version is loaded. This is detailed on the
[MacOS development page](developer/Developing-MacOS.md).

### ImportError: cannot import name dependencies

There can be numerous reasons for imports to fail on MacOS here we describe
some of the more common ones encountered:

* clashing versions; you have multiple clashing versions installed on your system check the Python site-packages paths such as: `/Library/Python/2.7/site-packages/`, `/usr/local/lib/python2.7/site-packages/`.
* you used `pip` without `virtualenv` and have messed up your site-packages

### You used `pip` without `virtualenv` and have messed up your site-packages

The use of `pip` without `virtualenv` on MacOS is **strongly** discouraged,
unless you are very familiar with these tools. You might have already messed up
your site-packages beyond a state of a timely repair.

## Ubuntu Linux specific issues

### Origin of an installed package

To determine the origin of an installed package

```bash
apt-cache showpkg <package name>
```

## Windows specific issues

### Not a valid Win32 application

When I load one of the Python modules I get:

```
ImportError: DLL load failed: %1 is not a valid Win32 application.
```

This means your Python interpreter (on Windows) cannot load a Python module
since the module is not a valid Win32 DLL file. One cause of this could be
mismatch between a 64-bit Python and 32-bit build module (or vice versa).

### Unable to find an entry point in DLL

When I try to import one of the Python-bindings I get:

```
ImportError: DLL load failed: The specified procedure could not be found.
```

Make sure the DLL is built for the right WINAPI version, check the value of
WINVER of your build.

### setup.py and build errors

#### Unable to find vcvarsall.bat

When running setup.py I get:

```
error: Unable to find vcvarsall.bat
```

Make sure the environment variable VS90COMNTOOLS is set, e.g. for Visual Studio
2010:

```
set VS90COMNTOOLS=%VS100COMNTOOLS%
```

Or set it to a path:

```
set VS90COMNTOOLS="C:\Program Files (x86)\Microsoft Visual Studio 10.0\Common7\Tools\"
```

#### ValueError: [u'path'] when running setup.py

When running setup.py I get:

```
ValueError: [u'path']
```

Try running the command from the "Windows SDK 7.1" or "Visual Studio" Command
Prompt.

#### I'm getting linker "unresolved externals" errors when running setup.py

If you're building a 64-bit version of a Python binding Visual Studio 2010
express make sure to use "Windows SDK 7.1 Command Prompt".

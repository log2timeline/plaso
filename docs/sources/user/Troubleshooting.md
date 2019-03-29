# Troubleshooting

This page contains instructions that can be used to assist you in debugging potential issues with the plaso and its dependencies.

## Quick list

1. Check the [commit history](https://github.com/log2timeline/plaso/commits/master) and [issue tracker](https://github.com/log2timeline/plaso/issues?q=is%3Aissue) if the bug has already been fixed;
2. If you are running the development release make sure plaso and dependencies are up to date, see: [Developers Guide](/developer/Developers-Guide.md)
3. If you are experiencing an issue that cannot directly be attributed to some broken code e.g. the test are getting killed, check your system logs it might be a problem with resources available to plaso;
4. Try to isolate the error, see below.

If everything fails create a new issue on the [issue tracker](https://github.com/log2timeline/plaso/issues). Please provide as much detailed information as possible, keep in mind that:

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

**Note that the github issue tracker uses [markdown](https://help.github.com/articles/markdown-basics/) and thus please escape blocks of error output accordingly.**

Also see the sections below on how to troubleshoot issues of a specific nature.

## Isolating errors

The most important part of troubleshooting is isolating the error.

Can you run the tests successfully?
```
$ python run_tests.py
...
----------------------------------------------------------------------
Ran 585 tests in 66.530s

OK
```

If an error occurs when processing a storage media image try to run with the storage image media file and/or the file system directly mounted. Mounting the storage image media file will bypass libraries (modules) supporting the storage image media format. Running [source_analyzer.py](https://github.com/log2timeline/dfvfs/blob/master/examples/source_analyzer.py) can help pinpointing the issue, e.g.

```
PYTHONPATH=. python examples/source_analyzer.py --no-auto-recurse
```

Try:

* logging to a log file `log2timeline.py --log-file=log2timeline.log ...`;
* running in debug mode `log2timeline.py --debug ...`;
* running in single process mode this will bypass any issues with multi processing `log2timeline.py --single-process ...`;
* mounting the file system as well to bypass libraries (modules) supporting the file system, e.g. the SleuthKit and pytsk;
* running in single process and debug mode, see section below.

## Producing debug logs

To produce debugging logs, run log2timeline like so: `log2timeline.py --log-file=log2timeline_problem.log.gz --debug`. This will create multiple, gzip-compressed log files. There will be one called log2timeline_problem.log.gz containing logs from the main log2timeline process, and one log file for each worker process.

Note that the .gz file suffix is important, as it triggers Plaso to compress the log output. In an uncompressed form, the logs are very large. The compressed logs can be reviewed with unzip tools like `zless` and `zgrep`.

## Import errors

It sometimes happen that the tests fail with an import error e.g.
```
ImportError: Failed to import test module:
plaso.parsers.winreg_plugins.shutdown_test
Traceback (most recent call last):
  File "/usr/lib64/python2.7/unittest/loader.py", line 254, in _find_tests
    module = self._get_module_from_name(name)
  File "/usr/lib64/python2.7/unittest/loader.py", line 232, in
_get_module_from_name
    __import__(name)
  File "./plaso/parsers/__init__.py", line 4, in <module>
    from plaso.parsers import asl
ImportError: cannot import name asl
```

This does not necessarily mean that the code cannot find the asl module. The import error can mask an underlying issue. Try running the following commands in a Python shell:
```
$ python
import sys
sys.path.insert(0, u'.')
import plaso
```

It also sometimes means that you have multiple versions of plaso installed on your system and Python tries to import for the wrong one.

## Crashes, hangs and tracebacks

In the context of plaso crashes and tracebacks have different meanings:

* crash; an error that causes an abrupt termination of the program you were running e.g. a segfault (SIGSEGV)
* traceback; the back trace of an error that was caught by an exception handler that can cause a termination of the program you were running

### A worker segfault-ing

Since plaso relies on several compiled dependencies it is possible that a worker segfault (SIGSEGV).

As part of the 1.3 pre-release bug hunting a SIGSEGV signal handler was added however this process turned out, as expected, unreliable. However it added an interesting side effect that is very useful for debugging. If the SIGSEGV signal handler is enable the worker process typically remains in the "running" state but stops producing event object. What happens under the hood is that the SIGSEGV signal is caught but the worker is unable to cleanly terminate. Because of this "frozen" state of the worker it is very easy to attach a debugger e.g. `gdb python -p PID`.

A `kill -11 PID` however seems to be cleanly handled by the SIGSEGV signal handler and puts the worker into "error" status.

### A worker gives a killed status

This typically indicates that the worker was killed (SIGKILL) likely by an external process e.g the Out Of Memory (OOM) killer.

Your system logs might indicate why the worker was killed.

### Which processes are running

The following command help you determine which plaso processes are running on your system:

Linux:
```
top -p `ps -ef | grep log2timeline.py | grep python | awk '{ print $2 }' | tr '\n' ',' | sed 's/,$//'`
```

Mac OS X:
```
ps aux | grep log2timeline.py | grep python | awk '{print $2}' | tr '\n' ',' | sed 's/,$//'
```

### Analyzing crashes with single process and debug mode

In single process and debug mode `log2timeline.py --debug --single-process ...` log2timeline will run a Python debug shell (pdb) when an uncaught Python exception is raised.

Use `u` to go up one level and `d` to go down one level .

Print the attributes of the current object you are looking for.
```
!self.__dict__
```

Print the current argument stack to see what arguments are available to you.
```
args
```

Note that inside pdb you can run any Python commands including loading new libraries e.g. for troubleshooting. You can prepend commands with an exclamation mark (!) to indicate that you want to run a Python command as an opposed to a debug shell one.

### Analyzing crashes with gdb

Once you have isolated the file that causes the crash and you cannot share the file you can generate a back trace that can help us fix the error.

First make sure you have the debug symbols installed.

Then run the plaso as a single process with gdb:
```
gdb --ex r --args log2timeline.py --single-process -d /tmp/test.dump /tmp/file_that_crashes_the_tool
```

To generate a back trace:
```
bt
```

Note that often the first 10 lines of the back trace are sufficient information.

An alternative approach is to attach a debugger to it once the program is running:
```
gdb python -p PID
```

Where PID is the process identifier of the program. Once the debugger is attached continue running:
```
c
```

Wait until the crash occurs and generate a back trace.

Also see: [DebuggingWithGdb](https://wiki.python.org/moin/DebuggingWithGdb), [gdb Support](https://docs.python.org/devguide/gdb.html)

## High memory usage

Plaso consists of various components. It can happen that one of these components uses a lot of memory or even leaks memory. In these cases it is important to isolate the error, see before, to track down what the possible culprit is. Also see: [Profiling memory usage](../developer/Profiling.md#profiling-memory-usage)

## Also see

* [Troubleshooting Mac OS X specific issues](Troubleshooting-MacOS.md)
* [Troubleshooting Ubuntu specific issues](Troubleshooting-Ubuntu.md)
* [Troubleshooting Windows specific issues](Troubleshooting-Windows.md)
* [Troubleshooting Plaso Issues - Memory Edition](http://blog.kiddaland.net/2014/11/troubleshooting-plaso-issues-memory.html)

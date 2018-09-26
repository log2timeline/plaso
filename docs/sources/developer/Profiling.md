Plaso supports various profiling options for troubleshooting and performance tuning.

## Profiling CPU usage

### Profiling parsers

To profile the CPU usage of the parsers run log2timeline.py with the following options:
```
log2timeline.py --profilers=parsers --profiling-directory=profile plaso.db image.raw
```

### Profiling serialization

To profile the CPU usage of the serialization run log2timeline.py with the following options:
```
log2timeline.py --profilers=serializers --profiling-directory=profile plaso.db image.raw
```

## Profiling storage

The storage profiler tracks:

* the amount of data of serialized attribute containers read and / or written

To profile the storage run log2timeline.py with the following options:
```
log2timeline.py --profilers=storage --profiling-directory=profile plaso.db image.raw
```

## Profiling task queue

The task queue profiler tracks:

* number of tasks queued for processing or to be merged
* number of tasks processing
* number of tasks pending to be merged
* number of tasks abandoned
* total number of tasks, included completed tasks

To profile the task queue statue run log2timeline.py with the following options:
```
log2timeline.py --profilers=task_queue --profiling-directory=profile plaso.db image.raw
```

## Profiling memory usage

The memory usage of the worker processes used by log2timeline.py can be profiled with the memory profiler and/or guppy.

### Profiling Python memory usage with the memory profiler

To profile the amount of data read and/or written of the storage run log2timeline.py with the following options:
```
log2timeline.py --profilers=memory --profiling-directory=profile plaso.db image.raw
```

### Profiling Python memory usage with guppy

To profile Python memory usage with guppy you'll need to install [guppy](https://pypi.python.org/pypi/guppy), version 0.1.10 or later is recommended. If plaso detects that guppy is available it will enable the `guppy` profiling option.

Run log2timeline.py with the following options:
```
log2timeline.py --profilers=guppy --profiling_directory=profile --profiling-sample-rate=5000 plaso.dump image.raw
```

This will create a #.hpy file per worker, where # is the number of the worker.

## Graphing profiles

Requires matplotlib and numpy

### Graphing memory usage over time

`./utils/plot-memory-usage.py profile`

### Graphing task queue over time

`./utils/plot-task-queue.py profile`

### Guppy

Guppy has a built-in profile browser to view the .hpy files e.g.
```
from guppy import hpy
heapy = hpy()
heapy.pb('0.hpy')
```

### Also see

* [Troubleshooting Plaso Issues - Memory Edition](http://blog.kiddaland.net/2014/11/troubleshooting-plaso-issues-memory.html)
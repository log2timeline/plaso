Plaso supports various profiling options for troubleshooting and performance
tuning.

## Profiling CPU usage

The CPU usage of various parts of Plaso its procseeing can be profiled with the
CPU ussage profiler.

To profile the CPU usage run log2timeline.py with the following options:

```bash
log2timeline.py --profilers=${PROFILERS} --profiling-directory=profile --storage-file timeline.plaso image.raw
```

Where ${PROFILERS} is comma separated list of one or more of the following
CPU usage profilers:

Name | Description
--- | --- 
analyzers | Profile CPU time of analyzers, like hashing
parsers | Profile CPU time per parser
processing | Profile CPU time of processing phases
serializers | Profile CPU time of serialization

## Profiling memory usage

The memory usage of the main (foreman) and worker processes can be profiled with
the memory profiler.

To profile the memory usage run log2timeline.py with the following options:

```bash
log2timeline.py --profilers=memory --profiling-directory=profile --storage-file timeline.plaso image.raw
```

## Profiling storage

The amount of data read and / or written by the storage con be profiled with
the storage profiler.

To profile the storage run log2timeline.py with the following options:

```bash
log2timeline.py --profilers=storage --profiling-directory=profile --storage-file timeline.plaso image.raw
```

## Profiling the task queue

The task queue profiler tracks:

* number of tasks queued for processing or to be merged
* number of tasks processing
* number of tasks pending to be merged
* number of tasks abandoned
* total number of tasks, included completed tasks

To profile the task queue statue run log2timeline.py with the following options:

```bash
log2timeline.py --profilers=task_queue --profiling-directory=profile --storage-file timeline.plaso image.raw
```

## Graphing profiles

To graph profiling data you will need to have the matplotlib and numpy Python
modules installed.

### Graphing CPU usage over time

`./utils/plot-cpu-usage.py profile`

### Graphing memory usage over time

`./utils/plot-memory-usage.py profile`

### Graphing task queue over time

`./utils/plot-task-queue.py profile`

### Also see

* [Troubleshooting Plaso Issues - Memory Edition](http://blog.kiddaland.net/2014/11/troubleshooting-plaso-issues-memory.html)

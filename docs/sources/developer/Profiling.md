Plaso supports various profiling options for troubleshooting and performance
tuning.

To list the available profilers run:

```bash
log2timeline.py --profilers list
```

The profilers write their sample files to the directory specified by
`--profiling-directory`, by default the current working directory.

## Profiling CPU usage

The CPU usage of various parts of Plaso its processing can be profiled with the
CPU usage profiler.

To profile the CPU usage run log2timeline.py with the following options:

```bash
log2timeline.py --profilers=${PROFILERS} --profiling-directory=profile --storage-file timeline.plaso image.raw
```

Where ${PROFILERS} is comma separated list of one or more of the following
CPU usage profilers:

Name | Description
--- | ---
analyzers | Profile CPU time of analyzers, like hashing
format_checks | Profile CPU time per format check
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

The amount of data read and / or written by the storage can be profiled with
the storage profiler.

To profile the storage run log2timeline.py with the following options:

```bash
log2timeline.py --profilers=storage --profiling-directory=profile --storage-file timeline.plaso image.raw
```

## Profiling the task queue

The task queue profiler is only supported in multi-processing mode and tracks:

* number of tasks queued for processing or to be merged
* number of tasks processing
* number of tasks pending to be merged
* number of tasks abandoned
* total number of tasks, included completed tasks

To profile the task queue status run log2timeline.py with the following options:

```bash
log2timeline.py --profilers=task_queue --profiling-directory=profile --storage-file timeline.plaso image.raw
```

## Profiling tasks

The tasks profiler is only supported in multi-processing mode and tracks the
status of individual tasks, such as when a task was created, processed and
merged.

To profile the tasks run log2timeline.py with the following options:

```bash
log2timeline.py --profilers=tasks --profiling-directory=profile --storage-file timeline.plaso image.raw
```

## Graphing profiles

To graph profiling data you will need to have the matplotlib and numpy Python
modules installed.

The plot scripts read the profiling sample files from the profiling directory,
for example `profile`. By default they show the graph interactively, use
`--output` to write the graph to a file instead, for example
`--output cpu_usage.png`.

### Graphing CPU usage over time

```bash
./utils/plot_cpu_usage.py --profiler processing profile
```

Where `--profiler` is one of: analyzers, parsers or processing. The default is
processing.

### Graphing memory usage over time

```bash
./utils/plot_memory_usage.py profile
```

### Graphing storage over time

```bash
./utils/plot_storage.py profile
```

### Graphing task queue over time

```bash
./utils/plot_task_queue.py profile
```

### Graphing tasks over time

```bash
./utils/plot_tasks.py profile
```

### Also see

* [Troubleshooting Plaso Issues - Memory Edition](http://blog.kiddaland.net/2014/11/troubleshooting-plaso-issues-memory.html)

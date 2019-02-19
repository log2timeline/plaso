# Tagging Analysis Plugin

Notes on how to use the tagging analysis plugin.

## Creating the tagging file

A tagging-file.txt is an UTF-8 encoded text file that contains tagging definitions.

A tagging definition consists of:
```
TAG LABEL
  EVENT TAGGING EXPRESSION
```

For example:
```
task_schedule
  data_type is 'windows:evt:record' and source_name is 'Security' and event_identifier is 602
  data_type is 'windows:evtx:record' and source_name is 'Microsoft-Windows-Security-Auditing' and event_identifier is 4698
```

## Running plaso

First run log2timeline to extract events:
```
log2timeline.py timeline.plaso image.raw
```

Next run psort to tag events:
```
psort.py --analysis tagging --tagging-file tagging-file.txt timeline.plaso
```

## Also see

* [Event filters](Event-Filters.md)

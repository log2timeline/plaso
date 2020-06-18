# Tagging Analysis Plugin

Notes on how to use the tagging analysis plugin.

## Creating a tagging file

A tagging file is an UTF-8 encoded text file that contains tagging rules.

A tagging rule consists of:

```
# Short description
LABEL
  EVENT FILTER EXPRESSION
```

For example:

```
task_schedule
  data_type is 'windows:evt:record' and source_name is 'Security' and event_identifier is 602
  data_type is 'windows:evtx:record' and source_name is 'Microsoft-Windows-Security-Auditing' and event_identifier is 4698
```

## Running Plaso

First run log2timeline to extract events:

```
log2timeline.py timeline.plaso image.raw
```

Next run psort to tag events:

```
psort.py --analysis tagging --tagging-file tagging-file.txt timeline.plaso
```

## Also see

* [Event filters](Event-filters.md)
* [Tagging rules](Tagging-Rules.md)

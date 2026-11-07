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

## Running the analysis plugin

First run log2timeline to extract events:

```bash
log2timeline.py --storage-file timeline.plaso image.raw
```

Next run psort to tag events:

```bash
psort.py --analysis tagging --tagging-file tagging-file.txt -o null timeline.plaso
```

This will tag events based on the tagging rules.

Plaso provides the following tagging files, which are described in
[Tagging rules](Tagging-Rules.md):

* tag_linux.txt
* tag_macos.txt
* tag_windows.txt

If the tagging file does not exist at the given path, psort looks for it in
the data location, which is detected automatically or can be set with
`--data`. So a bundled tagging file
can be specified by its name, for example:

```bash
psort.py --analysis tagging --tagging-file tag_windows.txt -o null timeline.plaso
```

The last step would be to export a timeline with the tags:

```bash
psort.py -o dynamic --fields datetime,timestamp_desc,source,source_long,message,parser,tag -w timeline.csv timeline.plaso
```

## Also see

* [Event filters](Event-filters.md)
* [Tagging rules](Tagging-Rules.md)

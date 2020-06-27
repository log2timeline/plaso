# Output and formatting

The plaso tools `psort.py` and `psteal.py` can output events in multiple
formats using several output modules.

## Output modules

Plaso supports several output formats:

Name | Description
--- | ---
dynamic | Output events to a delimiter (comma by default) separated value output format, that supports a dynamic selection of fields.
elastic | Output events to an ElasticSearch database. Requires elasticsearch-py.
json | Output events to JSON format.
json_line | Output events to JSON line format.
l2tcsv | Output events to log2timeline.pl legacy CSV format, with 17 fixed fields. Also see: [l2tcsv output format](Output-format-l2tcsv.md)
l2ttln | Output events to log2timeline.pl extended TLN format, with 7 fixed field. | delimited output. Also see: [TLN](https://forensicswiki.xyz/wiki/index.php?title=TLN).
null | Do not output events.
rawpy | Output events in "raw" (or native) Python format.
timesketch | Output events to a Timesketch ElasticSearch database. Requires elasticsearch-py.
tln | Output events to TLN format, with 5 fixed fields. Also see: [TLN](https://forensicswiki.xyz/wiki/index.php?title=TLN).

## Message formatting

In log2timeline.pl the l2tcsv format introduced the `desc` and `short` fields
that provide a description of the field, the interpreted results or the content
of the corresponding log line.

In Plaso the dynamic format extended the idea of the `desc` field, to provide
a formatted `message` field. That allow to provide more extensive formatting
such as [supporting Windows Event Log message strings](http://blog.kiddaland.net/2015/04/windows-event-log-message-strings.html).

### Formatter configuration file format

As of version 20200227 Plaso supports formatter configuration files.

**Note that the format of these configuration files is subject to change.**

An event formatter is defined as a set of attributes:

* "data_type"; required event data type;
* "message"; required formatter message string, for a basic type, or list of messages string pieces, for a conditional type.
* "separator"; optional conditional message string piece separator;
* "short_message"; required formatter short message string, for a basic type, or list of short messages string pieces, for a conditional type.
* "short_source"; required formatter short source identifier that corresponds with the l2tcsv and tln source field.
* "source"; required formatter source identifier that corresponds with the l2tcsv sourcetype field.
* "type"; required event formatter type either "basic" or "conditional".

For example:

```
---
type: 'basic'
data_type: 'bash:history:command'
message: 'Command executed: {command}'
short_message: '{command}'
short_source: 'LOG'
source: 'Bash History'
---
type: 'conditional'
data_type: 'syslog:cron:task_run'
message:
- 'Cron ran: {command}'
- 'for user: {username}'
- 'pid: {pid}'
separator: ', '
short_message:
- '{body}'
short_source: 'LOG'
source: 'Cron log'
```

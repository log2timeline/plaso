# Output and formatting

The plaso tools `psort.py` and `psteal.py` can output events in multiple
formats using several output modules.

## Output modules

Plaso supports several output formats:

Name | Description
--- | ---
dynamic | Output events to a delimiter (comma by default) separated value output format, that supports a dynamic selection of fields.
json | Output events to JSON format.
json_line | Output events to JSON line format.
kml | Output events with geography data into a KML format.
l2tcsv | Output events to log2timeline.pl legacy CSV format, with 17 fixed fields. Also see: [l2tcsv output format](Output-format-l2tcsv.html)
l2ttln | Output events to log2timeline.pl extended TLN format, with 7 fixed field. | delimited output. Also see: [TLN](https://forensics.wiki/tln).
null | Do not output events.
rawpy | Output events in "raw" (or native) Python format.
opensearch | Saves the events into an OpenSearch database. Requires opensearchpy.
opensearch_ts | Saves the events into an OpenSearch database for use with Timesketch. Requires opensearchpy
tln | Output events to TLN format, with 5 fixed fields. Also see: [TLN](https://forensics.wiki/tln).
xlsx | Output events to an Excel Spreadsheet (XLSX).

### Dynamic output module fields

The dynamic output module defines the following command line options to specify
which fields should be represented in the output, namely `--fields` and
`--additional_fields`. The name of the fields typically map 1-to-1 to the names
of attributes of the event data. However there are "special" fields that are
composed at runtime.

Name | Description
--- | ---
date | The date of the event formatted as "YYYY-MM-DD" or "0000-00-00" on error
datetime | The date and time of the event in ISO 8601 format in microseconds or "0000-00-00T00:00:00.000000+00:00" on error
description | The event message string as defined by the message formatter
description_short | The short event message string as defined by the message formatter
display_name | Human readable representation of the path specification
filename | The "filename" attribute if present in the event data, otherwise derived from the path specification
host | The hostname derived by pre-processing
hostname | The hostname derived by pre-processing
inode | The "inode" attribute if present in the event data, otherwise derived from the file system identifier (such as inode, MFT entry) in the path specification
macb | MACB (Modification, Access, Change, Birth) group representation
message | The event message string as defined by the message formatter
message_short | The short event message string as defined by the message formatter
source | The short event source as defined by the message formatter
sourcetype | The event source as defined by the message formatter
source_long | The event source as defined by the message formatter
tag | The labels defined by event tags
time | The time of the event in seconds formatted as "HH:MM:SS" or "--:--:--" on error
timestamp_desc | Indication of what the event time represents such as Creation Time or Program Execution Duration
timezone | Time zone indicator
type | Indication of what the event time represents such as Creation Time or Program Execution Duration
user | The username derived by pre-processing
username | The username derived by pre-processing
zone | Time zone indicator

Note that the `--dynamic-time` output option will change the format of the
datetime output field to use value appropriate granularity, for example seconds
for a HFS+ timestamp will be "YYYY-MM-DDTHH:MM:SS" but for an NTFS filetime it
will be "YYYY-MM-DDTHH:MM:SS.#######", or a semantic time, for example
"Not set", or "Error" on error. Older Plaso storage files do not necessarily
support the dynamic time option.

Output fields that are not part of the event data but of the data stream the
event data originates from.

Name | Description
--- | ---
file_entropy | Byte entropy of the data stream content. This is a value ranging from 0.0 to 8.0, where 8.0 indicates the distribution of byte values is highly random.
md5_hash | MD5 hash of the data stream content.
sha1_hash | SHA-1 hash of the data stream content.
sha256_hash | SHA-256 hash of the data stream content.
yara_match | Names of the Yara rules that matched the data stream content.

## Output field formatting

### Source fields

As of Plaso 20200916 the value of the long and short source fields are defined
in `data/sources.config`. This file contains 3 tab separated values:

* data_type; event data type.
* short_source; short source identifier that corresponds with the l2tcsv and tln source field.
* source; source identifier that corresponds with the l2tcsv sourcetype field.

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

* "data_type"; required event data type.
* "boolean_helpers"; optional boolean helpers.
* "custom_helpers"; optional custom helpers.
* "enumeration_helpers"; optional enumeration helpers.
* "message"; required formatter message string, for a basic type, or list of messages string pieces, for a conditional type.
* "separator"; optional conditional message string piece separator, the default is a single space.
* "short_message"; required formatter short message string, for a basic type, or list of short messages string pieces, for a conditional type.
* "type"; required event formatter type either "basic" or "conditional".

For example:

```
---
type: 'basic'
data_type: 'bash:history:command'
message: 'Command executed: {command}'
short_message: '{command}'
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
```

#### Boolean helpers

Boolean helpers can be defined to map a boolean value of an event attribute to
a more descriptive value, for example mapping True to Shared in the example
below.

```
type: 'conditional'
data_type: 'gdrive:snapshot:cloud_entry'
boolean_helpers:
- input_attribute: 'shared'
  output_attribute: 'shared'
  value_if_false: 'Private'
  value_if_true: 'Shared'
message:
- 'File Path: {path}'
- '[{shared}]'
short_message:
- '{path}'
```

Boolean helpers are defined as a set of attributes:

* "input_attribute"; required name of the attribute which the value is read from.
* "output_attribute"; required name of the attribute which the formatted value is written to.
* "default_value"; optional default value if there is no corresponding mapping in "values".
* "value_if_false"; optional output value if the boolean input value is False.
* "value_if_true"; optional output value if the boolean input value is True.

#### Custom helpers

Custom helpers can be defined to map a value of an event attribute to custom
formatting code.

```
type: 'conditional'
data_type: 'fs:stat:ntfs'
custom_helpers:
- identifier: 'ntfs_file_reference'
  output_attribute: 'file_reference'
message:
- '{display_name}'
- 'File reference: {file_reference}'
short_message:
- '{filename}'
- '{file_reference}'
```

Here `ntfs_file_reference` references the `NTFSFileReferenceFormatterHelper`,
which is defined in `plaso/formatters/file_system.py`.

Custom helpers are defined as a set of attributes:

* "identifier"; required identifier of the custom format helper.
* "input_attribute"; optional name of the attribute which the value is read from.
* "output_attribute"; optional name of the attribute which the formatted value is written to.

#### Enumeration helpers

Enumeration helpers can be defined to map a value of an event attribute to
a more descriptive value, for example mapping 100 to BEGIN_SYSTEM_CHANGE in
the example below.

```
type: 'conditional'
data_type: 'windows:restore_point:info'
enumeration_helpers:
- input_attribute: 'restore_point_event_type'
  output_attribute: 'restore_point_event_type'
  default_value: 'UNKNOWN'
  values:
    100: 'BEGIN_SYSTEM_CHANGE'
    101: 'END_SYSTEM_CHANGE'
    102: 'BEGIN_NESTED_SYSTEM_CHANGE'
    103: 'END_NESTED_SYSTEM_CHANGE'
- input_attribute: 'restore_point_type'
  output_attribute: 'restore_point_type'
  default_value: 'UNKNOWN'
  values:
    0: 'APPLICATION_INSTALL'
    1: 'APPLICATION_UNINSTALL'
    10: 'DEVICE_DRIVER_INSTALL'
    12: 'MODIFY_SETTINGS'
    13: 'CANCELLED_OPERATION'
message:
- '{description}'
- 'Event type: {restore_point_event_type}'
- 'Restore point type: {restore_point_type}'
short_message:
- '{description}'
```

Enumeration helpers are defined as a set of attributes:

* "input_attribute"; required name of the attribute which the value is read from.
* "output_attribute"; required name of the attribute which the formatted value is written to.
* "default_value"; optional default value if there is no corresponding mapping in "values".
* "values"; required value mappings, contains key value pairs.

#### Flags helpers

Flags helpers can be defined to map a value of an event attribute to a more
descriptive value, for example mapping 0x00000040 to FinderInfoModified in
the example below.

```
type: 'conditional'
data_type: 'macos:fseventsd:record'
flags_helpers:
- input_attribute: 'flags'
  output_attribute: 'flag_values'
  # The include header sys/fsevents.h defines various FSE constants, e.g.
  # #define FSE_CREATE_FILE          0
  # The flag values correspond to: FLAG = 1 << CONSTANT
  values:
    0x00000000: 'None'
    0x00000001: 'Created'
    0x00000002: 'Removed'
    0x00000004: 'InodeMetadataModified'
    0x00000008: 'Renamed'
    0x00000010: 'Modified'
    0x00000020: 'Exchange'
    0x00000040: 'FinderInfoModified'
    0x00000080: 'DirectoryCreated'
    0x00000100: 'PermissionChanged'
    0x00000200: 'ExtendedAttributeModified'
    0x00000400: 'ExtendedAttributeRemoved'
    0x00001000: 'DocumentRevision'
    0x00004000: 'ItemCloned'
    0x00080000: 'LastHardLinkRemoved'
    0x00100000: 'IsHardLink'
    0x00400000: 'IsSymbolicLink'
    0x00800000: 'IsFile'
    0x01000000: 'IsDirectory'
    0x02000000: 'Mount'
    0x04000000: 'Unmount'
    0x20000000: 'EndOfTransaction'
message:
- '{path}'
- 'Flag Values: {flag_values}'
- 'Flags: 0x{flags:08x}'
- 'Event Identifier: {event_identifier}'
short_message:
- '{path}'
- '{flag_values}'
```

Flags helpers are defined as a set of attributes:

* "input_attribute"; required name of the attribute which the value is read from.
* "output_attribute"; required name of the attribute which the formatted value is written to.
* "values"; required value mappings, contains key value pairs.

#### Change log

* 20200227 Added support for formatter configuration files.
* 20200822 Added support for enumeration helpers.
* 20200904 Added support for flags helpers.
* 20200916 Removed source types from formatters.
* 20201220 Added support for boolean helpers.
* 20201227 Added support for custom helpers.

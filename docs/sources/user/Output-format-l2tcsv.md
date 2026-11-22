# l2tcsv output format

By default log2timeline.pl used the l2tcsv (or l2t_csv) output format. l2tcsv
is a CSV (comma separated values) format with 17 fields.

**Note that for Plaso log2timeline l2tcsv is no longer the default.**

The first line in the CSV file is a header, containing the name of each field.
Other lines in the CSV file refer to one or more events. Consecutive events
with the same values that have a Content Modification, Last Access, Metadata
Modification or Creation time description are grouped into a single line, see
the MACB and type fields below.

The header consists of:

```
date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,version,filename,inode,notes,format,extra
```

and the fields contain the following values:

Name | Description
--- | ---
date | The date of the event(s), in the format of "MM/DD/YYYY" (n.b this might get changed in a future version to YYYY-MM-DD, but for now this will stay this way). The date is in the output time zone. If the event has a timestamp of 0, for example because it has no date and time value, the date is "00/00/0000".
time | time of day, expressed in a 24h format, HH:MM:SS (in future versions this may change to include ms values in the format of HH:MM:SS.ms). The time is in the output time zone. If the event has a timestamp of 0 the time is "--:--:--".
timezone | The abbreviation of the output time zone, as determined by the time zone database (pytz). The output time zone is UTC by default and can be changed with the psort `--output_time_zone` option. If the event has a timestamp of 0 the timezone is "-".
MACB | MACB or legacy meaning of the fields, mostly for compatibility with the output of the Sleuthkit mactime utility. For a group of events this contains the letters of all the events in the group, for example "M.C." for a Content Modification Time and a Metadata Modification Time event with the same values.
source | Short name for the source. This may be something like LOG, WEBHIST, REG, etc. This field name should correspond to the type field in the TLN output format and describes the nature of the log format on a high level (all log files are marked as LOG, all registry as REG, etc.)
sourcetype | More comprehensive description of the source. This field further describes the format, such as "Syslog" instead of simply "LOG", "NTUSER.DAT Registry" instead of "REG", etc.
type | type of the timestamp itself, such as “Last Accessed”, “Last Written” or “Last modified”, etc. For a group of events this contains the timestamp descriptions of all the events in the group, separated by "; ".
user | username associated with the entry, if one is available.
host | hostname associated with the entry, if one is available.
short | short description of the entry, usually contains less text than the full description field. This is created to assist with tools that try to visualize the event. In those output the short description is used as the default text, and further information or the full description can be seen by either hovering over the text or clicking on further details about the event.
desc | description field, this is where most of the information is stored. This field is the full description of the field, the interpreted results or the content of the actual log line.
version | version number of the timestamp object. Current version is 2.
filename | display name of the file that contained the entry, such as "OS:/var/log/syslog", where the prefix indicates the type of the file system or storage media image. If the event data defines a display name that is used instead.
inode | inode number of the file that contained the entry, if the event data has an inode, such as the file stat events of a file system. Otherwise "-" unless the psort `--output_fallback_path` option is used, in which case the inode or equivalent identifier, such as the NTFS MFT entry, is taken from the path specification of APFS, EXT, HFS, NTFS and TSK file systems.
notes | labels of the event tag, separated by a space, or "-" if the event was not tagged, for example by the tagging analysis plugin.
format | the Plaso parser chain, which is the name of the parser and plugin(s) that produced the event data, such as "text/syslog_traditional" or "filestat". In log2timeline.pl output this was the name of the input module in the format Log2t::input::NAME.
extra | additional information parsed is joined together and put here. This 'extra' field may contain various information that further describe the event. Some input modules contain additional information about events, such as further divide the event into source IP's, etc. These fields may not fit directly into any other field in the CSV file and are thus combined into this 'extra' field.

## Examples

The examples below were generated with:

```bash
psort.py -o l2tcsv -w timeline.csv test_data/psort_test.plaso
```

A syslog line that was tagged with the labels "exit1" and "exit2":

```
12/18/2012,17:54:32,UTC,M...,LOG,Log File,Content Modification Time,-,myhostname.myhost.com,[anacron  pid: 1234] No true exit can exist (124 job run),[anacron  pid: 1234] No true exit can exist (124 job run),2,OS:/tmp/test/test_data/syslog/syslog,-,exit1 exit2,text/syslog_traditional,sha256_hash: 1f0105612f6ad2d225d6bd9ba631148740e312598878adcd2b74098a3dab50c4
```

A group of a Content Modification Time and a Metadata Modification Time
file stat event with the same values:

```
07/02/2026,17:47:57,UTC,M.C.,FILE,File stat,Content Modification Time; Metadata Modification Time,-,-,/tmp/test/test_data/syslog/syslog,OS:/tmp/test/test_data/syslog/syslog Type: file Owner identifier: 1000 Group identifier: 1000 Mode: 0o644 Number of links: 1,2,OS:/tmp/test/test_data/syslog/syslog,351025,-,filestat,attribute_names: ['security.selinux']; file_size: 1509; file_system_type: OS; is_allocated: True; sha256_hash: 1f0105612f6ad2d225d6bd9ba631148740e312598878adcd2b74098a3dab50c4
```

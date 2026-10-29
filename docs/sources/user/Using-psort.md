# Using psort.py (Plaso Síar Og Raðar Þessu)

**psort** is a command line tool to post-process Plaso storage files. It allows
you to filter, sort and run automatic analysis on the contents of Plaso storage
files.

Looking for [tips and tricks](Using-psort.md#how-do-i)?

## Usage

To see a list of all available parameters you can pass to psort use ``-h`` or
``--help``.

The most basic way to use **psort** is to provide it with a storage file and
output file, for example:

```bash
$ psort.py -w test.log timeline.plaso
```

This will use the default dynamic output format and write to test.log all
extracted events, merging detected duplicate events. All date and time values
will be in UTC.

**Note that as of 1.5.0 psort no longer supports writing output to stdout.**

Some other basic options are:

```bash
$ psort.py [-a] [-o FORMAT] [-w OUTPUTFILE] [--output-time-zone TIME_ZONE] STORAGE_FILE FILTER
```

### Output format

**psort** uses output modules to output in different formats. To see a list of
the available supported output modules use the ``-o list`` parameter, for example:

```bash
$ psort.py -o list

******************************** Output Modules ********************************
         Name : Description
--------------------------------------------------------------------------------
      dynamic : Dynamic selection of fields for a separated value output
                format.
         json : Saves the events into a JSON format.
    json_line : Saves the events into a JSON line format.
          kml : Saves events with geography data into a KML format.
       l2tcsv : CSV format used by legacy log2timeline, with 17 fixed fields.
       l2ttln : Extended TLN 7 field | delimited output.
         null : Output module that does not output anything.
   opensearch : Saves the events into an OpenSearch database.
opensearch_ts : Saves the events into an OpenSearch database for use with
                Timesketch.
        rawpy : native (or "raw") Python output.
          tln : TLN 5 field | delimited output.
         xlsx : Excel Spreadsheet (XLSX) output
--------------------------------------------------------------------------------
```

If you are missing any optional dependencies not all output modules may be
available, which would be displayed by the ``-o list`` switch, for example:

```bash
******************************** Output Modules ********************************
     Name : Description
--------------------------------------------------------------------------------
  dynamic : Dynamic selection of fields for a separated value output format.
     json : Saves the events into a JSON format.
json_line : Saves the events into a JSON line format.
      kml : Saves events with geography data into a KML format.
   l2tcsv : CSV format used by legacy log2timeline, with 17 fixed fields.
   l2ttln : Extended TLN 7 field | delimited output.
     null : Output module that does not output anything.
    rawpy : native (or "raw") Python output.
      tln : TLN 5 field | delimited output.
     xlsx : Excel Spreadsheet (XLSX) output
--------------------------------------------------------------------------------

*************************** Disabled Output Modules ****************************
         Name : Description
--------------------------------------------------------------------------------
   opensearch : Saves the events into an OpenSearch database.
opensearch_ts : Saves the events into an OpenSearch database for use with
                Timesketch.
--------------------------------------------------------------------------------
```

Also see [output and formatting](Output-and-formatting.md).

#### Changing output format

To change the output use the ``-o FORMAT`` parameter, for example:

```bash
$ psort.py -o l2tcsv -w test.l2tcsv timeline.plaso
```

This would use the "l2tcsv" output module, which is the CSV output of the older
Perl version of log2timeline.

#### Modify the output time zone

**psort** uses UTC as its default time zone when outputting events. Some
output formats, like dynamic and l2tcsv can output date and time values in
a different time zone. This can be controlled using the
``--output-time-zone TIME_ZONE`` parameter, for example.

```bash
$ psort.py --output-time-zone EST5EDT -w tz.csv timeline.plaso
$ head -n 3 tz.csv
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag
2012-01-22T02:52:33.000000-05:00,Content Modification Time,LOG,Log File,[client  pid: 30840] INFO No change in [/etc/netgroup]. Done,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
2012-01-22T02:52:33.000000-05:00,Content Modification Time,LOG,Log File,[client  pid: 30840] INFO No new content in ímynd.dd.,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
```

To see a list of all supported time zones use the `--output-time-zone list`
parameter:

```bash
$ psort.py --output-time-zone list

************************************ Zones *************************************
                       Time zone : UTC Offset
--------------------------------------------------------------------------------
                  Africa/Abidjan : +00:00
                    Africa/Accra : +00:00
              Africa/Addis_Ababa : +03:00
                  Africa/Algiers : +01:00
                   Africa/Asmara : +03:00
                   Africa/Asmera : +03:00
                   Africa/Bamako : +00:00
...
```

#### Output fields

Several parameters control which fields are written to the output and how
their values are formatted:

+ ``--fields FIELDS`` defines a comma separated list of the fields to include in the output, instead of the default fields. Output formats that support this are: dynamic and xlsx.
+ ``--additional_fields ADDITIONAL_FIELDS`` defines a comma separated list of fields to include in addition to the default fields.
+ ``--custom_fields CUSTOM_FIELDS`` defines a comma separated list of fields with a fixed value, each in the form "name:value".
+ ``--dynamic_time`` writes date and time values with the granularity of the original timestamp, instead of a fixed number of fractional seconds.
+ ``--output_fallback_hostname`` uses the hostname derived by pre-processing when an event has no hostname.
+ ``--output_fallback_path`` uses the path specification of the event data stream when an event has no filename or inode.
+ ``--custom_formatter_definitions PATH`` reads custom event formatter definitions from a YAML file, to customize or override the built-in event messages.
+ ``--language LANGUAGE_TAG`` defines the preferred language of Windows EventLog message strings. Use ``--language list`` to see the supported language tags.

For example, to only output the date and time, timestamp description, message
and tag fields:

```bash
$ psort.py --fields datetime,timestamp_desc,message,tag -w fields.csv timeline.plaso
$ head -n 4 fields.csv
datetime,timestamp_desc,message,tag
2012-01-22T07:52:33.000000+00:00,Content Modification Time,[client  pid: 30840] INFO No change in [/etc/netgroup]. Done,-
2012-01-22T07:52:33.000000+00:00,Content Modification Time,[client  pid: 30840] INFO No new content in ímynd.dd.,-
2012-01-22T07:53:01.000000+00:00,Content Modification Time,Cron ran: touch /var/run/crond.somecheck for user: root pid: 31051,application_execution
```

See [output and formatting](Output-and-formatting.md) for the fields supported
by each output module.

#### Quiet and More Verbose Output

**psort** records the number of events it processes and how many events got
filtered out due to filter settings, time slices or duplicate removals. This
information is shown in the status view while **psort** runs, for example
at the end of a full run:

```bash
$ psort.py -w timeline.csv timeline.plaso
...
plaso - psort version 20261025

Storage file		: timeline.plaso
Processing time		: 00:00:02

Events:         Filtered        In time slice   Duplicates      MACB grouped    Total
                0               0               18              20              38

Identifier              PID     Status          Memory          Events          Tags            Reports
Main                    1517207 completed       87.9 MiB        38 (0)          0 (0)           0 (0)

Processing completed.
```

This output provides valuable information about how many events got filtered
out by for instance the duplicate entry removals. There are many reasons why
there may be duplicate entries in an output:

+ A filesystem entry that has the same timestamp for MACB timestamps (or any combination of them)
+ Parsing a storage media file and processing a VSS store will produce a lot of duplicate entries, for example: the exact same Event Log record.
+ Metadata information extracted from a file that is stored in more than one place on the drive

If you don't want duplicate entries to be removed it is possible to supply the
flag ``-a`` or ``--include_all`` to **psort**.

```bash
$ psort.py -a -w all_events.txt timeline.plaso
```

If you on the other hand do not want to see the status view it is possible to
disable it with ``--status_view none``. The ``-q`` flag suppresses the
"Processing completed." message and the details of analysis reports printed at
the end of the run. To run **psort** without any console output combine both:

```bash
$ psort.py -q --status_view none -w output.csv timeline.plaso
```

### Automatic Analysis

Plaso defines a concept called an analysis plugin. Essentially that means that
you can write a plugin that gets a copy of every event that is extracted and is
not filtered out to inspect and potentially extract meaning or context out of.
This information can be used to create tags and attach them back to the events
or to create reports.

The analysis plugins are only exposed to the post-processing layer, as in
exposed to **psort**.

The syntax works by using the ``--analysis PLUGIN`` syntax, for example:

```bash
$ psort.py --analysis PLUGIN_NAME ...
```

To get a full list of the available plugins use the ``--analysis list`` parameter:

```bash
$ psort.py --analysis list

******************************* Analysis Plugins *******************************
                  Name : Description
--------------------------------------------------------------------------------
                 bloom : Analysis plugin for looking up hashes in bloom
                         database. [Summary/Report plugin]
        browser_search : Analyze browser search entries from events.
                         [Summary/Report plugin]
      chrome_extension : Analysis plugin to gather information about Chrome
                         extensions. [Summary/Report plugin]
               nsrlsvr : Analysis plugin for looking up hashes in nsrlsvr.
                         [Summary/Report plugin]
            sessionize : Analysis plugin that labels events by session.
                         [Summary/Report plugin]
               tagging : Analysis plugin that labels events according to rules
                         in a tagging file. [Summary/Report plugin]
unique_domains_visited : A plugin to generate a list all domains visited.
                         [Summary/Report plugin]
            virustotal : An analysis plugin for looking up hashes in
                         VirusTotal. [Summary/Report plugin]
--------------------------------------------------------------------------------
```

Some of these plugins may provide additional parameters that may be required
for each analysis plugin. To know which parameters are exposed use the ``-h``
flag in addition to the ``--analysis PLUGIN``, for example:

```bash
$ psort.py --analysis virustotal -h
...
Analysis Arguments:
  --analysis PLUGIN_LIST
                        A comma separated list of analysis plugin names to be
                        loaded or "--analysis list" to see a list of available
                        plugins.
  --virustotal-api-key, --virustotal_api_key API_KEY
                        Specify the API key for use with VirusTotal.
  --virustotal-free-rate-limit, --virustotal_free_rate_limit
                        Limit Virustotal requests to the default free API key
                        rate of 4 requests per minute. Set this to false if
                        you have an key for the private API.
  --virustotal-hash, --virustotal_hash HASH
                        Type of hash to query VirusTotal, the default is:
                        sha256
...
```

An example run could therefore be:

```bash
$ psort.py -o null --analysis tagging --tagging-file tag_linux.txt timeline.plaso
```

What this does is:

+ Uses the "*null*" output module, that is it does not print out any events.
+ Runs the tagging analysis plugin. This analysis plugin runs through each event, compares that to the list of tags you provide to the tool and applies the appropriate tags.
+ Uses the file "tag_linux.txt" as a source of all tags to apply.

The filter file that is passed on is searched for using the provided path as an
absolute, relative path or relative to the [data](https://github.com/log2timeline/plaso/tree/main/plaso/data)
directory.

The file [tag_linux.txt](https://github.com/log2timeline/plaso/blob/main/plaso/data/tag_linux.txt)
for instance is a file that is found inside the data directory and can thus be
used without creating any file.

At the end of the run the tool will produce a summary or reports of the
analysis plugins:

```bash
...
*************************** Analysis report: tagging ***************************
Date and time : 2026-10-29T11:51:06.000000+00:00
 Event filter : N/A
      Results : application_execution: 6
              : event_tags: 6
--------------------------------------------------------------------------------
```

And in this case, since this was tagging the results of what tags were provided
can be viewed using **pinfo**:

```bash
$ pinfo.py timeline.plaso
...
************************ Event tags generated per label ************************
                Label : Number of event tags
--------------------------------------------------------------------------------
application_execution : 6
                exit1 : 2
                exit2 : 2
             repeated : 4
                Total : 14
--------------------------------------------------------------------------------
...
```

The tags are now included in the output:

```bash
$ psort.py -w output_tags.csv timeline.plaso
$ grep "application_execution" output_tags.csv
2012-01-22T07:53:01.000000+00:00,Content Modification Time,LOG,Cron log,Cron ran: touch /var/run/crond.somecheck for user: root pid: 31051,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,application_execution
2012-01-22T07:54:01.000000+00:00,Content Modification Time,LOG,Cron log,Cron ran: /sbin/status.mycheck) for user: root pid: 31067,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,application_execution
2012-01-22T07:54:01.000000+00:00,Content Modification Time,LOG,Cron log,Cron ran: touch /var/run/crond.somecheck for user: root pid: 31068,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,application_execution
```

**TODO: Move this documentation to a separate analysis plugin site and include
information about the rest of the plugins.**

### Filtering

It is possible to filter out the results **psort** provides using few different
methods:

+ If you have a timestamp of interest a time slice, where only events that occur X minutes before and after that timestamp are included
+ Provide a granular filter for timestamps and/or content of various attributes
+ If you've got a regular filter and want to include events that occurred just before and after the events that match the filter.

#### Time Slices

The simplest filter is the time slice, where if you've discovered an
interesting timestamp and would like to explore what occurred just prior and
after that timestamp of interest. This can be achieved using the ``--slice
DATE_TIME`` parameter, for example:

**Note that as of 20200613 the date and time parameter of ``--slice`` must
be defined in ISO 8601 format, for example 2020-06-19T20:09:23+02:00. The
time zone offset is optional and defaults to UTC.**

```bash
$ psort.py --slice "2014-11-18T08:30:00" -w slice.csv timeline.plaso
$ cat slice.csv
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag
2014-11-18T08:30:20.000000+00:00,Content Modification Time,LOG,Log File,[kernel] [997.390602] sda2: rw=0  want=65  limit=2,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
2014-11-18T08:31:20.000000+00:00,Content Modification Time,LOG,Log File,[kernel] [998.390602] sda2: rw=0  want=66  limit=2,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
```

By default the tool chooses 5 minutes prior and after the timestamp in
question. To configure that use the ``--slice_size SLICE_SIZE`` parameter.

```bash
$ psort.py --slice "2014-11-18T08:30:00" --slice_size 1 -w slice_size.csv timeline.plaso
$ cat slice_size.csv
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag
2014-11-18T08:30:20.000000+00:00,Content Modification Time,LOG,Log File,[kernel] [997.390602] sda2: rw=0  want=65  limit=2,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
```

#### Filters

A more comprehensive discussions of the filters can be [read here](Event-filters.md).

For **psort** the filters are included at the end of the command line
arguments, for example:

```bash
$ psort.py -w output.csv timeline.plaso FILTER
```

An example filter that filters out all events within a certain time range:

```bash
$ psort.py -w filter.csv timeline.plaso "date < DATETIME('2012-01-22T07:54:00') and date > DATETIME('2012-01-22T07:52:00')"
$ cat filter.csv
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag
2012-01-22T07:52:33.000000+00:00,Content Modification Time,LOG,Log File,[client  pid: 30840] INFO No change in [/etc/netgroup]. Done,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
2012-01-22T07:52:33.000000+00:00,Content Modification Time,LOG,Log File,[client  pid: 30840] INFO No new content in ímynd.dd.,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
2012-01-22T07:53:01.000000+00:00,Content Modification Time,LOG,Cron log,Cron ran: touch /var/run/crond.somecheck for user: root pid: 31051,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,application_execution
```

#### Filter and Include Surrounding Events

If you have something interesting that you want to filter but you also want to
include some context surrounding those matches you can run the tool with the
flag ``--slicer`` in addition to the filter.

An example:

```bash
$ psort.py -w match.csv timeline.plaso "message_body contains 'single character day'"
$ cat match.csv
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag
2014-02-06T15:16:30.000000+00:00,Content Modification Time,LOG,Log File,[process  pid: 2085] Test message with single character day,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
```

Here the filter ``message_body contains 'single character day'`` is applied to
the output searching for all syslog lines that contain the text "single
character day". If we wanted to gather some context surrounding these events we
can supply the ``--slicer`` flag, for example:

```bash
$ psort.py --slicer -w slicer.csv timeline.plaso "message_body contains 'single character day'"
$ cat slicer.csv
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag
2013-03-23T23:01:18.000000+00:00,Content Modification Time,LOG,Log File,[somrandomexe  pid: 19] This syslog message has a fractional value for seconds.,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
2013-11-18T01:15:20.000000+00:00,Content Modification Time,LOG,Log File,[aprocess  pid: 10100] This is a multi-line message that screws up	many syslog parsers.,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
2013-12-31T17:54:32.000000+00:00,Content Modification Time,LOG,Log File,[/sbin/anacron  pid: 1234] Another one just like this (124 job run),text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
2014-02-06T15:16:30.000000+00:00,Content Modification Time,LOG,Log File,[process  pid: 2085] Test message with single character day,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
2014-11-18T01:15:43.000000+00:00,Content Modification Time,LOG,Log File,[---] last message repeated 5 times ---,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,repeated
2014-11-18T08:30:20.000000+00:00,Content Modification Time,LOG,Log File,[kernel] [997.390602] sda2: rw=0  want=65  limit=2,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
2014-11-18T08:31:20.000000+00:00,Content Modification Time,LOG,Log File,[kernel] [998.390602] sda2: rw=0  want=66  limit=2,text/syslog_traditional,OS:/tmp/test/test_data/syslog/syslog,-
```

By default the tool will include five events before and after each filter match.
These events are counted before duplicate removal, so fewer events can be
shown. This can be controlled using the ``--slice_size``.

```bash
$ psort.py --slice_size 15 --slicer -w slicer_15.csv timeline.plaso "message_body contains 'single character day'"
```

### Other options

The [data](https://github.com/log2timeline/plaso/tree/main/plaso/data) folder
was [previously mentioned](Using-psort.md#automatic-analysis). The location of
this folder is automatically determined, depending on how the tool got installed
on the system and the OS platform. This data path is used by **psort** to find
the location of filter files, Event Log message database, etc.

This data path can be changed from the default location, for instance if you
have your own *winevt-rc.db* database or set of filter files. This can be
achieved using the ``--data PATH`` parameter, for example:

```bash
$ psort.py --data /where/my/data/is/stored -w output.csv timeline.plaso
```

#### Debug

If during the runtime of **psort** the tool encounters an unexpected exception
the debug mode can be used. To invoke debug mode use the ``-d`` parameter,
which enables debug output, such as debug log messages, that can help to
determine the cause of the problem.

## How do I?

### How do I filter on tags?

```bash
psort.py -w timeline.log timeline.plaso "tag contains 'browser_search'"
```

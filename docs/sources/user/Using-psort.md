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
$ psort.py --output-time-zone EST5EDT timeline.plaso
```

To see a list of all supported time zones use the `--output-time-zone list`
parameter:

```bash
$ psort.py --output-time-zone list

************************************ Zones *************************************
                        Timezone : UTC Offset
                  Africa/Abidjan : +00:00
                    Africa/Accra : +00:00
              Africa/Addis_Ababa : +03:00
                  Africa/Algiers : +01:00
                   Africa/Asmara : +03:00
                   Africa/Asmera : +03:00
...
```

#### Quiet and More Verbose Output

**psort** records the number of events it processes and how many events got
filtered out due to filter settings or to duplication removals. This
information is printed out at the end of each run, for example:

```bash
$ psort.py timeline.plaso "SELECT timestamp LIMIT 10"
...
[INFO] Output processing is done.

*********************************** Counter ************************************
            Stored Events : 143960
          Events Included : 10
               Limited By : 10
```

Or from a full run:

```bash
$ psort.py timeline.plaso
...
*********************************** Counter ************************************
            Stored Events : 143960
          Events Included : 143812
       Duplicate Removals : 23157

```

This output provides valuable information about how many events got filtered
out by for instance the duplicate entry removals. There are many reasons why
there may be duplicate entries in an output:

+ A filesystem entry that has the same timestamp for MACB timestamps (or any combination of them)
+ Parsing a storage media file and processing a VSS store will produce a lot of duplicate entries, for example: the exact same Event Log record.
+ Metadata information extracted from a file that is stored in more than one place on the drive

If you don't want duplicate entries to be removed it is possible to supply the
flag ``-a`` or ``--include_all` to **psort**.

```bash
$ psort.py -a -w all_events.txt timeline.plaso
```

If you on the other hand do not want to see the overview printed at the end it
is possible to silence it with the ``-q`` flag:

```bash
$ psort.py -q -w output.csv timeline.plaso
```

### Automatic Analysis

Plaso defines a concept called an analysis plugin. Essentially that means that
you can write a plugin that gets a copy of every event that is extracted and is
not filtered out to inspect and potentially extract meaning or context out of.
This information can be used to create tags and attach them back to the events
or to create reports.

As of now the analysis plugins are only exposed to the post-processing layer,
as in exposed to **psort** although there are efforts underway to expose them
to the extraction stage as well. That way you can use them to create tags that
are immediately available in post processing.

The syntax works by using the ``--analysis PLUGIN`` syntax, for example:

```bash
$ psort.py --analysis PLUGIN_NAME ...
```

To get a full list of the available plugins use the ``--analysis list`` parameter:

```bash
$ psort.py --analysis list

******************************* Analysis Plugins *******************************
  browser_search : Analyze browser search entries from events. [Summary/Report
                   plugin]
chrome_extension : Convert Chrome extension IDs into names, requires Internet
                   connection. [Summary/Report plugin]
         tagging : Analysis plugin that tags events according to rules in a
                   tag file. [Summary/Report plugin]
           viper : An analysis plugin for looking up SHA256 hashes in Viper.
                   [Summary/Report plugin]
      virustotal : An analysis plugin for looking up hashes in VirusTotal.
                   [Summary/Report plugin]
windows_services : Provides a single list of for Windows services found in the
                   Registry. [Summary/Report plugin]
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
  --virustotal-api-key VIRUSTOTAL-API-KEY
                        Specify the API key for use with VirusTotal.
  --virustotal-free-rate-limit VIRUSTOTAL-RATE-LIMIT
                        Limit Virustotal requests to the default free API key
                        rate of 4 requests per minute. Set this to false if
                        you have an key for the private API.
  --windows-services-output {text,yaml}
                        Specify how the results should be displayed. Options
                        are text and yaml.
  --viper-host VIPER-HOST
                        Specify the host to query Viper on.
  --viper-protocol {http,https}
                        Protocol to use to query Viper.
  --tagging-file TAGGING_FILE
                        Specify a file to read tagging criteria from.
...
```

An example run could therefore be:

```bash
$ psort.py -o null --analysis tagging --tagging-file tag_windows.txt timeline.plaso
```

What this does is:

+ Uses the "*null*" output module, that is it does not print out any events.
+ Runs the tagging analysis plugin. This analysis plugin runs through each event, compares that to the list of tags you provide to the tool and applies the appropriate tags.
+ Uses the file "tag_windows.txt" as a source of all tags to apply.

The filter file that is passed on is searched for using the provided path as an
absolute, relative path or relative to the [data](https://github.com/log2timeline/plaso/tree/main/data)
directory.

The file [tag_windows.txt](https://github.com/log2timeline/plaso/blob/main/data/tag_windows.txt)
for instance is a file that is found inside the data directory and can thus be
used without creating any file.

At the end of the run the tool will produce a summary or reports of the
analysis plugins:

```bash
[INFO] All analysis plugins are now completed.
Report generated from: tagging
Generated on: 2015-07-31T17:38:32+00:00

Report text:
Tagging plugin produced 146 tags.
```

And in this case, since this was tagging the results of what tags were provided
can be viewed using **pinfo**:

```bash
$ pinfo.py timeline.plaso
...
Parser counter information:
	Counter: Total Tags = 146
	Counter: Application Execution = 144
	Counter: Document Printed = 2
...
```

The tags are now included in the output:

```bash
$ psort.py -w output_tags.csv timeline.plaso
$ grep "Document Printed" output_tags.csv
1999-05-15T15:39:16+00:00,Document Last Printed Time,OLECF,OLECF Summary Info,Title: Microsoft Powertoys for Windows XP  Subject: Powertoys Author: Microsoft Corporation Keywords: Powertoy Template: Intel;1033 Revision number: {1DA2A275-1387-4A40-8453-EFDF70F62811} Last saved by: InstallShield  Number of pages: 110 Number of words: 0 Number of characters: 0 Application: InstallShield® Developer 7.0 Security: 0x00000001: Password protected,olecf/olecf_summary,TSK:/WINDOWS/Downloaded Installations/Powertoys For Windows XP.msi;TSK:/WINDOWS/Installer/ac704.msi,Document Printed,1,888
...
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
be defined in ISO 8601 format.**

```bash
$ psort.py -q --slice "2004-09-20T16:13:02" timeline.plaso
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag,store_number,store_index
2004-09-20T16:13:02+00:00,Expiration Time,WEBHIST,MSIE Cache File URL record,Location: Visited: Mr. Evil@http://www.microsoft.com/windows/ie/getosver/javaxp.asp Number of hits: 2 Cached file size: 0,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/History/History.IE5/index.dat,-,1,143661
2004-09-20T16:13:12+00:00,Expiration Time,WEBHIST,MSIE Cache File URL record,Location: Visited: Mr. Evil@http://fosi.ural.net Number of hits: 1 Cached file size: 0,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/History/History.IE5/index.dat,-,1,143663
2004-09-20T16:13:12+00:00,Expiration Time,WEBHIST,MSIE Cache File URL record,Location: :2004082520040826: Mr. Evil@http://fosi.ural.net Number of hits: 1 Cached file size: 0,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/History/History.IE5/MSHist012004082520040826/index.dat,-,1,143662
```

By default the tool chooses 5 minutes prior and after the timestamp in
question. To configure that use the ``--slice_size SLICE_SIZE`` parameter.

```bash
$ psort.py -q --slice "2004-09-20T16:13:02" --slice_size 100 timeline.plaso
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag,store_number,store_index
2004-09-20T15:18:38+00:00,Expiration Time,WEBHIST,MSIE Cache File URL record,Location: :2004082520040826: Mr. Evil@http://www.yahoo.com Number of hits: 1 Cached file size: 0,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/History/History.IE5/MSHist012004082520040826/index.dat,-,1,143624
2004-09-20T15:18:38+00:00,Expiration Time,WEBHIST,MSIE Cache File URL record,Location: Visited: Mr. Evil@http://www.yahoo.com Number of hits: 1 Cached file size: 0,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/History/History.IE5/index.dat,-,1,143625
2004-09-20T15:18:54+00:00,Expiration Time,WEBHIST,MSIE Cache File URL record,Location: Visited: Mr. Evil@http://www.yahoo.com/_ylh=X3oDMTB1M2EzYWFoBF9TAzI3MTYxNDkEdGVzdAMwBHRtcGwDaWUtYmV0YQ--/s/208739 Number of hits: 1 Cached file size: 0,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/History/History.IE5/index.dat,-,1,143626
2004-09-20T15:19:00+00:00,Expiration Time,WEBHIST,MSIE Cache File URL record,Location: :2004082520040826: Mr. Evil@http://story.news.yahoo.com/news?tmpl=story&cid=564&ncid=564&e=1&u=/nm/20040825/ts_nm/iraq_usa_beheading_dc Number of hits: 1 Cached file size: 0,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/History/History.IE5/MSHist012004082520040826/index.dat,-,1,143627
...
```

#### Filters

A more comprehensive discussions of the filters can be [read here](Event-filters.md).

For **psort** the filters are included at the end of the command line
arguments, for example:

```bash
$ psort.py -q timeline.plaso FILTER
```

An example filter that filters out all events within a certain time range:

```bash
$ psort.py -q  timeline.plaso "date < '2004-09-20 16:20:00' and date > '2004-09-20 16:10:00'"
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag,store_number,store_index
2004-09-20T16:13:02+00:00,Expiration Time,WEBHIST,MSIE Cache File URL record,Location: Visited: Mr. Evil@http://www.microsoft.com/windows/ie/getosver/javaxp.asp Number of hits: 2 Cached file size: 0,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/History/History.IE5/index.dat,-,1,143661
...
```

#### Filter and Include Surrounding Events

If you have something interesting that you want to filter but you also want to
include some context surrounding those matches you can run the tool with the
flag ``--slicer`` in addition to the filter.

An example:

```bash
$ psort.py -q timeline.plaso "cached_file_size is 43"
[INFO] Data files will be loaded from /usr/share/plaso by default.
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag,store_number,store_index
1994-04-15T00:00:00+00:00,Content Modification Time,WEBHIST,MSIE Cache File URL record,Location: http://us.i1.yimg.com/us.yimg.com/i/us/hdr/el/uh_bk.gif Number of hits: 5 Cached file: PTV39NDQ\uh_bk[1].gif Cached file size: 43 HTTP headers: HTTP/1.0 200 OK - Content-Type: image/gif - Content-Length: 43 -  - ~U:mr. evil - ,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/index.dat,-,1,370
...
```

Here the filter ``cached_file_size is 43`` is applied to the output searching
for all IE cache files that are 43 bytes in size. If we wanted to gather some
context surrounding these events we can supply the ``--slicer`` flag, for
example:

```bash
$ psort.py --slicer -q timeline.plaso "cached_file_size is 43"
datetime,timestamp_desc,source,source_long,message,parser,display_name,tag,store_number,store_index
...
2001-02-23T03:15:06+00:00,Content Modification Time,WEBHIST,MSIE Cache File URL record,Location: http://www.2600.org/images/masthead2.jpg Number of hits: 1 Cached file: JIRVJY9X\masthead2[1].jpg Cached file size: 2558 HTTP headers: HTTP/1.0 200 OK - ETag: "565062-9fe-3a95d5ba" - Content-Length: 2558 - Content-Type: image/jpeg -  - ~U:mr. evil - ,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/index.dat,-,1,1413
2001-02-23T03:15:21+00:00,Content Modification Time,WEBHIST,MSIE Cache File URL record,Location: http://www.2600.org/images/sch23.gif Number of hits: 1 Cached file: PN0J7OQM\sch23[1].gif Cached file size: 11739 HTTP headers: HTTP/1.1 200 OK - ETag: "565064-2ddb-3a95d5c9" - Content-Length: 11739 - Content-Type: image/gif -  - ~U:mr. evil - ,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/index.dat,-,1,1414
2001-02-24T18:46:19+00:00,Content Modification Time,WEBHIST,MSIE Cache File URL record,Location: http://www.2600.org/images/1.gif Number of hits: 1 Cached file: HYU1BON0\1[1].gif Cached file size: 43 HTTP headers: HTTP/1.1 200 OK - ETag: "565065-2b-3a98017b" - Content-Length: 43 - Content-Type: image/gif -  - ~U:mr. evil - ,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/index.dat,-,1,1415
2001-02-24T20:51:57+00:00,Content Modification Time,WEBHIST,MSIE Cache File URL record,Location: http://www.2600.org/images/storeadmed.jpg Number of hits: 1 Cached file: HYU1BON0\storeadmed[1].jpg Cached file size: 4323 HTTP headers: HTTP/1.0 200 OK - ETag: "565066-10e3-3a981eed" - Content-Length: 4323 - Content-Type: image/jpeg -  - ~U:mr. evil - ,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/index.dat,-,1,1416
2001-02-24T22:19:38+00:00,Content Modification Time,WEBHIST,MSIE Cache File URL record,Location: http://www.2600.org/images/oldmasthead.gif Number of hits: 1 Cached file: PN0J7OQM\oldmasthead[1].gif Cached file size: 26273 HTTP headers: HTTP/1.1 200 OK - ETag: "565067-66a1-3a98337a" - Content-Length: 26273 - Content-Type: image/gif -  - ~U:mr. evil - ,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/index.dat,-,1,1417
2001-02-26T05:16:09+00:00,Content Modification Time,WEBHIST,MSIE Cache File URL record,Location: http://www.2600.org/images/725274831586.gif Number of hits: 1 Cached file: PN0J7OQM\725274831586[1].gif Cached file size: 1568 HTTP headers: HTTP/1.1 200 OK - ETag: "565068-620-3a99e699" - Content-Length: 1568 - Content-Type: image/gif -  - ~U:mr. evil - ,msiecf,TSK:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/index.dat,-,1,1418
...
```

By default the tool will include five events before and after each filter match.
This can be controlled using the ``--slice_size``.

```bash
$ psort.py --slice_size 15 --slicer -q timeline.plaso "cached_file_size is 43"
```

### Other options

The [data](https://github.com/log2timeline/plaso/tree/main/data) folder was
[previously mentioned](Using-psort.md#automatic-analysis). The location of this
folder is automatically determined, depending on how the tool got installed on
the system and the OS platform. This data path is used by **psort** to find the
location of filter files, Event Log message database, etc.

This data path can be changed from the default location, for instance if you
have your own *winevt-rc.db* database or set of filter files. This can be
achieved using the ``--data PATH`` parameter, for example:

```bash
$ psort.py --data /where/my/data/is/stored timeline.plaso
```

#### Debug

If during the runtime of **psort** the tool encounters an unexpected exception
the debug mode can be used. To invoke debug mode use the ``-d`` parameter. What
that will do is that instead of exiting the tool when an unexpected exception
is raised it prints the traceback of the exception and drops into a
[Python debug shell](https://stackoverflow.com/questions/4228637/getting-started-with-the-python-debugger-pdb).
This can be used to debug the problem and fix the issue.

## How do I?

### How do I filter on tags?

```bash
psort.py -w timeline.log timeline.plaso "tag contains 'browser_search'"
```


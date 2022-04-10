# Switching from Log2Timeline Perl (Legacy) to Plaso

This page contains information for those that are used to using the 0.x version
of log2timeline, also known as Log2Timeline Perl or Log2Timeline legacy.

The syntax has changed somewhat from the 0.x version, the largest differences
may be:

* The output of the tool is no longer controllable through the log2timeline.py command line tool (or front-end). There is only one storage mechanism and that is the Plaso storage file. To produce an output file comparable with the 0.x version you'll need to run the psort.py command line tool with l2t_csv output module.
* The log2timeline.py command line tool can extract events **directly** from storage media images, such as raw or E01. Removing the need to manually mounting these images.
* The names of the parser have changed. There are a numerous new parsers, but note that some of the older parsers have not been ported.
* The post-processing tool is no longer called l2t_process, it is now named **psort.py**.
* The command line parameters and options have changed considerably. More information below.

In the information below the name Plaso is the name of the new back-end as
opposed to Log2Timeline which is the old Perl back-end. log2timeline.py is
a CLI tool (or front-end). There are other front-ends to the tool though, for
example [Timesketch](https://github.com/google/timesketch).

Let's go over the old and new method of collecting a timeline from a raw
storage media image file.

## Old method

First of all we needed to mount the image. Something like this:

```bash
sudo mount -t ntfs-3g -o ro,nodev,noexec,show_sys_files,streams_interface=windows,loop,offset=32256 image.dd /mnt/nfts
```

Then we needed to run log2timeline against the mount point. You needed to
define the timezone of the suspect image, which could get overwritten if a
correct value was found and you needed to define which parsers to use. The
sample run is:

```bash
cd /mnt/ntfs
log2timeline -r -p -z CST6CDT -f win7 . > /cases/timeline/myhost.csv 2> /cases/timeline/myhost.log
```

This would pick all the parsers defined in the "win7" list and run those
against every file found in the mount point. A list of all available parsers
and lists could be produced by running:

```bash
log2timeline -f list
```

As noted earlier, the above approach would produce a large "kitchen-sink"
approach timeline that is not sorted. To sort that one (no filtering):

```bash
cd /cases/timeline
l2t_process.py -b myhost.csv > myhost.sorted.csv
```

Now we would have a large sorted CSV file ready to analyze.

Limiting the output to a specific date could be achieved using methods like:

```bash
l2t_process.py -b myhost.csv 10-10-2012..10-11-2012
```

However, you could not limit the output of the timeline to a more narrow
timeframe than a single day, for that you needed grep (or some other tools of
choice).

```bash
l2t_process.py -b myhost.csv 10-10-2012..10-11-2012 | grep ",1[8-9]:[0-5][0-9]:[0-9][0-9],"
```

And filtering based on content was constrained to few options:
* Use a keyword file that contained case-insensitive regular expressions to include or exclude events.
* Use a YARA rule that matched against the description_long field.
* Use grep/sed/awk.

The problem with most of the l2t_process filtering is that it was either done
on the whole line or against the description_long field. There was no easy way
to filter against a more specific attribute of the event.

## New method

Since the new version works directly on a raw image file there is no need to
mount the image first (and mounting them is actually highly discouraged), the
timeline can be created in a single step:

```bash
log2timeline.py --storage-file /cases/timeline/timeline.plaso image.dd
```

The tool will detect whether or not the input is a file, directory or a disk
image/partition. If the tool requires additional information, such as when VSS
stores are detected or more than a single partition in the volume the tool will
ask for additional details. An example of that:

```
The following Volume Shadow Snapshots (VSS) were found:
Identifier      VSS store identifier                    Creation Time
vss1            23b509aa-3499-11e3-be88-24fd52566ede    2013-10-16T13:18:01.685825+00:00
vss2            8dfc93b3-376f-11e3-be88-24fd52566ede    2013-10-18T00:28:29.120593+00:00
vss3            dc8ffcf4-3a6b-11e3-be8a-24fd52566ede    2013-10-21T19:24:50.879381+00:00

Please specify the identifier(s) of the VSS that should be processed:
Note that a range of stores can be defined as: 3..5. Multiple stores can
be defined as: 1,3,5 (a list of comma separated values). Ranges and lists can
also be combined as: 1,3..5. The first store is 1. If no stores are specified
none will be processed. You can abort with Ctrl^C.
```

The options can also be supplied on the command line, `--vss_stores '1,2'` for
defining the VSS stores to parse, or `--no-vss` or `-vss-stores all` for
processing all VSS stores.

This can be achieved without calculating the offset into the disk image.

```bash
log2timeline.py --partitions 2 --storage-file /cases/timeline/timeline.plaso image.dd
```

First of all there is quite a difference in the number of parameters, let's go
slightly over them:

* There is no `-r` for recursive, when the tool is run against an image or a directory recursive is automatically assumed, run it against a single file and it recursion is not turned on.
* There is no need to supply the tool with the `-p` (preprocessing) when run against an image, that is automatically turned on.
* The `-z CST6CDT` is not used here. The tool does automatically pick up the timezone and use that. However in the case the timezone is not identified the option is still possible and in fact if not provided uses UTC as the timezone.
* You may have noticed there is no `-f list` parameter used. The notion of selecting filters is now removed and is done automatically. The way the tool now works is that it tries to "guess" the OS and select the appropriate parsers based on that selection. The categories that are available can  be found here or by issuing `log2timeline.py --info`. If you want to overwrite the automatic selection of parsers you can define them using the `--parsers` parameter.
* You have to supply the tool with the parameter to define where to save the output (can no longer just output to STDOUT and pipe it to a file).

The equivalent call of the old tool of `-f list` can now be found using
`--info`. That will print out all available parsers and plugins in the tool.
One thing to take note of is the different concepts of either plugins or
parsers. In the old tool there was just the notion of a parser, which purpose
it was to parse a single file/artifact. However Plaso introduces both plugins
and parsers, and there is a distinction between the two. The parser understands
and parses file formats whereas a plugin understands data inside file formats.
So in the case of the Windows Registry the parser understands the file format
of the registry and parses that, but it's the purpose of a plugin to read the
actual key content and produce meaningful data of it. The same goes with SQLite
databases, the parser understands how to read SQLite databases while the
plugins understand the data in them, an example of a SQLite plugin is the
Chrome History plugin, or the Firefox History plugin. Both are SQLite databases
so the use the same parser, but the data stored in them is different, thus we
need a plugin for that.

To see the list of presets that are available use the `--info` parameter. The
old tool allowed you to indicate which presets you wanted using the `-f`
parameter. In the new version this same functionality is exposed as the
`--parsers` parameter. Example usage of this parameter is:

```bash
log2timeline.py --parsers "win7" --storage-file /cases/timeline/timeline.plaso image.dd
log2timeline.py --parsers "win7,\!winreg" --storage-file /cases/timeline/timeline.plaso image.dd
log2timeline.py --parsers "winreg,winevt,winevtx" --storage-file /cases/timeline/timeline.plaso image.dd
```

There is another difference, the old tool used l2t_csv as the default output,
which could be configured using the `-o` parameter of log2timeline. This output
was all saved in a single file that was unsorted, which meant that a
post-processing tool called l2t_process needed to be run to sort the output and
remove duplicate entries before analysis started (you could however immediately
start to grep the output).

log2timeline.py does not allow you to control the output, there is only one
available output and that is the Plaso storage file. The Plaso storage file
contains additional metadata about the how log2timeline.py was run, information
gathered during pre-processing, warnings about data that could not be parser and
other useful information that could not be stored in the older format.

The downside of the storage format is that you can no longer immediately start
to grep or analyze the output of the tool, now you need to run a second tool to
sort, remove duplicates and change it into a human readable format.

```bash
psort.py -w /cases/timeline/myhost.sorted.csv /cases/timeline/timeline.plaso
```

There is a command line tool psteal.py which runs log2timeline.py and psort.py
in a single invocation.

With the new storage format and the filtering possibilities of psort, many new
things are now available that were not possible in the older version. For
instance the possibility to scope the time windows of the output to few minutes:

```bash
psort.py /cases/timeline/timeline.plaso "date > '2012-10-10 18:24:00' and date < '2012-10-10 22:25:19'"
```

Or to a specific dataset:

```bash
psort.py /cases/timeline/timeline.plaso "date > '2012-10-10 12:00:00' and date < '2012-10-10 23:55:14' and message contains 'evil' and (source is 'LNK' or timestamp_desc iregexp 'st\swr' or filename contains 'mystery')"
```

Or to just present a small time slice based on a particular event of interest:

```bash
psort.py --slice "2012-10-10T12:00:00" /cases/timeline/timeline.plaso
```

More information about event filters can be found [here](Event-filters.md).

The main difference between the old branch and the new one is that now
filtering is a lot more granular, and also very different. It is possible to
filter against every attribute that is stored inside the event. Some types of
events will store certain attributes, while others will not.

```bash
psort.py /cases/timeline/timeline.plaso "username contains 'joe'"
```

Filter like this one above will go through every event and only include those
events that actually have the attribute username set, which may not be nearly
everyone (only those events that can positively attribute an event to a
specific user). And then filter out those events even further by only including
the events that contain the letters "joe" (case insensitive).

The most common usage of the filters will most likely be constrained to the
common fields, like source/source_short, date/timestamp, source_long, message,
filename, timestamp_desc, parser, etc.

For now, the new version does not have some of the capabilities that the older version had, that is to say the:
* Yara rules to filter out content.
* Inclusion/exclusion regular expressions.

These are things that are on the roadmap and should hopefully be added before
too long.

Another new thing that the older version did not have is metadata stored inside
the storage file. Since the older version only used l2t_csv as the output
(default output, configurable) it had no means of storing metadata about the
runtime of the tool nor the events that were collected. That has changed with
the new version. Some of the metadata stored can be used for filtering out data
(or has the potential of being used for that) or at least be printed out again,
since it contains useful information about the collection.

```bash
pinfo.py -v /cases/timeline/timeline.plaso
```

This tool will show metadata information that is stored inside the storage
file, so you can see what is exactly stored inside there. The storage may also
contain additional details, such as; tags for events, analysis reports and
other data.

Another aspect that was not part of the older version is tagging and any other
sort of automatic analysis on the data set. For more information see: [tagging rules](Tagging-Rules.md).

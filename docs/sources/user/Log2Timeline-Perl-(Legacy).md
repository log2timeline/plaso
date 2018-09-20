# Switching from Log2Timeline Perl (Legacy) to plaso

This is a site that should contain information for those that are used to the 0.X branch of log2timeline, also known as Log2Timeline Perl or Log2Timeline legacy.

The syntax has changed somewhat from the older version, the largest user facing differences may be:

 * Output of the tool is no longer controllable through the log2timeline front-end (there is only one storage mechanism and that is binary). The user needs to run psort on the output to produce a human-readable content (with l2t_csv as the default output).
 * Raw image files can be parsed **directly**, so mounting the images is no longer required (not encouraged).
 * Parser names have changed (number of new parsers yet some that have not yet been ported).
 * Parameters have changed considerably and options are different, **so please read this page**.
 * The post-processing tool is no longer called l2t_process, it is now named **psort**.
 * The name plaso can come up in the discussion, that is the name of the new backend (as an opposed to Log2Timeline which is the old Perl backend). Hence plaso refers to the backend, log2timeline to the CLI based front-end of the tool. There are other front-ends to the tool though, for instance [timesketch](http://www.timesketch.org/) and [4n6time](http://forensicswiki.org/wiki/4n6time).


Let's go over the old and new method of collecting a timeline from a simple image file.

## Old method

First of all we needed to mount the image. Something like this:

    sudo mount -t ntfs-3g -o ro,nodev,noexec,show_sys_files,streams_interface=windows,loop,offset=32256 image.dd /mnt/nfts

Then we needed to run log2timeline against the mount point. You needed to define the timezone of the suspect image, which could get overwritten if a correct value was found and you needed to define which parsers to use. The sample run is:

    cd /mnt/ntfs
    log2timeline -r -p -z CST6CDT -f win7 . > /cases/timeline/myhost.csv 2> /cases/timeline/myhost.log

This would pick all the parsers defined in the "win7" list and run those against every file found in the mount point. A list of all available parsers and lists could be produced by running:

    log2timeline -f list

As noted earlier, the above approach would produce a large "kitchen-sink" approach timeline that is not sorted. To sort that one (no filtering):

    cd /cases/timeline
    l2t_process.py -b myhost.csv > myhost.sorted.csv

Now we would have a large sorted CSV file ready to analyze.

Limiting the output to a specific date could be achieved using methods like:

    l2t_process.py -b myhost.csv 10-10-2012..10-11-2012

However, you could not limit the output of the timeline to a more narrow timeframe than a single day, for that you needed grep (or some other tools of choice).

    l2t_process.py -b myhost.csv 10-10-2012..10-11-2012 | grep ",1[8-9]:[0-5][0-9]:[0-9][0-9],"

And filtering based on content was constrained to few options:
 * Use a keyword file that contained case-insensitive potentially regular expressions and supply that as a white- or blacklist.
 * Use a YARA rule that matched against the description_long field.
 * Use grep/sed/awk.

The problem with most of the l2t_process filtering is that it was either done on the whole line or against the description_long field. There was no easy way to filter against a more specific attribute of the event.

## New method

Since the new version works directly on a raw image file there is no need to mount the image first (and mounting them is actually highly discouraged), the timeline can be created in a single step:

    log2timeline.py /cases/timeline/myhost.plaso image.dd

The tool will detect whether or not the input is a file, directory or a disk image/partition. If the tool requires additional information, such as when VSS stores are detected or more than a single partition in the volume the tool will ask for additional details. An example of that:

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

The options can also be supplied on the command line, `-o 63` for sector offset into the disk image, or `--vss_stores '1,2'` for defining the VSS stores to parse, or `--no-vss` or `-vss-stores all` for processing all VSS stores.

This can also be achieved without knowing the offset into the disk image.

    log2timeline.py --partition 2 /cases/timeline/myhost.dump image.dd

First of all there is quite a difference in the number of parameters, let's go slightly over them:

 * There is no `-r` for recursive, when the tool is run against an image or a directory recursive is automatically assumed, run it against a single file and it recursion is not turned on.
 * There is no need to supply the tool with the `-p` (preprocessing) when run against an image, that is automatically turned on.
 * The `-z CST6CDT` is not used here. The tool does automatically pick up the timezone and use that. However in the case the timezone is not identified the option is still possible and in fact if not provided uses UTC as the timezone.
 * You may have noticed there is no `-f list` parameter used. The notion of selecting filters is now removed and is done automatically. The way the tool now works is that it tries to "guess" the OS and select the appropriate parsers based on that selection. The categories that are available can  be found here or by issuing `log2timeline.py --info`. If you want to overwrite the automatic selection of parsers you can define them using the `--parsers` parameter.
 * You have to supply the tool with the parameter to define where to save the output (can no longer just output to STDOUT and pipe it to a file).

The equivalent call of the old tool of `-f list` can now be found using `--info`. That will print out all available parsers and plugins in the tool. One thing to take note of is the different concepts of either plugins or parsers. In the old tool there was just the notion of a parser, which purpose it was to parse a single file/artifact. However plaso introduces both plugins and parsers, and there is a distinction between the two. The parser understands and parses file formats whereas a plugin understands data inside file formats. So in the case of the Windows Registry the parser understands the file format of the registry and parses that, but it's the purpose of a plugin to read the actual key content and produce meaningful data of it. The same goes with SQLite databases, the parser understands how to read SQLite databases while the plugins understand the data in them, an example of a SQLite plugin is the Chrome History plugin, or the Firefox History plugin. Both are SQLite databases so the use the same parser, but the data stored in them is different, thus we need a plugin for that.

To see the list of presets that are available use the `--info parameter`. The old tool allowed you to indicate which presets you wanted using the `-f` parameter. In the new version this same functionality is exposed as the `--parsers` parameter. The difference now is that now you can supply globs or patterns to match parser names (since they are longer than in the previous version). Example usage of this parameter is:

    log2timeline.py --parsers "win7" /cases/timeline/myhost.dump image.dd
    log2timeline.py --parsers "win7,-winreg" /cases/timeline/myhost.dump image.dd
    log2timeline.py --parsers "winreg,winevt,winevtx" /cases/timeline/myhost.dump image.dd

There is another difference, the old tool used l2t_csv as the default output, which could be configured using the `-o` parameter of log2timeline. This output was all saved in a single file that was unsorted, which meant that a post-processing tool called l2t_process needed to be run to sort the output and remove duplicate entries before analysis started (you could however immediately start to grep the output).

The new version does not allow you to control the output (ATM, that support will be added into future versions), there is only one available output and that is the plaso storage file. That output is a ZIP container that stores binary files that represent each event. This has many benefits over the older format, since first of all the data is compressed, saving disk space, and it can store metadata about the runtime of the tool, information gathered during the parsing and other useful information that could not be stored in the older format. The data is also stored semi sorted (several smaller sorted files), which makes sorting easier (and less strenuous on memory), and finally the data is stored in a more structured format making filtering considerably easier and more flexible.

The downside of the storage format is that you can no longer immediately start to grep or analyze the output of the tool, now you need to run a second tool to sort, remove duplicates and change it into a human readable format.

   psort.py -w /cases/timeline/myhost.sorted.csv /cases/timeline/myhost.dump

However, with the new storage format and the filtering possibilities of psort, many new things are now available that were not possible in the older version. For instance the possibility to narrow down the window of output to few minutes:

    psort.py /cases/timeline/myhost.dump "date > '2012-10-10 18:24:00' and date < '2012-10-10 22:25:19'"

Or to a specific dataset:

    psort.py /cases/timeline/myhost.dump "date > '2012-10-10 12:00:00' and date < '2012-10-10 23:55:14' and message contains 'evil' and (source is 'LNK' or timestamp_desc iregexp 'st\swr' or filename contains 'mystery')"

Or to just present a small time slice based on a particular event of interest:

    psort.py --slice "2012-10-10 12:00:00" /cases/timeline/myhost.dump

More on the usage of filters [here](http://plaso.kiddaland.net/usage/filters).

The main difference between the old branch and the new one is that now filtering is a lot more granular, and also very different. It is possible to filter against every attribute that is stored inside the event. Some types of events will store certain attributes, while others will not.

    psort.py /cases/timeline/myhost.dump "username contains 'joe'"

Filter like this one above will go through every event and only include those events that actually have the attribute username set, which may not be nearly everyone (only those events that can positively attribute an event to a specific user). And then filter out those events even further by only including the events that contain the letters "joe" (case insensitive).

The most common usage of the filters will most likely be constrained to the common fields, like source/source_short, date/timestamp, source_long, message, filename, timestamp_desc, parser, etc.

For now, the new version does not have some of the capabilities that the older version had, that is to say the:
 * Yara rules to filter out content.
 * White/black lists.

These are things that are on the roadmap and should hopefully be added before too long.

Another new thing that the older version did not have is metadata stored inside the storage file. Since the older version only used l2t_csv as the output (default output, configurable) it had no means of storing metadata about the runtime of the tool nor the events that were collected. That has changed with the new version. Some of the metadata stored can be used for filtering out data (or has the potential of being used for that) or at least be printed out again, since it contains useful information about the collection.

 * pinfo.py -v /cases/timeline/myhost.dump

This tool will dump out all the metadata information that is stored inside the storage file, so you can see what is exactly stored inside there. The storage may also contain additional details, such as; tags for events, analysis reports and other data.

Another aspect that was not part of the older version is tagging and any other sort of automatic analysis on the data set.

**TODO: describe tagging**
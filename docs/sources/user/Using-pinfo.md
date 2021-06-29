# Using pinfo.py

**pinfo** is a command line tool to provide information about the contents of a Plaso storage file.

The Plaso storage file contains information about:

 + When and how the tool was run
 + Information gathered during the pre-processing stage
 + Metadata about each storage container or store
 + What parsers were used during the extraction phase, parameters used
 + How many extracted events are in the storage file, and count of each parser
 + If there are tagged events, what tag file was used, what tags have been applied and count for each one
 + If analysis plugins have been run, an overview of which have been run and the content of the report

## Usage

Usage of **pinfo** is very simple, however for full list of parameters use the ``-h`` or ``--help`` switch.

The simplest way to run the tool is to run it without any parameters:

```bash
$ pinfo.py timeline.plaso

--------------------------------------------------------------------------------
                Plaso Storage Information
--------------------------------------------------------------------------------
Storage file:           timeline.plaso
Serialization format:   json
Source processed:       N/A
Time of processing:     2015-07-16T20:39:40+00:00

Collection information:
        parser_selection = winxp
        recursive = False
        preferred_encoding = UTF-8
        os_detected = Windows
        workers = 0
        output_file = timeline.plaso
        method = imaged processed
        preprocess = True
        version = 1.3.0
        cmd_line = /usr/bin/log2timeline.py timeline.plaso test.dd
        debug = False
        runtime = multi process mode
        parsers = bencode, binary_cookies, chrome_cache, chrome_preferences, esedb, filestat, firefox_cache, java_idx, lnk, mcafee_protection, msiecf, olecf, openxml, opera_global, opera_typed_history, pe, plist, prefetch, recycle_bin_info2, skydrive_log, skydrive_log_error, sqlite, symantec_scanlog, winevt, winfirewall, winjob, winreg
        configured_zone = CST6CDT
        protobuf_size = 0

Parser counter information:
        Counter: total = 149925
        Counter: winreg/winreg_default = 87885
        Counter: filestat = 28894
        Counter: pe = 26161
        Counter: msiecf = 3156
        Counter: lnk/shell_items = 1361
        Counter: winreg/windows_services = 831
        Counter: lnk = 483
        Counter: winevt = 364
...
```

This produces the basic information the storage file stores. To get more verbose output, for instance to see the information collected during the pre-processing stage or content of analysis reports use the verbose switch, ``-v``

```bash
$ pinfo.py -v timeline.plaso
...
Preprocessing information:
        Operating system        : Microsoft Windows XP
        Hostname                : N-1A9ODN6ZXK4LQ
        Time zone               : CST6CDT
        %ProgramFiles%          : Program Files
        %SystemRoot%            : /WINDOWS
        %WinDir%                : /WINDOWS
    Users information:
        Name                    : systemprofile
        SID                     : S-1-5-18
        Profile path            : %systemroot%\system32\config\systemprofile
        Name                    : LocalService
        SID                     : S-1-5-19
        Profile path            : %SystemDrive%\Documents and Settings\LocalService
        Name                    : NetworkService
        SID                     : S-1-5-20
        Profile path            : %SystemDrive%\Documents and Settings\NetworkService
        Name                    : Mr. Evil
        SID                     : S-1-5-21-2000478354-688789844-1708537768-1003
        Profile path            : %SystemDrive%\Documents and Settings\Mr. Evil
    Other:
        Time zone               : CST6CDT
        Operating system        : Windows
        Registry path           : /WINDOWS/system32/config
        store_range             : (1, 1)
        Code page               : cp1252

-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
...
```

If analysis plugins have been run the reports are also displayed:

```bash
Report generated from: browser_search
Generated on: 2015-07-17T02:52:07+00:00

Report text:
 == ENGINE: GoogleSearch ==
10 who am i
10 what is my ip
```

Same if there are any tags stored in the storage file.

```bash
Parser counter information:
        Counter: Total Tags = 146
        Counter: Application Execution = 144
        Counter: Document Printed = 2
```

There is also an option to compare two storage files, for instance if you run
the tool against a storage media file, then later re-run the tool and you want
to quickly determine if there is a difference between the two storage files
(does not go into content, only counters).

```bash
$ pinfo.py --compare older_timeline.plaso timeline.plaso

collection_information.version value mismatch 1.3.0_20150716 != 1.3.0_20150713.
counter.filestat value mismatch 49090 != 28894.
counter.total value mismatch 143960 != 123764.
```

This shows the comparison between two runtimes of the tool against the same
test dataset, before a bug was fixed and after. There are two things that
changed, the version number increased and there are a lot more filestat events
in the newer storage file.

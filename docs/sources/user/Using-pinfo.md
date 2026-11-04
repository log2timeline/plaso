# Using pinfo.py

**pinfo** is a command line tool to provide information about the contents of a
Plaso storage file.

The Plaso storage file contains information about:

 + When and how the tool was run (sessions)
 + The sources that were processed
 + How many events were extracted, per data type and per parser (plugin)
 + Which event tags were applied and how many per label
 + Which warnings were generated during extraction, preprocessing, recovery
   and timelining
 + Which analysis plugins were run and the results of their reports

## Usage

For the full list of parameters use the ``-h`` or ``--help`` switch.

The simplest way to run the tool is to pass it only the storage file:

```bash
$ pinfo.py timeline.plaso
************************** Plaso Storage Information ***************************
            Filename : timeline.plaso
      Format version : 20260516
Serialization format : json
--------------------------------------------------------------------------------

*********************************** Sessions ***********************************
bf263ca6-f352-4480-b06b-d5849ba95d17 : 2026-07-02T17:48:14.943433+00:00
--------------------------------------------------------------------------------

******************************** Event sources *********************************
Total : 2
--------------------------------------------------------------------------------

************************ Events generated per data type ************************
Data type name : Number of events
--------------------------------------------------------------------------------
       fs:stat : 3
         Total : 3
--------------------------------------------------------------------------------

************************* Events generated per parser **************************
Parser (plugin) name : Number of events
--------------------------------------------------------------------------------
            filestat : 3
               Total : 3
--------------------------------------------------------------------------------

No events labels stored.

No warnings stored.

No analysis reports stored.
```

The sessions table lists the identifier and start time of every session, for
example one per log2timeline or psort run that wrote to the storage file.

If the storage file contains event tags, warnings or analysis reports, these
are shown as well:

```bash
$ pinfo.py timeline.plaso
...
************************ Event tags generated per label ************************
   Label : Number of event tags
--------------------------------------------------------------------------------
   exit1 : 2
   exit2 : 2
repeated : 4
   Total : 8
--------------------------------------------------------------------------------

******************* Extraction warnings generated per parser *******************
   Parser (plugin) name : Number of warnings
--------------------------------------------------------------------------------
text/syslog_traditional : 2
--------------------------------------------------------------------------------

************** Path specifications with most extraction warnings ***************
Number of warnings : Pathspec
--------------------------------------------------------------------------------
                 2 : type: OS, location: /tmp/test/test_data/syslog/syslog
--------------------------------------------------------------------------------

****************************** Analysis report: 0 ******************************
  Name plugin : tagging
Date and time : 2026-07-02T17:48:02.000000+00:00
 Event filter : N/A
      Results : 
   event_tags : 4
        exit1 : 2
     repeated : 2
--------------------------------------------------------------------------------
...
```

### Verbose output

To get more detailed output use the verbose switch, ``-v``. In verbose mode
pinfo prints a block per session, with for example the command line, the
enabled parsers and plugins and the preferred time zone, every event source
and the details of every warning:

```bash
$ pinfo.py -v timeline.plaso
...
**************** Session: bf263ca6-f352-4480-b06b-d5849ba95d17 *****************
                Start time : 2026-07-02T17:48:14.943433+00:00
           Completion time : 2026-07-02T17:48:25.359960+00:00
              Product name : plaso
           Product version : 20260702
    Command line arguments : ./plaso/scripts/log2timeline.py --partition=all
                             --quiet --storage-file pinfo_test.plaso
                             test_data/tsk_volume_system.raw
  Parser filter expression : N/A
Enabled parser and plugins : android_app_usage, asl_log, bencode,
                             ...
                             winreg/winrar_mru, winreg/winreg_default
        Preferred encoding : UTF-8
       Preferred time zone : UTC
                Debug mode : False
          Artifact filters : N/A
               Filter file : N/A
--------------------------------------------------------------------------------

******************************** Event sources *********************************
0 : type: OS, location: /tmp/test/test_data/tsk_volume_system.raw
  : type: RAW
  : type: TSK_PARTITION, location: /p5, part index: 6, start offset: 0x0002c000
  : type: EXT, location: /
1 : type: OS, location: /tmp/test/test_data/tsk_volume_system.raw
  : type: RAW
  : type: TSK_PARTITION, location: /p5, part index: 6, start offset: 0x0002c000
  : type: EXT, inode: 11, location: /lost+found
--------------------------------------------------------------------------------
...
```

### Selecting sections

By default pinfo shows all sections. Use ``--sections`` with a comma separated
list of section names to show only some of them. The storage information table
at the top is always shown. ``--sections list`` lists the available sections:

```bash
$ pinfo.py --sections list
*********************************** Sections ***********************************
    Name : Description
--------------------------------------------------------------------------------
  events : Show information about events.
 reports : Show information about analysis reports.
sessions : Show information about sessions.
 sources : Show information about event sources.
warnings : Show information about warnings during processing.
--------------------------------------------------------------------------------
```

The events section includes the event tags per label. When the warnings
section is selected explicitly, the details of every warning are shown, as with
``-v``:

```bash
$ pinfo.py --sections events,warnings timeline.plaso
************************** Plaso Storage Information ***************************
            Filename : timeline.plaso
      Format version : 20260516
Serialization format : json
--------------------------------------------------------------------------------

************************ Events generated per data type ************************
      Data type name : Number of events
--------------------------------------------------------------------------------
             fs:stat : 6
syslog:cron:task_run : 6
         syslog:line : 26
               Total : 38
--------------------------------------------------------------------------------
...
**************************** Extraction warning: 0 *****************************
           Message : unable to parse record: log_line with error: Unable to
                     parse time elements with error: Invalid month: None
      Parser chain : text/syslog_traditional
Path specification : type: OS, location: /tmp/test/test_data/syslog/syslog
--------------------------------------------------------------------------------
...
```

### Output formats

Use ``--output_format`` to select the format of the output: ``text`` (the
default), ``markdown`` or ``json``. For example:

```bash
$ pinfo.py --output_format markdown timeline.plaso
# Plaso Storage Information

<table>
<tr><th nowrap style="text-align:left;vertical-align:top">Filename</th><td>timeline.plaso</td></tr>
<tr><th nowrap style="text-align:left;vertical-align:top">Format version</th><td>20260516</td></tr>
<tr><th nowrap style="text-align:left;vertical-align:top">Serialization format</th><td>json</td></tr>
</table>
...
## Events generated per data type

Data type name | Number of events
--- | ---
fs:stat | 3
Total | 3
...
```

The JSON output contains the sessions, the event sources and the storage
counters:

```bash
$ pinfo.py --output_format json timeline.plaso
{"sessions": {"session": {"__type__": "AttributeContainer", "__container_type__": "session", "aborted": false, "command_line_arguments": "./plaso/scripts/log2timeline.py --partition=all --quiet --storage-file pinfo_test.plaso test_data/tsk_volume_system.raw", ...}}, "event_sources": {...}, "storage_counters": {"data_types": {"fs:stat": 3, "total": 3}, "parsers": {"filestat": 3, "total": 3}, "event_labels": {}, "warnings_by_parser": {}, "warnings_by_path_spec": {}, "analysis_reports": {}}}
```

The output format also applies to the reports described below.

### Writing the output to a file

Use ``-w`` or ``--write`` to write the output to a file instead of stdout. The
output file must not exist yet:

```bash
$ pinfo.py --output_format json -w timeline.json timeline.plaso
```

### Reports

Use ``--report`` to generate a report on specific information in the storage
file instead of the overview. ``--report list`` lists the available reports:

```bash
$ pinfo.py --report list
*********************************** Reports ************************************
                 Name : Description
--------------------------------------------------------------------------------
       browser_search : Report browser searches determined by the
                        browser_search analysis plugin.
     chrome_extension : Report Chrome extensions determined by the
                        chrome_extension analysis plugin.
environment_variables : Report environment variables extracted during
                        processing.
          file_hashes : Report file hashes calculated during processing.
     windows_services : Report Windows services and drivers extracted during
                        processing.
     winevt_providers : Report Windows EventLog providers extracted during
                        processing.
--------------------------------------------------------------------------------
```

The browser_search and chrome_extension reports need the results of the
corresponding psort analysis plugin. The other reports use information that
log2timeline stored during extraction. A report that has no matching
information in the storage file only shows the column names. In the text
output format the columns are separated by tabs.

For example, the Windows services and drivers found in the SYSTEM Registry
file:

```bash
$ pinfo.py --report windows_services timeline.plaso
Name	Service type	Start type	Image path
1394ohci	Kernel device driver (0x01)	On demand (3)	\SystemRoot\system32\drivers\1394ohci.sys
ACPI	Kernel device driver (0x01)	Boot (0)	system32\drivers\ACPI.sys
AcpiPmi	Kernel device driver (0x01)	On demand (3)	\SystemRoot\system32\drivers\acpipmi.sys
AdobeARMservice	Stand-alone service (0x10)	Automatic (2)	"C:\Program Files\Common Files\Adobe\ARM\1.0\armsvc.exe"
...
```

The Windows EventLog providers found in the Registry:

```bash
$ pinfo.py --report winevt_providers timeline.plaso
Identifier	Log source(s)	Log type(s)	Event message file(s)	Parameter message file(s)
{0063715b-eeda-4007-9429-ad526f62696e}	['microsoft-windows-services']	[]	['%SystemRoot%\\system32\\services.exe']	[]
{01090065-b467-4503-9b28-533766761087}	['microsoft-windows-parentalcontrols']	[]	['%SystemRoot%\\system32\\wpc.dll']	[]
...
```

The file_hashes report lists the hash and display name of every event data
stream. Use ``--hash`` to select the hash type: ``md5``, ``sha1`` or ``sha256``
(the default). The hash must have been calculated during extraction, see the
``--hashers`` option of log2timeline, otherwise it is shown as "N/A".

```bash
$ pinfo.py --report file_hashes timeline.plaso
SHA256 hash	Display name
1f0105612f6ad2d225d6bd9ba631148740e312598878adcd2b74098a3dab50c4	OS:/tmp/test/test_data/syslog/syslog
1f0105612f6ad2d225d6bd9ba631148740e312598878adcd2b74098a3dab50c4	OS:/tmp/test/test_data/syslog/syslog
```

```bash
$ pinfo.py --report file_hashes --hash md5 --output_format markdown timeline.plaso
MD5 hash | Display name
--- | ---
N/A | OS:/tmp/test/test_data/syslog/syslog
N/A | OS:/tmp/test/test_data/syslog/syslog
```

### Comparing storage files

The ``--compare`` option compares the counters of two storage files, for
example to determine if a re-run of log2timeline against the same source
produced different results. It compares the number of events per data type and
per parser, the number of event tags per label and the number of extraction and
recovery warnings, not the events themselves.

For every counter that differs, pinfo shows the value of the storage file
passed as argument, followed by the value of the storage file passed to
``--compare`` in parentheses:

```bash
$ pinfo.py --compare older_timeline.plaso timeline.plaso
************************ Events generated per data type ************************
      Data type name : Number of events
--------------------------------------------------------------------------------
             fs:stat : 6 (3)
syslog:cron:task_run : 6 (0)
         syslog:line : 26 (0)
               total : 38 (3)
--------------------------------------------------------------------------------


************************* Events generated per parser **************************
Parser (plugin) name : Number of events
--------------------------------------------------------------------------------
            filestat : 6 (3)
  syslog_traditional : 32 (0)
               total : 38 (3)
--------------------------------------------------------------------------------

...
Storage files are different.
```

Here timeline.plaso contains 6 fs:stat events and older_timeline.plaso 3. When
the counters are identical pinfo prints "Storage files are identical.". The
exit code is 0 if the storage files are identical and 1 otherwise.

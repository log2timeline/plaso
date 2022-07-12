# Using log2timeline.py

**log2timeline** is a command line tool to extract
[events](Scribbles-about-events.md#what-is-an-event) from individual files,
recursing a directory, for example a mount point, or storage media image or
device. log2timeline creates a plaso storage file which can be analyzed with
the pinfo and psort tools.

The Plaso storage file contains the extracted events and various metadata about
the collection process alongside information collected from the source data. It
may also contain information about tags applied to events and reports from
analysis plugins.

To get a complete list of all switches and parameters of log2timeline.py, use
``-h`` or ``--help``.

This guide will cover the most basic options and then discuss some of the
perhaps less used ones.

## Basic usage

The simplest way, and perhaps the most common way to run log2timeline.py without
any additional parameters, only defining the output and input. The output is
the path and filename of the storage file while the input is the location of
the source, whether that is a single file, a storage media image or a directory
such as a mount point. log2timeline.py will go through the entire data set and
produce a "*kitchen sink*" timeline, containing information extracted from all
discovered files.

```bash
$ log2timeline.py --storage-file OUTPUT INPUT
```

For example:

```bash
$ log2timeline.py --storage-file timeline.plaso /PATH/image.E01
2021-05-09 10:15:19,162 [INFO] (MainProcess) PID:3143504 <artifact_definitions> Determined artifact definitions path: /usr/share/artifacts/
Checking availability and versions of dependencies.
[OK]


Source path		: /PATH/image.E01
Source type		: storage media image
Processing time		: 00:00:00

Processing started.
```

```bash
plaso - log2timeline version 20210412

Source path		: /PATH/image.E01
Source type		: storage media image
Processing time		: 00:04:57

Tasks:          Queued  Processing      Merging         Abandoned       Total
                0       0               0               0               18675

Identifier      PID     Status          Memory          Sources         Events          File
Main            3143050 completed       1.3 GiB         18675 (0)       499347 (0)
Worker_00       3143054 idle            1.2 GiB         3275 (0)        101555 (0)      NTFS:\WINDOWS\$NtServicePackUninstall$
Worker_01       3143056 idle            1.2 GiB         4246 (0)        42476 (0)       NTFS:\WINDOWS\ie7
Worker_02       3143058 idle            1.2 GiB         675 (0)         63234 (0)       NTFS:\WINDOWS\inf
Worker_03       3143060 idle            1.2 GiB         350 (0)         57190 (0)       NTFS:\pagefile.sys
Worker_04       3143064 idle            1.2 GiB         3876 (0)        103856 (0)      NTFS:\hiberfil.sys
Worker_05       3143068 idle            1.2 GiB         1985 (0)        64947 (0)       NTFS:\WINDOWS\security
Worker_06       3143072 idle            1.2 GiB         4267 (0)        66089 (0)       NTFS:\WINDOWS\ServicePackFiles

Processing completed.
```

The status window includes information, such as:

* how many workers were started up;
* what the process identifier (PID) fo the worker processes is;
* how many events in total and each one of the workers has extracted;
* what the last was a worker was extracting events from.

The input in the previous example was a storage media image with a single
partition, which was running a Windows XP system on it. The first thing the
log2timeline.py does is to scan the storage media file, if it discovers more
than a single partition, an encrypted partition or that the partition contains
Volume Shadow Copies (VSS) it will ask the user for further details, for
example:

```bash
$ log2timeline.py --storage-file timeline.plaso bde_enabled_windows.dd

The following partitions were found:
Identifier      Offset (in bytes)       Size (in bytes)
p1              1048576 (0x00100000)    350.0MiB / 367.0MB (367001600 B)
p2              368050176 (0x15f00000)  148.7GiB / 159.7GB (159671910400 B)

Please specify the identifier of the partition that should be processed.
All partitions can be defined as: "all". Note that you can abort with Ctrl^C.
p2
Found a BitLocker encrypted volume.
Supported credentials:

  0. startup_key
  1. recovery_password
  2. password
  3. skip

Note that you can abort with Ctrl^C.

Select a credential to unlock the volume:
```

Note that there are various options that can be used to prevent
log2timeline.py from prompting the user to select VSS stores or
partitions.

 + **--partitions PARTITION_NUMBERS**: Preselects the partition number to use, eg: ```---partitions 2``` will pick the second partition on the disk.
 + **--vss_stores**: Selects the VSS stores to include, eg: ```---vss_stores all``` will select all available VSS stores, or ```--vss_stores 1,4,5``` (only first, fourth and fifth), or ```--vss_stores 1..3``` (first three stores) or ```--vss_stores=none``` will ignore available VSS stores.
 + **--unattended**: log2timeline.py will error instead of prompting the user.

After finding a partition to process log2timeline.py will start the
pre-processing stage, where it collects information from the storage media.
That is evident by the entries like:

```bash
2015-07-16 16:54:05,368 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: hostname to N-1A9ODN6ZXK4LQ
```

Here log2timeline.py detected that the hostname from the Windows installation
in this partition is: **N-1A9ODN6ZXK4LQ**.

After that the tool spins up several workers (the actual number differs depends
on number of CPU's on the system running the tool), a collector and a storage
process.

## The info option

The first option is the ``--info`` which prints out information about all
supported plugins, parsers, output modules, etc.

```bash
$ log2timeline.py --info
======================== log2timeline/plaso information ========================

******************************** Parser Presets ********************************
                  android : android_app_usage, android_calls, android_sms
                    linux : bencode, filestat, google_drive, java_idx, olecf,
                            openxml, pls_recall, popularity_contest, selinux,
                            skype, syslog, utmp, webhist, xchatlog,
                            xchatscrollback, zeitgeist
                   macosx : appusage, asl_log, bencode, bsm_log, cups_ipp,
                            filestat, google_drive, java_idx, ls_quarantine,
                            mac_appfirewall_log, mac_document_versions,
                            mac_keychain, mac_securityd, mackeeper_cache,
                            macwifi, olecf, openxml, plist, skype, utmpx,
                            webhist
...
```

## The logfile option

Another useful option to use is the ```--logfile```. This will redirect all log
messages from log2timeline.py to a file. This can be coupled with ```-d``` if
you wish to get more detailed debug information.

```bash
$ log2timeline.py --logfile test.log --storage-file timeline.plaso test.vhd
```

Note that the foreman (main process) and each worker will have a separate log
file. If th .log.gz extension is used log2timeline.py will create a compressed
log file.

## Using filter files for triage

Sometimes you may not want to do a complete timeline that extracts events from
every discovered file. To do more targeted extraction a filter file can be used.

```bash
$ log2timeline.py -f filter --storage-file timeline.plaso test.vhd

Source path	: /PATH/test.vhd
Source type	: storage media image
Filter file	: filter

Processing started.
...
Processing completed.
```

Instead of processing all the files only the file paths included in the filter
file will be used. Here the content is:

```bash
$ cat filter
{sysregistry}/.+
/Users/.+/NTUSER.DAT
/Documents And Settings/.+/NTUSER.DAT
```

This can be verified against the event sources:

```bash
$ pinfo.py --sections sources timeline.plaso
```

More information about the collection filters can be found [here](Collection-Filters.md).

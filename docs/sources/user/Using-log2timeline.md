# Using log2timeline.py

**This page is still a work in progress and will most likely change significantly**

# Usage

**log2timeline** is a command line tool to extract [events](Scribbles-about-events.md#what-is-an-event) from individual files, recursing a directory (e.g. mount point) or storage media image or device. log2timeline creates a plaso storage file which can be analyzed with the pinfo and psort tools.

The plaso storage file contains the extracted events and various metadata about the collection process alongside information collected from the source data. It may also contain information about tags applied to events and reports from analysis plugins.

# Running the tool

To get a complete list of all switches and parameters to the tool, use ``-h`` or ``--help``.

This guide will cover the most basic options and then discuss some of the perhaps less used ones.

The first option is the ``--info`` which prints out information about all supported plugins, parsers, output modules, etc.

```
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

The simplest way, and perhaps the most common way to run the tool is without any additional parameters, only defining the output and input. The output is the path and filename of the storage file while the input is the location of the source, whether that is a single file, storage media, device or a mount point. The tool will go through the entire data set and produce a "*kitchen sink*" timeline, containing information extracted from all discovered files.

```
$ log2timeline.py OUTPUT INPUT
```

An example run:
```
$ log2timeline.py test.plaso test.vhd

Source path	: /PATH/test.vhd
Source type	: storage media image

Processing started.
2015-07-16 16:53:58,808 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: sysregistry to /WINDOWS/system32/config
2015-07-16 16:53:58,820 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: systemroot to /WINDOWS
2015-07-16 16:53:58,834 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: windir to /WINDOWS
2015-07-16 16:53:59,937 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: users to [{u'path': u'%systemroot%\\system32\\config\\systemprofile', u'name': u'systemprofile', u'sid': u'S-1-5-18'}, {u'path': u'%SystemDrive%\\Documents and Settings\\LocalService', u'name': u'LocalService', u'sid': u'S-1-5-19'}, {u'path': u'%SystemDrive%\\Documents and Settings\\NetworkService', u'name': u'NetworkService', u'sid': u'S-1-5-20'}, {u'path': u'%SystemDrive%\\Documents and Settings\\Mr. Evil', u'name': u'Mr. Evil', u'sid': u'S-1-5-21-2000478354-688789844-1708537768-1003'}]
2015-07-16 16:54:01,038 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: programfiles to Program Files
2015-07-16 16:54:02,128 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: programfilesx86 to None
2015-07-16 16:54:03,300 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: osversion to Microsoft Windows XP
2015-07-16 16:54:04,311 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: code_page to cp1252
2015-07-16 16:54:05,368 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: hostname to N-1A9ODN6ZXK4LQ
2015-07-16 16:54:06,436 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: time_zone_str to CST6CDT
2015-07-16 16:54:06,437 [INFO] (MainProcess) PID:98252 <extraction_frontend> Parser filter expression changed to: winxp
2015-07-16 16:54:06,437 [INFO] (MainProcess) PID:98252 <extraction_frontend> Setting timezone to: CST6CDT
Worker_00 (PID: 98257) - events extracted: 596 - file: TSK:/Documents and Settings/All Users/Start Menu/Programs/Look@LAN/Look@LAN on the WEB.lnk - running: True <running>
Worker_01 (PID: 98258) - events extracted: 422 - file: TSK:/Documents and Settings/All Users/Start Menu/Programs/Look@LAN/License.lnk - running: True <running>
Worker_02 (PID: 98259) - events extracted: 4 - file: TSK:/hiberfil.sys - running: True <running>
...
Worker_03 (PID: 98273) - events extracted: 14169 - file: TSK:/WINDOWS/Installer/{350C97B0-3D7C-4EE8-BAA9-00BCB3D54227}/places.exe - running: True <running>
Worker_04 (PID: 98274) - events extracted: 20672 - file: TSK:/$RECYCLE.BIN/S-1-5-21-4281732234-1149440973-2434181300-1000/desktop.ini - running: True <running>
Worker_05 (PID: 98275) - events extracted: 12500 - file: TSK:/$Extend/$RmMetadata/$TxfLog/$TxfLogContainer00000000000000000002 - running: True <running>
All extraction workers completed - waiting for storage.
Processing completed.
```

The input here was a storage media file that had a single partition on it, which was running a Windows XP system on it. The first thing the tool does is to scan the storage media file, if it discovers more than a single partition, an encrypted partition or that the partition contains Volume Shadow Copies (VSS) it will ask the user for further details, eg:

```
$ log2timeline.py bde_windows.plaso bde_enabled_windows.dd

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

After finding a partition to process the tool will start the pre-processing stage, where it collects information from the storage media. That is evident by the entries like:

```
2015-07-16 16:54:05,368 [INFO] (MainProcess) PID:98252 <interface> [PreProcess] Set attribute: hostname to N-1A9ODN6ZXK4LQ
```

Here the tool detected that the hostname from this partition is: **N-1A9ODN6ZXK4LQ**.

After that the tool spins up several workers (the actual number differs depends on number of CPU's on the system running the tool), a collector and a storage process.

For a better overview of what the tool is doing, please use the ```--status_view``` parameter (warning the window status view does not work very well on Windows).

```
$ log2timeline.py --status_view window test.plaso test.vhd
```

This makes it easier to keep track on what the tool is doing at any point in time.

```
plaso - log2timeline version 1.3.0

Source path	: /PATH/test.vhd
Source type	: storage media image

Identifier	PID	Status		Events		File
Collector	98490	running
Worker_00	98484	running		1280 (108)	GZIP:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/HYU1BON0/results[1].aspx
Worker_01	98485	running		3069 (24)	TSK:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/HYU1BON0/google[1]
Worker_02	98486	running		1040 (160)	TSK:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/HYU1BON0/gray[1].gif
Worker_03	98487	running		2175 (8)	GZIP:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/HYU1BON0/login[1].first=1
Worker_04	98488	running		842 (148)	GZIP:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/HYU1BON0/downloadget[1].php
Worker_05	98489	running		1034 (4)	GZIP:/Documents and Settings/Mr. Evil/Local Settings/Temporary Internet Files/Content.IE5/HYU1BON0/CAJIGZ3H.com%2F
StorageWriter	98483	running		7646 (3063)
```

The status window includes information on how many workers were started up, what their PID is, how many total events each one of them has extracted (within the parenthesis) and what was the last file they were working on extracting events from.

Another useful option to use is the ```--logfile```. This will redirect all log messages from the tool to a file. This can be coupled with ```-d``` if you wish to get more detailed debug data.

```
$ log2timeline.py --status_view window --logfile test.log test.plaso test.vhd
```

This combines storing all log entries to a file for easier viewing later and having the status window displaying the current status of the tool. The benefits of this is the ability to both having a better overview of what the tool is doing at any point in time as well as being able to easily review after the run if the tool encountered any errors. That can be very useful in determining if the tool failed to process an important artifact for instance.

There are also few options that can be used to prevent the tool from prompting the user to select VSS stores or partitions.

 + **--partitions PARTITION_NUMBERS**: Preselects the partition number to use, eg: ```---partitions 2``` will pick the second partition on the disk.
 + **--vss_stores**: Selects the VSS stores to include, eg: ```---vss_stores all``` will select all available VSS stores, or ```--vss_stores 1,4,5``` (only first, fourth and fifth), or ```--vss_stores 1..3``` (first three stores).
 + **--no_vss**: Skip all VSS parsing

## Triage

Sometimes you may not want to do a complete timeline that extracts events from every discovered file. To do a more targeted timelining the ```-f FILTER_FILE``` parameter can be used.

```
$ log2timeline.py -f filter test.plaso test.vhd

Source path	: /PATH/test.vhd
Source type	: storage media image
Filter file	: filter

Processing started.
...
All extraction workers completed - waiting for storage.
Processing completed.
```

Instead of processing the entire partition only the file paths included in the filter file will be used. Here the content is:

```
$ cat filter
{sysregistry}/.+
/Users/.+/NTUSER.DAT
/Documents And Settings/.+/NTUSER.DAT
```

This can be verified with:
```
$ psort.py -a -q test.plaso "SELECT filename" | sort -u
/Documents and Settings/Default User/NTUSER.DAT
/Documents and Settings/LocalService/NTUSER.DAT
/Documents and Settings/Mr. Evil/NTUSER.DAT
/Documents and Settings/NetworkService/NTUSER.DAT
/WINDOWS/system32/config/AppEvent.Evt
/WINDOWS/system32/config/SAM
/WINDOWS/system32/config/SAM.LOG
/WINDOWS/system32/config/SECURITY
/WINDOWS/system32/config/SECURITY.LOG
/WINDOWS/system32/config/SecEvent.Evt
/WINDOWS/system32/config/SysEvent.Evt
/WINDOWS/system32/config/TempKey.LOG
/WINDOWS/system32/config/default
/WINDOWS/system32/config/default.LOG
/WINDOWS/system32/config/default.sav
/WINDOWS/system32/config/software
/WINDOWS/system32/config/software.LOG
/WINDOWS/system32/config/software.sav
/WINDOWS/system32/config/system
/WINDOWS/system32/config/system.LOG
/WINDOWS/system32/config/system.sav
/WINDOWS/system32/config/systemprofile
/WINDOWS/system32/config/userdiff
/WINDOWS/system32/config/userdiff.LOG
filename
```

More information about the collection filters can be found [here](Collection-Filters.md)


## Running against more than a single partition

**Everything following this is still not written**

Here we discuss the use of ```--partitions all```

### OTHER OPTIONS TO DISCUSS

Options:

```
-z TIMEZONE
--credential TYPE:DATA
--data

-d
--profile
--profiling_type


--single_process

--workers
```


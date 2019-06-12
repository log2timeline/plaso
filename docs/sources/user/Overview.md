## Plaso Overview

plaso (Plaso Langar Að Safna Öllu) is a Python-based backend engine for the tool log2timeline. 

log2timeline is a tool designed to extract timestamps from various files found on a typical computer system(s) and aggregate them.

The initial purpose of plaso was to have the timestamps in a single place for computer forensic analysis (aka Super Timeline).

However plaso has become a framework that supports:
* adding new parsers or parsing plug-ins;
* adding new analysis plug-ins;
* writing one-off scripts to automate repetitive tasks in computer forensic analysis or equivalent.

And is moving to support:
* adding new general purpose parses/plugins that may not have timestamps associated to them;
* adding more analysis context;
* allowing more targeted approach to the collection/parsing.

### Supported Formats

The information below is based of version 1.5.0

#### Storage Media Image File Formats

Storage Media Image File Format support is provided by [dfvfs](https://github.com/log2timeline/dfvfs/wiki#storage-media-types).

#### Volume System Formats

Volume System Format support is provided by [dfvfs](https://github.com/log2timeline/dfvfs/wiki#volume-systems).

#### File System Formats

File System Format support is provided by [dfvfs](https://github.com/log2timeline/dfvfs/wiki#file-systems).

#### File formats

* [Apple System Log (ASL)](http://forensicswiki.org/index.php?title=Apple_System_Log_(ASL)&action=edit&redlink=1)
* Android usage-history (app usage)
* [Basic Security Module (BSM)](http://forensicswiki.org/wiki/Basic_Security_Module_(BSM)_file_format)
* Bencode files
* [Chrome Disk Cache Format](http://forensicswiki.org/wiki/Chrome_Disk_Cache_Format)
* Chrome preferences
* CUPS IPP
* [Extensible Storage Engine (ESE) Database File (EDB) format](http://forensicswiki.org/wiki/Extensible_Storage_Engine_(ESE)_Database_File_(EDB)_format) using [libesedb](https://github.com/libyal/libesedb)
* Firefox Cache
* [Java WebStart IDX](http://forensicswiki.org/wiki/Java)
* [Jump Lists](http://forensicswiki.org/wiki/Jump_Lists) .customDestinations-ms files
* MacOS Application firewall
* [MacOS Keychain](https://github.com/libyal/dtformats/blob/master/documentation/MacOS%20keychain%20database%20file%20format.asciidoc)
* MacOS Securityd
* MacOS Wifi
* [mactime logs](http://forensicswiki.org/wiki/Mactime)
* McAfee Anti-Virus Logs
* Microsoft [Internet Explorer History File Format](http://forensicswiki.org/wiki/Internet_Explorer_History_File_Format) (also known as MSIE 4 - 9 Cache Files or index.dat) using [libmsiecf](https://github.com/libyal/libmsiecf)
* Microsoft IIS log files
* NTFS $MFT and $UsnJrnl:$J using [libfsntfs](https://github.com/libyal/libfsntfs)
* [OLE Compound File](http://forensicswiki.org/wiki/OLE_Compound_File) using [libolecf](https://github.com/libyal/libolecf)
* [Opera Browser history](http://forensicswiki.org/wiki/Opera)
* OpenXML
* Pcap files
* Portable Executable (PE) files using [pefile](https://github.com/erocarrera/pefile)
* PL SQL cache file (PL-SQL developer recall files)
* Popularity Contest log
* [Property list (plist) format](http://forensicswiki.org/wiki/Property_list_(plist)) using [biplist](https://bitbucket.org/wooster/biplist)
* [Restore Point logs (rp.log)](https://github.com/libyal/dtformats/blob/master/documentation/Restore%20point%20formats.asciidoc)
* [Safari Binary Cookies](https://github.com/libyal/dtformats/blob/master/documentation/Safari%20Cookies.asciidoc)
* SCCM client logs
* SELinux audit logs
* SkyDrive log and error log files
* [SQLite database format](http://forensicswiki.org/wiki/SQLite_database_format) using [SQLite](http://forensicswiki.org/wiki/SQLite)
* Symantec AV Corporate Edition and Endpoint Protection log
* Syslog
* [utmp, utmpx](https://github.com/libyal/dtformats/blob/master/documentation/Utmp%20login%20records%20format.asciidoc)
* [Windows Event Log (EVT)](http://forensicswiki.org/wiki/Windows_Event_Log_(EVT)) using [libevt](https://github.com/libyal/libevt)
* Windows Firewall
* [Windows Job files](http://forensicswiki.org/wiki/Windows_Job_File_Format) (also known as "at jobs")
* [Windows Prefetch files](http://forensicswiki.org/wiki/Windows_Prefetch_File_Format)
* [Windows Recycle bin](http://forensicswiki.org/wiki/Windows#Recycle_Bin) (INFO2 and $I/$R)
* [Windows NT Registry File (REGF)](http://forensicswiki.org/wiki/Windows_NT_Registry_File_(REGF)) using [libregf](https://github.com/libyal/libregf)
* [Windows Shortcut File (LNK) format](http://forensicswiki.org/wiki/LNK) using [liblnk](https://github.com/libyal/liblnk) (including shell item support)
* [Windows XML Event Log (EVTX)](http://forensicswiki.org/wiki/Windows_XML_Event_Log_(EVTX)) using [libevtx](https://github.com/libyal/libevtx)
* Xchat and Xchat scrollback files
* Zsh history files

#### Bencode file formats

* Transmission
* uTorrent

#### ESE database file formats

* Internet Explorer WebCache format
* Windows 8 File History

#### OLE Compound File formats

* Document summary information
* Summary information (top-level only)
* [Jump Lists](http://forensicswiki.org/wiki/Jump_Lists) .automaticDestinations-ms files

#### Property list (plist) formats

* Airport
* Apple Account
* Bluetooth
* Install History
* iPod/iPhone
* Mac User
* [Safari history](http://forensicswiki.org/wiki/Apple_Safari)
* Software Update
* Spotlight
* Spotlight Volume Information
* Timemachine

#### SQLite database file formats

* Android call logs
* Android SMS
* Chrome cookies
* Chrome browsing and downloads history
* Chrome Extension activity
* Firefox cookies
* Firefox browsing and downloads history
* Google Drive
* iMessage (iOS and MacOS)
* Kik (iOS)
* Launch services quarantine events
* MacKeeper cache
* MacOS document versions
* Skype text conversations
* Twitter (iOS)
* Zeitgeist activity database

#### Windows Registry formats

* AppCompatCache
* BagMRU (or ShellBags)
* CCleaner
* [Explorer ProgramsCache](https://github.com/libyal/winreg-kb/blob/master/documentation/Programs%20Cache%20values.asciidoc)
* Less Frequently Used (LFU)
* MountPoints2
* Most Recently Used (MRU) MRUList and MRUListEx (including shell item support)
* MSIE Zones
* Office MRU
* Outlook Search
* Run and RunOnce keys
* SAM
* Services
* Shutdown
* Task Scheduler Cache (Task Cache)
* Terminal Server MRU
* Timezones
* Typed URLS
* USB
* USBStor
* UserAssist
* WinRar
* Windows version information

#### Hashers Supported

* MD5
* SHA1
* SHA256

### Also see

* [Project documentation](http://wiki.log2timeline.net/)
  * [Developers Guide](Developers-Guide.md)
  * [Users Guide](Users-Guide.md)
* [Downloads](https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg/)
* Blog: [All things time related....](http://blog.kiddaland.net/)
* Mailing lists:
  * For general discussions: [log2timeline-discuss](https://groups.google.com/forum/#!forum/log2timeline-discuss)
  * For development: [log2timeline-dev](https://groups.google.com/forum/#!forum/log2timeline-dev)

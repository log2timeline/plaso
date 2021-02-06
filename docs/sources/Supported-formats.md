## Supported Formats

The information below is based of version 1.5.0

### Storage Media Image File Formats

Storage Media Image File Format support is provided by [dfvfs](https://dfvfs.readthedocs.io/en/latest/sources/Supported-formats.html#storage-media-types).

### Volume System Formats

Volume System Format support is provided by [dfvfs](https://dfvfs.readthedocs.io/en/latest/sources/Supported-formats.html#volume-systems).

### File System Formats

File System Format support is provided by [dfvfs](https://dfvfs.readthedocs.io/en/latest/sources/Supported-formats.html#file-systems).

### File formats

* Apple System Log (ASL)
* Android usage-history (app usage)
* [Basic Security Module (BSM)](https://forensicswiki.xyz/wiki/index.php?title=Basic_Security_Module_(BSM)_file_format)
* Bencode files
* [Chrome Disk Cache Format](https://forensicswiki.xyz/wiki/index.php?title=Chrome_Disk_Cache_Format)
* Chrome preferences
* CUPS IPP
* [Extensible Storage Engine (ESE) Database File (EDB) format](https://forensicswiki.xyz/wiki/index.php?title=Extensible_Storage_Engine_(ESE)_Database_File_(EDB)_format) using [libesedb](https://github.com/libyal/libesedb)
* Firefox Cache
* [Java WebStart IDX](https://forensicswiki.xyz/wiki/index.php?title=Java)
* [Jump Lists](https://forensicswiki.xyz/wiki/index.php?title=Jump_Lists) .customDestinations-ms files
* MacOS Application firewall
* [MacOS Keychain](https://github.com/libyal/dtformats/blob/main/documentation/MacOS%20keychain%20database%20file%20format.asciidoc)
* MacOS Securityd
* MacOS Wifi
* [mactime logs](https://forensicswiki.xyz/wiki/index.php?title=Mactime)
* McAfee Anti-Virus Logs
* Microsoft [Internet Explorer History File Format](https://forensicswiki.xyz/wiki/index.php?title=Internet_Explorer_History_File_Format) (also known as MSIE 4 - 9 Cache Files or index.dat) using [libmsiecf](https://github.com/libyal/libmsiecf)
* Microsoft IIS log files
* NTFS $MFT and $UsnJrnl:$J using [libfsntfs](https://github.com/libyal/libfsntfs)
* [OLE Compound File](https://forensicswiki.xyz/wiki/index.php?title=OLE_Compound_File) using [libolecf](https://github.com/libyal/libolecf)
* [Opera Browser history](https://forensicswiki.xyz/wiki/index.php?title=Opera)
* OpenXML
* Pcap files
* Portable Executable (PE) files using [pefile](https://github.com/erocarrera/pefile)
* PL SQL cache file (PL-SQL developer recall files)
* Popularity Contest log
* [Property list (plist) format](https://forensicswiki.xyz/wiki/index.php?title=Property_list_(plist)) using plistlib
* [Restore Point logs (rp.log)](https://github.com/libyal/dtformats/blob/main/documentation/Restore%20point%20formats.asciidoc)
* [Safari Binary Cookies](https://github.com/libyal/dtformats/blob/main/documentation/Safari%20Cookies.asciidoc)
* SCCM client logs
* SELinux audit logs
* SkyDrive log and error log files
* [SQLite database format](https://forensicswiki.xyz/wiki/index.php?title=SQLite_database_format) using [SQLite](https://forensicswiki.xyz/wiki/index.php?title=SQLite)
* Symantec AV Corporate Edition and Endpoint Protection log
* Syslog
* [utmp, utmpx](https://github.com/libyal/dtformats/blob/main/documentation/Utmp%20login%20records%20format.asciidoc)
* [Windows Event Log (EVT)](https://forensicswiki.xyz/wiki/index.php?title=Windows_Event_Log_(EVT)) using [libevt](https://github.com/libyal/libevt)
* Windows Firewall
* [Windows Job files](https://forensicswiki.xyz/wiki/index.php?title=Windows_Job_File_Format) (also known as "at jobs")
* [Windows Prefetch files](https://forensicswiki.xyz/wiki/index.php?title=Windows_Prefetch_File_Format)
* [Windows Recycle bin](https://forensicswiki.xyz/wiki/index.php?title=Windows#Recycle_Bin) (INFO2 and $I/$R)
* [Windows NT Registry File (REGF)](https://forensicswiki.xyz/wiki/index.php?title=Windows_NT_Registry_File_(REGF)) using [libregf](https://github.com/libyal/libregf)
* [Windows Shortcut File (LNK) format](https://forensicswiki.xyz/wiki/index.php?title=LNK) using [liblnk](https://github.com/libyal/liblnk) (including shell item support)
* [Windows XML Event Log (EVTX)](https://forensicswiki.xyz/wiki/index.php?title=Windows_XML_Event_Log_(EVTX)) using [libevtx](https://github.com/libyal/libevtx)
* Xchat and Xchat scrollback files
* Zsh history files

### Bencode file formats

* Transmission
* uTorrent

### ESE database file formats

* Internet Explorer WebCache format
* Windows 8 File History

### OLE Compound File formats

* Document summary information
* Summary information (top-level only)
* [Jump Lists](https://forensicswiki.xyz/wiki/index.php?title=Jump_Lists) .automaticDestinations-ms files

### Property list (plist) formats

* Airport
* Apple Account
* Bluetooth
* Install History
* iPod/iPhone
* Mac User
* [Safari history](https://forensicswiki.xyz/wiki/index.php?title=Apple_Safari)
* Software Update
* Spotlight
* Spotlight Volume Information
* Timemachine

### SQLite database file formats

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

### Windows Registry formats

* AppCompatCache
* BagMRU (or ShellBags)
* CCleaner
* [Explorer ProgramsCache](https://github.com/libyal/winreg-kb/blob/main/documentation/Programs%20Cache%20values.asciidoc)
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

### Hashers Supported

* MD5
* SHA1
* SHA256

## Supported Formats

The information below is based of version 20210213

### Storage media image file formats

Storage media image file format support is provided by [dfvfs](https://dfvfs.readthedocs.io/en/latest/sources/Supported-formats.html#storage-media-types).

### Volume system formats

Volume system format support is provided by [dfvfs](https://dfvfs.readthedocs.io/en/latest/sources/Supported-formats.html#volume-systems).

### File system formats

File System Format support is provided by [dfvfs](https://dfvfs.readthedocs.io/en/latest/sources/Supported-formats.html#file-systems).

### File formats

* [Amazon Web Services CloudTrail logs](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-examples.html)
* [Amazon Web Services Elastic Load Balancer access logs](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html#access-log-file-format)
* Apple System Log (ASL)
* [Azure Activity logs](https://docs.microsoft.com/en-us/azure/azure-monitor/essentials/activity-log)
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
* Portable Executable (PE) files using [pefile](https://github.com/erocarrera/pefile)
* PL SQL cache file (PL-SQL developer recall files)
* Popularity Contest log
* [Property list (plist) format](https://forensicswiki.xyz/wiki/index.php?title=Property_list_(plist)) using plistlib
* [Restore Point logs (rp.log)](https://github.com/libyal/dtformats/blob/main/documentation/Restore%20point%20formats.asciidoc)
* Santa logs
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

* Transmission BitTorrent activity file
* uTorrent active torrent file

### Browser cookie formats

* Google Analytics __utma cookie
* Google Analytics __utmb cookie
* Google Analytics __utmt cookie
* Google Analytics __utmz cookie

### Compound ZIP file formats

* OpenXML (OXML) file

### ESE database file formats

* Internet Explorer WebCache ESE database (WebCacheV01.dat, WebCacheV24.dat) file
* System Resource Usage Monitor (SRUM) ESE database file
* Windows 8 File History ESE database file

### OLE Compound File formats

* [Automatic destinations jump list OLE compound file (.automaticDestinations-ms)](https://forensicswiki.xyz/wiki/index.php?title=Jump_Lists)
* Document summary information (\0x05DocumentSummaryInformation)
* Summary information (\0x05SummaryInformation) (top-level only)

### Property list (plist) formats

* Airport plist file
* Apple account information plist file
* Bluetooth plist file
* iPod, iPad and iPhone plist file
* Launchd plist file
* MacOS installation history plist file
* MacOS software update plist file
* MacOS user plist file
* [Safari history plist file](https://forensicswiki.xyz/wiki/index.php?title=Apple_Safari)
* Spotlight plist file
* Spotlight volume configuration plist file
* TimeMachine plist file

### SQLite database file formats

* Android call history SQLite database (contacts2.db) file
* Android text messages (SMS) SQLite database (mmssms.dbs) file
* Android WebViewCache SQLite database file
* Android WebView SQLite database file
* Dropbox sync_history SQLite database file
* Google Chrome 17 - 65 cookies SQLite database file
* Google Chrome 27 and later history SQLite database file
* Google Chrome 66 and later cookies SQLite database file
* Google Chrome 8 - 25 history SQLite database file
* Google Chrome autofill SQLite database (Web Data) file
* Google Chrome extension activity SQLite database file
* Google Drive snapshot SQLite database (snapshot.db) file
* Google Hangouts conversations SQLite database (babel.db) file
* iOS Kik messenger SQLite database (kik.sqlite) file
* Kodi videos SQLite database (MyVideos.db) file
* MacOS and iOS iMessage database (chat.db, sms.db) file
* MacOS application usage SQLite database (application_usage.sqlite) file
* MacOS document revisions SQLite database file
* MacOS Duet / KnowledgeC SQLites database file
* MacOS launch services quarantine events database SQLite database file
* MacOS MacKeeper cache SQLite database file
* MacOS Notes SQLite database (NotesV7.storedata) file
* MacOS Notification Center SQLite database file
* MacOS Transparency, Consent, Control (TCC) SQLite database (TCC.db) file
* Mozilla Firefox cookies SQLite database file
* Mozilla Firefox downloads SQLite database (downloads.sqlite) file
* Mozilla Firefox history SQLite database (places.sqlite) file
* Safari history SQLite database (History.db) file
* Skype SQLite database (main.db) file
* Tango on Android profile SQLite database file
* Tango on Android TC SQLite database file
* Twitter on Android SQLite database file
* Twitter on iOS 8 and later SQLite database (twitter.db) file
* Windows 10 Timeline SQLite database (ActivitiesCache.db) file
* Zeitgeist activity SQLite database file

### Syslog file formats

* Cron syslog line
* SSH syslog line

### Windows Registry formats

* Application Compatibility Cache Registry data
* Background Activity Moderator (BAM) Registry data
* BagMRU (or ShellBags) Registry data
* Boot Execution Registry data
* CCleaner Registry data
* Microsoft Internet Explorer zone settings Registry data
* Microsoft Office MRU Registry data
* Microsoft Outlook search MRU Registry data
* Most Recently Used (MRU) Registry data
* Run and run once Registry data
* Security Accounts Manager (SAM) users Registry data
* Terminal Server Client Connection Registry data
* Terminal Server Client Most Recently Used (MRU) Registry data
* User Assist Registry data
* Windows boot verification Registry data
* Windows drivers and services Registry data
* Windows Explorer mount points Registry data
* [Windows Explorer Programs Cache Registry data](https://winreg-kb.readthedocs.io/en/latest/sources/explorer-keys/Program-cache.html)
* Windows Explorer typed URLs Registry data
* Windows last shutdown Registry data
* Windows log-on Registry data
* Windows network drives Registry data
* Windows networks (NetworkList) Registry data
* Windows Task Scheduler cache Registry data
* Windows time zone Registry data
* Windows USB device Registry data
* Windows USB Plug And Play Manager USBStor Registry data
* Windows version (product) Registry data
* WinRAR History Registry data

### Hashers Supported

* MD5
* SHA1
* SHA256

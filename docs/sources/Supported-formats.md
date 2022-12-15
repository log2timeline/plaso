## Supported Formats

The information below is based of version 20221212

### Storage media image file formats

Storage media image file format support is provided by [dfVFS](https://dfvfs.readthedocs.io/en/latest/sources/Supported-formats.html#storage-media-types).

### Volume system formats

Volume system format support is provided by [dfVFS](https://dfvfs.readthedocs.io/en/latest/sources/Supported-formats.html#volume-systems).

### File system formats

File System Format support is provided by [dfVFS](https://dfvfs.readthedocs.io/en/latest/sources/Supported-formats.html#file-systems).

### File formats

* Android usage history (usage-history.xml) file
* Apple System Log (ASL)
* [Basic Security Module (BSM)](https://forensics.wiki/basic_security_module_(bsm)_file_format)
* Bencode files
* [Chrome Disk Cache Format](https://forensics.wiki/chrome_disk_cache_format)
* Chrome preferences
* CUPS IPP
* [Extensible Storage Engine (ESE) Database File (EDB) format](https://forensics.wiki/extensible_storage_engine_(ese)_database_file_(edb)_format) using [libesedb](https://github.com/libyal/libesedb)
* Firefox Cache
* [Java WebStart IDX](https://forensics.wiki/java)
* [Jump Lists](https://forensics.wiki/jump_lists) .customdestinations-ms files
* [MacOS Keychain](https://github.com/libyal/dtformats/blob/main/documentation/MacOS%20keychain%20database%20file%20format.asciidoc)
* [mactime logs](https://forensics.wiki/mactime)
* McAfee Anti-Virus Logs
* Microsoft [Internet Explorer History File Format](https://forensics.wiki/internet_explorer_history_file_format) (also known as msie 4 - 9 cache files or index.dat) using [libmsiecf](https://github.com/libyal/libmsiecf)
* NTFS $MFT and $UsnJrnl:$J using [libfsntfs](https://github.com/libyal/libfsntfs)
* [OLE Compound File](https://forensics.wiki/ole_compound_file) using [libolecf](https://github.com/libyal/libolecf)
* [Opera Browser history](https://forensics.wiki/opera)
* OpenXML
* Portable Executable (PE) files using [pefile](https://github.com/erocarrera/pefile)
* PL SQL cache file (PL-SQL developer recall files)
* [Property list (plist) format](https://forensics.wiki/property_list_(plist)) using plistlib
* [Restore Point logs (rp.log)](https://github.com/libyal/dtformats/blob/main/documentation/Restore%20point%20formats.asciidoc)
* [Safari Binary Cookies](https://github.com/libyal/dtformats/blob/main/documentation/Safari%20Cookies.asciidoc)
* SCCM client logs
* SkyDrive multi-line log and error log files
* [SQLite database format](https://forensics.wiki/sqlite_database_format) using [sqlite](https://forensics.wiki/sqlite)
* Symantec AV Corporate Edition and Endpoint Protection log
* Syslog
* [utmp, utmpx](https://github.com/libyal/dtformats/blob/main/documentation/Utmp%20login%20records%20format.asciidoc)
* [Windows Event Log (EVT)](https://forensics.wiki/windows_event_log_(evt)) using [libevt](https://github.com/libyal/libevt)
* [Windows Job files](https://forensics.wiki/windows_job_file_format) (also known as "at jobs")
* [Windows Prefetch files](https://forensics.wiki/windows_prefetch_file_format)
* [Windows Recycle bin](https://forensics.wiki/windows/#recyclebin) (info2 and $i/$r)
* [Windows NT Registry File (REGF)](https://forensics.wiki/windows_nt_registry_file_(regf)) using [libregf](https://github.com/libyal/libregf)
* [Windows Shortcut File (LNK) format](https://forensics.wiki/lnk) using [liblnk](https://github.com/libyal/liblnk) (including shell item support)
* [Windows XML Event Log (EVTX)](https://forensics.wiki/windows_xml_event_log_(evtx)) using [libevtx](https://github.com/libyal/libevtx)
* Viminfo files
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

### JSON-L log file formats

* [AWS CloudTrail logs](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-examples.html)
* [Azure Activity logs](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/activity-log)
* Azure Application Gateway access log
* Docker container configuration file
* Docker container log file
* Docker layer configuration file
* Google Cloud (GCP) log
* iOS Application Privacy report
* Microsoft (Office) 365 audit log

### OLE Compound File formats

* [Automatic destinations jump list OLE compound file (.automaticDestinations-ms)](https://forensics.wiki/jump_lists)
* Document summary information (\0x05DocumentSummaryInformation)
* Summary information (\0x05SummaryInformation) (top-level only)

### Property list (plist) formats

* MacOS Airport plist file
* Apple account information plist file
* MacOS Bluetooth plist file
* Apple iOS Car Play Application plist file
* iPod, iPad and iPhone plist file
* MacOS Launchd plist file
* MacOS installation history plist file
* MacOS software update plist file
* MacOS user plist file
* [Safari history plist file](https://forensics.wiki/apple_safari)
* Spotlight searched terms plist file
* Spotlight volume configuration plist file
* MacOS TimeMachine plist file

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

### Text-based log file formats

* Advanced Packaging Tool (APT) History log file
* Android logcat file
* Apache access log (access.log) file
* [AWS ELB Access log file](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html#access-log-file-format)
* Bash history file
* Confluence access log (access.log) file
* Debian package manager log (dpkg.log) file
* Google Drive Sync log file
* Google-formatted log file
* iOS lockdown daemon log
* iOS sysdiag log
* iOS sysdiagnose logd file
* MacOS Application firewall log (appfirewall.log) file
* MacOS security daemon (securityd) log file
* MacOS Wi-Fi log (wifi.log) file
* Microsoft IIS log file
* OneDrive (or SkyDrive) version 1 log file
* OneDrive (or SkyDrive) version 2 log file
* Popularity Contest log file
* PostgreSQL application log file
* Santa log (santa.log) file
* SELinux audit log (audit.log) file
* Snort3/Suricata fast-log alert log (fast.log) file
* Sophos anti-virus log file (SAV.txt) file
* System Center Configuration Manager (SCCM) client log file
* System log (syslog) file
* Viminfo file
* vsftpd log file
* Windows Firewall log file
* Windows SetupAPI log file
* XChat log file
* XChat scrollback log file
* ZSH extended history file

### Windows Registry formats

* AMCache (AMCache.hve)
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

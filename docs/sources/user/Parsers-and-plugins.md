### Parsers

Name | Description
--- | ---
amcache | Parser for AMCache Windows NT Registry (AMCache.hve) files.
android_app_usage | Parser for Android usage history (usage-history.xml) files.
apache_access | Parser for Apache access log (access.log) files.
apt_history | Parser for Advanced Packaging Tool (APT) History log files.
asl_log | Parser for Apple System Log (ASL) files.
bash_history | Parser for Bash history files.
bencode | Parser for Bencoded files.
binary_cookies | Parser for Safari Binary Cookie files.
bsm_log | Parser for Basic Security Module (BSM) event auditing files.
chrome_cache | Parser for Google Chrome or Chromium Cache files.
chrome_preferences | Parser for Google Chrome Preferences files.
cups_ipp | Parser for CUPS IPP files.
custom_destinations | Parser for Custom destinations jump list (.customDestinations-ms) files.
czip | Parser for Compound ZIP files.
dockerjson | Parser for Docker configuration and log JSON files.
dpkg | Parser for Debian package manager log (dpkg.log) files.
esedb | Parser for Extensible Storage Engine (ESE) Database File (EDB) format.
filestat | Parser for file system stat information.
firefox_cache | Parser for Mozilla Firefox Cache version 1 file (version 31 or earlier).
firefox_cache2 | Parser for Mozilla Firefox Cache version 2 file (version 32 or later).
fseventsd | Parser for MacOS File System Events Disk Log Stream (fseventsd) files.
gdrive_synclog | Parser for Google Drive Sync log files.
googlelog | Parser for Google-formatted log files.
java_idx | Parser for Java WebStart Cache IDX files.
lnk | Parser for Windows Shortcut (LNK) files.
mac_appfirewall_log | Parser for MacOS Application firewall log (appfirewall.log) files.
mac_keychain | Parser for MacOS keychain database files.
mac_securityd | Parser for MacOS security daemon (securityd) log files.
mactime | Parser for SleuthKit version 3 bodyfile.
macwifi | Parser for MacOS Wifi log (wifi.log) files.
mcafee_protection | Parser for McAfee Anti-Virus access protection log files.
mft | Parser for NTFS $MFT metadata files.
msiecf | Parser for Microsoft Internet Explorer (MSIE) 4 - 9 cache (index.dat) files.
networkminer_fileinfo | Parser for NetworkMiner .fileinfos files.
olecf | 
opera_global | Parser for Opera global history (global_history.dat) files.
opera_typed_history | Parser for Opera typed history (typed_history.xml) files.
pe | Parser for Portable Executable (PE) files.
plist | Parser for Property list (plist) files.
pls_recall | 
popularity_contest | Parser for Popularity Contest log files.
prefetch | Parser for Windows Prefetch File (PF).
recycle_bin | Parser for Windows $Recycle.Bin $I files.
recycle_bin_info2 | Parser for Windows Recycler INFO2 files.
rplog | Parser for Windows Restore Point log (rp.log) files.
santa | Parser for Santa log (santa.log) files.
sccm | Parser for System Center Configuration Manager (SCCM) client log files.
selinux | Parser for SELinux audit log (audit.log) files.
setupapi | Parser for Windows SetupAPI log files.
skydrive_log | Parser for OneDrive (or SkyDrive) log files.
skydrive_log_old | Parser for OneDrive (or SkyDrive) old log files.
sophos_av | Parser for Sophos Anti-Virus log file (SAV.txt) files.
spotlight_storedb | Parser for Apple Spotlight store database (store.db) files.
sqlite | Parser for SQLite database files.
symantec_scanlog | Parser for AV Corporate Edition and Endpoint Protection log files.
syslog | Parser for System log (syslog) files.
systemd_journal | Parser for Systemd journal files.
trendmicro_url | Parser for Trend Micro Office Web Reputation log files.
trendmicro_vd | Parser for Trend Micro Office Scan Virus Detection log files.
usnjrnl | Parser for NTFS USN change journal ($UsnJrnl:$J) file system metadata files.
utmp | Parser for Linux libc6 utmp files.
utmpx | Parser for Mac OS X 10.5 utmpx files.
vsftpd | Parser for vsftpd log files.
winevt | Parser for Windows EventLog (EVT) files.
winevtx | Parser for Windows XML EventLog (EVTX) files.
winfirewall | Parser for Windows Firewall log files.
winiis | Parser for Microsoft IIS log files.
winjob | Parser for Windows Scheduled Task job (or at-job) files.
winreg | Parser for Windows NT Registry (REGF) files.
xchatlog | Parser for XChat log files.
xchatscrollback | Parser for XChat scrollback log files.
zsh_extended_history | Parser for ZSH extended history files.

### Parser plugins: bencode

Name | Description
--- | ---
bencode_transmission | Parser for Transmission BitTorrent activity files.
bencode_utorrent | Parser for uTorrent active torrent files.

### Parser plugins: czip

Name | Description
--- | ---
oxml | Parser for OpenXML (OXML) files.

### Parser plugins: esedb

Name | Description
--- | ---
file_history | Parser for Windows 8 File History ESE database files.
msie_webcache | Parser for Internet Explorer WebCache ESE database (WebCacheV01.dat, WebCacheV24.dat) files.
srum | Parser for System Resource Usage Monitor (SRUM) ESE database files.

### Parser plugins: olecf

Name | Description
--- | ---
olecf_automatic_destinations | Parser for Automatic destinations jump list OLE compound file (.automaticDestinations-ms).
olecf_default | Parser for Generic OLE compound item.
olecf_document_summary | Parser for Document summary information (\0x05DocumentSummaryInformation).
olecf_summary | Parser for Summary information (\0x05SummaryInformation) (top-level only).

### Parser plugins: plist

Name | Description
--- | ---
airport | Parser for Airport plist files.
apple_id | Parser for Apple account information plist files.
ipod_device | Parser for iPod, iPad and iPhone plist files.
launchd_plist | Parser for Launchd plist files.
macos_software_update | Parser for MacOS software update plist files.
macosx_bluetooth | Parser for Bluetooth plist files.
macosx_install_history | Parser for MacOS installation history plist files.
macuser | Parser for MacOS user plist files.
plist_default | Parser for plist files.
safari_history | Parser for Safari history plist files.
spotlight | Parser for Spotlight plist files.
spotlight_volume | Parser for Spotlight volume configuration plist files.
time_machine | Parser for TimeMachine plist files.

### Parser plugins: sqlite

Name | Description
--- | ---
android_calls | Parser for Android call history SQLite database (contacts2.db) files.
android_sms | Parser for Android text messages (SMS) SQLite database (mmssms.dbs) files.
android_webview | Parser for Android WebView SQLite database files.
android_webviewcache | Parser for Android WebViewCache SQLite database files.
appusage | Parser for MacOS application usage SQLite database (application_usage.sqlite) files.
chrome_17_cookies | Parser for Google Chrome 17 - 65 cookies SQLite database files.
chrome_27_history | Parser for Google Chrome 27 and later history SQLite database files.
chrome_66_cookies | Parser for Google Chrome 66 and later cookies SQLite database files.
chrome_8_history | Parser for Google Chrome 8 - 25 history SQLite database files.
chrome_autofill | Parser for Google Chrome autofill SQLite database (Web Data) files.
chrome_extension_activity | Parser for Google Chrome extension activity SQLite database files.
firefox_cookies | Parser for Mozilla Firefox cookies SQLite database files.
firefox_downloads | Parser for Mozilla Firefox downloads SQLite database (downloads.sqlite) files.
firefox_history | Parser for Mozilla Firefox history SQLite database (places.sqlite) files.
google_drive | Parser for Google Drive snapshot SQLite database (snapshot.db) files.
hangouts_messages | Parser for Google Hangouts conversations SQLite database (babel.db) files.
imessage | Parser for MacOS and iOS iMessage database (chat.db, sms.db) files.
kik_messenger | Parser for iOS Kik messenger SQLite database (kik.sqlite) files.
kodi | Parser for Kodi videos SQLite database (MyVideos.db) files.
ls_quarantine | Parser for MacOS launch services quarantine events database SQLite database files.
mac_document_versions | Parser for MacOS document revisions SQLite database files.
mac_knowledgec | Parser for MacOS Duet / KnowledgeC SQLites database files.
mac_notes | Parser for MacOS Notes SQLite database (NotesV7.storedata) files.
mac_notificationcenter | Parser for MacOS Notification Center SQLite database files.
mackeeper_cache | Parser for MacOS MacKeeper cache SQLite database files.
macostcc | Parser for MacOS Transaprency, Consent, Control (TCC) SQLite database (TCC.db) files.
safari_historydb | Parser for Safari history SQLite database (History.db) files.
skype | Parser for Skype SQLite database (main.db) files.
tango_android_profile | Parser for Tango on Android profile SQLite database files.
tango_android_tc | Parser for Tango on Android TC SQLite database files.
twitter_android | Parser for Twitter on Android SQLite database files.
twitter_ios | Parser for Twitter on iOS 8 and later SQLite database (twitter.db) files.
windows_timeline | Parser for Windows 10 Timeline SQLite database (ActivitiesCache.db) files.
zeitgeist | Parser for Zeitgeist activity SQLite database files.

### Parser plugins: syslog

Name | Description
--- | ---
cron | Parser for Cron syslog line.
ssh | Parser for SSH syslog line.

### Parser plugins: winreg

Name | Description
--- | ---
appcompatcache | Parser for Application Compatibility Cache Registry data.
bagmru | Parser for BagMRU (or ShellBags) Registry data.
bam | Parser for Background Activity Moderator (BAM) Registry data.
ccleaner | Parser for CCleaner Registry data.
explorer_mountpoints2 | Parser for Windows Explorer mount points Registry data.
explorer_programscache | Parser for Windows Explorer Programs Cache Registry data.
microsoft_office_mru | Parser for Microsoft Office MRU Registry data.
microsoft_outlook_mru | Parser for Microsoft Outlook search MRU Registry data.
mrulist_shell_item_list | Parser for Most Recently Used (MRU) Registry data.
mrulist_string | Parser for Most Recently Used (MRU) Registry data.
mrulistex_shell_item_list | Parser for Most Recently Used (MRU) Registry data.
mrulistex_string | Parser for Most Recently Used (MRU) Registry data.
mrulistex_string_and_shell_item | Parser for Most Recently Used (MRU) Registry data.
mrulistex_string_and_shell_item_list | Parser for Most Recently Used (MRU) Registry data.
msie_zone | Parser for Microsoft Internet Explorer zone settings Registry data.
mstsc_rdp | Parser for Terminal Server Client Connection Registry data.
mstsc_rdp_mru | Parser for Terminal Server Client Most Recently Used (MRU) Registry data.
network_drives | Parser for Windows network drives Registry data.
networks | Parser for Windows networks (NetworkList) Registry data.
userassist | Parser for User Assist Registry data.
windows_boot_execute | Parser for Boot Execution Registry data.
windows_boot_verify | Parser for Windows boot verification Registry data.
windows_run | Parser for Run and run once Registry data.
windows_sam_users | Parser for Security Accounts Manager (SAM) users Registry data.
windows_services | Parser for Windows drivers and services Registry data.
windows_shutdown | Parser for Windows last shutdown Registry data.
windows_task_cache | Parser for Windows Task Scheduler cache Registry data.
windows_timezone | Parser for Windows time zone Registry data.
windows_typed_urls | Parser for Windows Explorer typed URLs Registry data.
windows_usb_devices | Parser for Windows USB device Registry data.
windows_usbstor_devices | Parser for Windows USB Plug And Play Manager USBStor Registry data.
windows_version | Parser for Windows version (product) Registry data.
winlogon | Parser for Windows log-on Registry data.
winrar_mru | Parser for WinRAR History Registry data.
winreg_default | Parser for Windows Registry data.

### Parser presets (data/presets.yaml)

Name | Parsers and plugins
--- | ---
android | android_app_usage, chrome_cache, filestat, sqlite/android_calls, sqlite/android_sms, sqlite/android_webview, sqlite/android_webviewcache, sqlite/chrome_8_history, sqlite/chrome_17_cookies, sqlite/chrome_27_history, sqlite/chrome_66_cookies, sqlite/skype
linux | apt_history, bash_history, bencode, czip/oxml, dockerjson, dpkg, filestat, gdrive_synclog, googlelog, olecf, pls_recall, popularity_contest, selinux, sqlite/google_drive, sqlite/skype, sqlite/zeitgeist, syslog, systemd_journal, utmp, vsftpd, webhist, xchatlog, xchatscrollback, zsh_extended_history
macos | asl_log, bash_history, bencode, bsm_log, cups_ipp, czip/oxml, filestat, fseventsd, gdrive_synclog, mac_appfirewall_log, mac_keychain, mac_securityd, macwifi, olecf, plist, spotlight_storedb, sqlite/appusage, sqlite/google_drive, sqlite/imessage, sqlite/ls_quarantine, sqlite/mac_document_versions, sqlite/mac_notes, sqlite/mackeeper_cache, sqlite/mac_knowledgec, sqlite/skype, syslog, utmpx, webhist, zsh_extended_history
webhist | binary_cookies, chrome_cache, chrome_preferences, esedb/msie_webcache, firefox_cache, java_idx, msiecf, opera_global, opera_typed_history, plist/safari_history, sqlite/chrome_8_history, sqlite/chrome_17_cookies, sqlite/chrome_27_history, sqlite/chrome_66_cookies, sqlite/chrome_autofill, sqlite/chrome_extension_activity, sqlite/firefox_cookies, sqlite/firefox_downloads, sqlite/firefox_history, sqlite/safari_historydb
win7 | amcache, custom_destinations, esedb/file_history, olecf/olecf_automatic_destinations, recycle_bin, winevtx, win_gen
win7_slow | mft, win7
win_gen | bencode, czip/oxml, esedb, filestat, gdrive_synclog, lnk, mcafee_protection, olecf, pe, prefetch, setupapi, sccm, skydrive_log, skydrive_log_old, sqlite/google_drive, sqlite/skype, symantec_scanlog, usnjrnl, webhist, winfirewall, winjob, winreg
winxp | recycle_bin_info2, rplog, win_gen, winevt
winxp_slow | mft, winxp


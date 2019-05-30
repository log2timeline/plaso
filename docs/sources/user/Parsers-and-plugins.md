### Parsers

Name | Description
--- | ---
amcache | Parser for Amcache Registry entries.
android_app_usage | Parser for Android usage-history.xml files.
apache_access | Apache access Parser
asl_log | Parser for ASL log files.
bash | Parser for Bash history files
bencode | Parser for bencoded files.
binary_cookies | Parser for Safari Binary Cookie files.
bsm_log | Parser for BSM log files.
chrome_cache | Parser for Chrome Cache files.
chrome_preferences | Parser for Chrome Preferences files.
cups_ipp | Parser for CUPS IPP files.
custom_destinations | Parser for *.customDestinations-ms files.
czip | Parser for compound ZIP files.
dockerjson | Parser for JSON Docker files.
dpkg | Parser for Debian dpkg.log files.
esedb | Parser for Extensible Storage Engine (ESE) database files.
filestat | Parser for file system stat information.
firefox_cache | Parser for Firefox Cache version 1 files (Firefox 31 or earlier).
firefox_cache2 | Parser for Firefox Cache version 2 files (Firefox 32 or later).
fsevents | Parser for fseventsd files.
gdrive_synclog | Parser for Google Drive Sync log files.
java_idx | Parser for Java WebStart Cache IDX files.
lnk | Parser for Windows Shortcut (LNK) files.
mac_appfirewall_log | Parser for appfirewall.log files.
mac_keychain | Parser for MacOS Keychain files.
mac_securityd | Parser for MacOS securityd log files.
mactime | Parser for SleuthKit version 3 bodyfiles.
macwifi | Parser for MacOS wifi.log files.
mcafee_protection | Parser for McAfee AV Access Protection log files.
mft | Parser for NTFS $MFT metadata files.
msiecf | Parser for MSIE Cache Files (MSIECF) also known as index.dat.
olecf | Parser for OLE Compound Files (OLECF).
opera_global | Parser for Opera global_history.dat files.
opera_typed_history | Parser for Opera typed_history.xml files.
pe | Parser for Portable Executable (PE) files.
plist | Parser for binary and text plist files.
pls_recall | Parser for PL/SQL Recall files.
popularity_contest | Parser for popularity contest log files.
prefetch | Parser for Windows Prefetch files.
recycle_bin | Parser for Windows $Recycle.Bin $I files.
recycle_bin_info2 | Parser for Windows Recycler INFO2 files.
rplog | Parser for Windows Restore Point (rp.log) files.
santa | Santa Parser
sccm | Parser for SCCM logs files.
selinux | Parser for SELinux audit.log files.
skydrive_log | Parser for OneDrive (or SkyDrive) log files.
skydrive_log_old | Parser for OneDrive (or SkyDrive) old log files.
sophos_av | Parser for Anti-Virus log (SAV.txt) files.
sqlite | Parser for SQLite database files.
symantec_scanlog | Parser for Symantec Anti-Virus log files.
syslog | Syslog Parser
systemd_journal | Parser for Systemd Journal files.
trendmicro_url | Parser for Trend Micro Office Web Reputation log files.
trendmicro_vd | Parser for Trend Micro Office Scan Virus Detection log files.
usnjrnl | Parser for NTFS USN change journal ($UsnJrnl).
utmp | Parser for Linux libc6 utmp files.
utmpx | Parser for Mac OS X 10.5 utmpx files.
winevt | Parser for Windows EventLog (EVT) files.
winevtx | Parser for Windows XML EventLog (EVTX) files.
winfirewall | Parser for Windows Firewall Log files.
winiis | Parser for Microsoft IIS log files.
winjob | Parser for Windows Scheduled Task job (or At-job) files.
winreg | Parser for Windows NT Registry (REGF) files.
xchatlog | Parser for XChat log files.
xchatscrollback | Parser for XChat scrollback log files.
zsh_extended_history | Parser for ZSH extended history files

### Parser plugins: bencode

Name | Description
--- | ---
bencode_transmission | Parser for Transmission bencoded files.
bencode_utorrent | Parser for uTorrent bencoded files.

### Parser plugins: czip

Name | Description
--- | ---
oxml | Parser for OpenXML (OXML) files.

### Parser plugins: esedb

Name | Description
--- | ---
file_history | Parser for File History ESE database files.
msie_webcache | Parser for MSIE WebCache ESE database files.
srum | Parser for System Resource Usage Monitor (SRUM) ESE database files.

### Parser plugins: olecf

Name | Description
--- | ---
olecf_automatic_destinations | Parser for *.automaticDestinations-ms OLECF files.
olecf_default | Parser for a generic OLECF item.
olecf_document_summary | Parser for a DocumentSummaryInformation OLECF stream.
olecf_summary | Parser for a SummaryInformation OLECF stream.

### Parser plugins: plist

Name | Description
--- | ---
airport | Parser for Airport plist files.
apple_id | Parser for Apple account information plist files.
ipod_device | Parser for iPod, iPad and iPhone plist files.
macosx_bluetooth | Parser for Bluetooth plist files.
macosx_install_history | Parser for installation history plist files.
macuser | Parser for MacOS user plist files.
maxos_software_update | Parser for MacOS software update plist files.
plist_default | Parser for plist files.
safari_history | Parser for Safari history plist files.
spotlight | Parser for Spotlight plist files.
spotlight_volume | Parser for Spotlight volume configuration plist files.
time_machine | Parser for TimeMachine plist files.

### Parser plugins: sqlite

Name | Description
--- | ---
android_calls | Parser for Android calls SQLite database files.
android_sms | Parser for Android text messages SQLite database files.
android_webview | Parser for Android WebView databases
android_webviewcache | Parser for Android WebViewCache databases
appusage | Parser for MacOS application usage SQLite database files.
chrome_27_history | Parser for Google Chrome 27 and up history SQLite database files.
chrome_8_history | Parser for Google Chrome 8 - 25 history SQLite database files.
chrome_autofill | Parser for Chrome autofill SQLite database files.
chrome_cookies | Parser for Chrome cookies SQLite database files.
chrome_extension_activity | Parser for Chrome extension activity SQLite database files.
firefox_cookies | Parser for Firefox cookies SQLite database files.
firefox_downloads | Parser for Firefox downloads SQLite database files.
firefox_history | Parser for Firefox history SQLite database files.
google_drive | Parser for Google Drive SQLite database files.
hangouts_messages | Parser for Google Hangouts Messages SQLite database files.
imessage | Parser for the iMessage and SMS SQLite databases on OSX and iOS.
kik_messenger | Parser for iOS Kik messenger SQLite database files.
kodi | Parser for Kodi MyVideos.db files.
ls_quarantine | Parser for LS quarantine events SQLite database files.
mac_document_versions | Parser for document revisions SQLite database files.
mac_notificationcenter | Parser for the Notification Center SQLite database
mackeeper_cache | Parser for MacKeeper Cache SQLite database files.
safari_history | Parser for Safari history SQLite database files.
skype | Parser for Skype SQLite database files.
tango_android_profile | Parser for Tango on Android profile database.
tango_android_tc | Parser for Tango on Android tc database.
twitter_android | Parser for Twitter on android database
twitter_ios | Parser for Twitter on iOS 8+ database
windows_timeline | Parser for the Windows Timeline SQLite database
zeitgeist | Parser for Zeitgeist activity SQLite database files.

### Parser plugins: syslog

Name | Description
--- | ---
cron | Parser for syslog cron messages.
ssh | Parser for SSH syslog entries.

### Parser plugins: winreg

Name | Description
--- | ---
appcompatcache | Parser for Application Compatibility Cache Registry data.
bagmru | Parser for BagMRU Registry data.
ccleaner | Parser for CCleaner Registry data.
explorer_mountpoints2 | Parser for mount points Registry data.
explorer_programscache | Parser for Explorer ProgramsCache Registry data.
microsoft_office_mru | Parser for Microsoft Office MRU Registry data.
microsoft_outlook_mru | Parser for Microsoft Outlook search MRU Registry data.
mrulist_shell_item_list | Parser for Most Recently Used (MRU) Registry data.
mrulist_string | Parser for Most Recently Used (MRU) Registry data.
mrulistex_shell_item_list | Parser for Most Recently Used (MRU) Registry data.
mrulistex_string | Parser for Most Recently Used (MRU) Registry data.
mrulistex_string_and_shell_item | Parser for Most Recently Used (MRU) Registry data.
mrulistex_string_and_shell_item_list | Parser for Most Recently Used (MRU) Registry data.
msie_zone | Parser for Internet Explorer zone settings Registry data.
mstsc_rdp | Parser for Terminal Server Client Connection Registry data.
mstsc_rdp_mru | Parser for Terminal Server Client MRU Registry data.
network_drives | Parser for Network Registry data.
networks | Parser for NetworkList data.
userassist | Parser for User Assist Registry data.
windows_boot_execute | Parser for Boot Execution Registry data.
windows_boot_verify | Parser for Boot Verification Registry data.
windows_run | Parser for run and run once Registry data.
windows_sam_users | Parser for SAM Users and Names Registry keys.
windows_services | Parser for services and drivers Registry data.
windows_shutdown | Parser for ShutdownTime Registry value.
windows_task_cache | Parser for Task Scheduler cache Registry data.
windows_timezone | Parser for Windows timezone settings.
windows_typed_urls | Parser for Explorer typed URLs Registry data.
windows_usb_devices | Parser for USB device Registry entries.
windows_usbstor_devices | Parser for USB Plug And Play Manager USBStor Registry Key.
windows_version | Parser for Windows version Registry data.
winlogon | Parser for winlogon Registry data.
winrar_mru | Parser for WinRAR History Registry data.
winreg_default | Parser for Registry data.

### Parser presets (data/presets.yaml)

Name | Parsers and plugins
--- | ---
android | android_app_usage, chrome_cache, filestat, sqlite/android_calls, sqlite/android_sms, sqlite/android_webview, sqlite/android_webviewcache, sqlite/chrome_27_history, sqlite/chrome_8_history, sqlite/chrome_cookies, sqlite/skype
linux | bash_history, bencode, czip/oxml, dockerjson, dpkg, filestat, gdrive_synclog, java_idx, olecf, pls_recall, popularity_contest, selinux, sqlite/google_drive, sqlite/skype, sqlite/zeitgeist, syslog, systemd_journal, utmp, webhist, xchatlog, xchatscrollback, zsh_extended_history
macos | asl_log, bash_history, bencode, bsm_log, cups_ipp, czip/oxml, filestat, fseventsd, gdrive_synclog, java_idx, mac_appfirewall_log, mac_keychain, mac_securityd, macwifi, olecf, plist, sqlite/appusage, sqlite/google_drive, sqlite/imessage, sqlite/ls_quarantine, sqlite/mac_document_versions, sqlite/mackeeper_cache, sqlite/skype, syslog, utmpx, webhist, zsh_extended_history
webhist | binary_cookies, chrome_cache, chrome_preferences, esedb/msie_webcache, firefox_cache, java_idx, msiecf, opera_global, opera_typed_history, plist/safari_history, sqlite/chrome_27_history, sqlite/chrome_8_history, sqlite/chrome_autofill, sqlite/chrome_cookies, sqlite/chrome_extension_activity, sqlite/firefox_cookies, sqlite/firefox_downloads, sqlite/firefox_history
win7 | amcache, custom_destinations, esedb/file_history, olecf/olecf_automatic_destinations, recycle_bin, winevtx, win_gen
win7_slow | mft, win7
win_gen | bencode, czip/oxml, esedb, filestat, gdrive_synclog, java_idx, lnk, mcafee_protection, olecf, pe, prefetch, sccm, skydrive_log, skydrive_log_old, sqlite/google_drive, sqlite/skype, symantec_scanlog, usnjrnl, webhist, winfirewall, winjob, winreg
winxp | recycle_bin_info2, rplog, win_gen, winevt
winxp_slow | mft, winxp


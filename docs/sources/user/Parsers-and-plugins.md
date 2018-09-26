### Parsers

Name | Description
--- | ---
android_app_usage | Parser for the Android usage-history.xml file.
asl_log | Parser for ASL log files.
bencode | Parser for bencoded files.
binary_cookies | Parser for Safari Binary Cookie files.
bsm_log | Parser for BSM log files.
chrome_cache | Parser for Chrome Cache files.
chrome_preferences | Parser for Chrome Preferences files.
cups_ipp | Parser for CUPS IPP files.
custom_destinations | Parser for *.customDestinations-ms files.
esedb | Parser for Extensible Storage Engine (ESE) database files.
filestat | Parser for file system stat information.
firefox_cache | Parser for Firefox Cache files.
firefox_old_cache | Parser for Firefox Cache files.
hachoir | Parser that wraps Hachoir.
java_idx | Parser for Java WebStart Cache IDX files.
lnk | Parser for Windows Shortcut (LNK) files.
mac_appfirewall_log | Parser for appfirewall.log files.
mac_keychain | Parser for Mac OS X Keychain files.
mac_securityd | Parser for Mac OS X securityd log files.
mactime | Parser for SleuthKit's mactime bodyfiles.
macwifi | Parser for Mac OS X wifi.log files.
mcafee_protection | Parser for McAfee AV Access Protection log files.
msiecf | Parser for MSIE Cache Files (MSIECF) also known as index.dat.
olecf | Parser for OLE Compound Files (OLECF).
openxml | Parser for OpenXML (OXML) files.
opera_global | Parser for Opera global_history.dat files.
opera_typed_history | Parser for Opera typed_history.xml files.
pcap | Parser for PCAP files.
pe | Parser for Portable Executable (PE) files.
plist | Parser for binary and text plist files.
pls_recall | Parser for PL/SQL Recall files.
popularity_contest | Parser for popularity contest log files.
prefetch | Parser for Windows Prefetch files.
recycle_bin | Parser for Windows $Recycle.Bin $I files.
recycle_bin_info2 | Parser for Windows Recycler INFO2 files.
rplog | Parser for Windows Restore Point (rp.log) files.
selinux | Parser for SELinux audit log files.
skydrive_log | Parser for OneDrive (or SkyDrive) log files.
skydrive_log_error | Parser for OneDrive (or SkyDrive) error log files.
sqlite | Parser for SQLite database files.
symantec_scanlog | Parser for Symantec Anti-Virus log files.
syslog | Parser for syslog files.
utmp | Parser for Linux/Unix UTMP files.
utmpx | Parser for UTMPX files.
winevt | Parser for Windows EventLog (EVT) files.
winevtx | Parser for Windows XML EventLog (EVTX) files.
winfirewall | Parser for Windows Firewall Log files.
winiis | Parser for Microsoft IIS log files.
winjob | Parser for Windows Scheduled Task job (or At-job) files.
winreg | Parser for Windows NT Registry (REGF) files.
xchatlog | Parser for XChat log files.
xchatscrollback | Parser for XChat scrollback log files.

### Parser plugins: bencode

Name | Description
--- | ---
bencode_transmission | Parser for Transmission bencoded files.
bencode_utorrent | Parser for uTorrent bencoded files.

### Parser plugins: esedb

Name | Description
--- | ---
esedb_file_history | Parser for File History ESE database files.
msie_webcache | Parser for MSIE WebCache ESE database files.

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
macuser | Parser for Mac OS X user plist files.
maxos_software_update | Parser for Mac OS X software update plist files.
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
appusage | Parser for Mac OS X application usage SQLite database files.
chrome_cookies | Parser for Chrome cookies SQLite database files.
chrome_extension_activity | Parser for Chrome extension activity SQLite database files.
chrome_history | Parser for Chrome history SQLite database files.
firefox_cookies | Parser for Firefox cookies SQLite database files.
firefox_downloads | Parser for Firefox downloads SQLite database files.
firefox_history | Parser for Firefox history SQLite database files.
google_drive | Parser for Google Drive SQLite database files.
ls_quarantine | Parser for LS quarantine events SQLite database files.
mac_document_versions | Parser for document revisions SQLite database files.
mackeeper_cache | Parser for MacKeeper Cache SQLite database files.
skype | Parser for Skype SQLite database files.
zeitgeist | Parser for Zeitgeist activity SQLite database files.

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
msie_zone_software | Parser for Internet Explorer zone settings Registry data.
mstsc_rdp | Parser for Terminal Server Client Connection Registry data.
mstsc_rdp_mru | Parser for Terminal Server Client MRU Registry data.
userassist | Parser for User Assist Registry data.
windows_boot_execute | Parser for Boot Execution Registry data.
windows_boot_verify | Parser for Boot Verification Registry data.
windows_run | Parser for run and run once Registry data.
windows_run_software | Parser for run and run once Registry data.
windows_sam_users | Parser for SAM Users and Names Registry keys.
windows_services | Parser for services and drivers Registry data.
windows_shutdown | Parser for ShutdownTime Registry value.
windows_task_cache | Parser for Task Scheduler cache Registry data.
windows_timezone | Parser for Windows timezone settings.
windows_typed_urls | Parser for Explorer typed URLs Registry data.
windows_usb_devices | Parser for USB device Registry entries.
windows_usbstor_devices | Parser for USB Plug And Play Manager USBStor Registry Key.
windows_version | Parser for Windows version Registry data.
winrar_mru | Parser for WinRAR History Registry data.
winreg_default | Parser for Registry data.

### Parser presets

Name | Parsers and plugins
--- | ---
android | android_app_usage, android_calls, android_sms
linux | bencode, filestat, google_drive, java_idx, olecf, openxml, pls_recall, popularity_contest, selinux, skype, syslog, utmp, webhist, xchatlog, xchatscrollback, zeitgeist
macosx | appusage, asl_log, bencode, bsm_log, cups_ipp, filestat, google_drive, java_idx, ls_quarantine, mac_appfirewall_log, mac_document_versions, mac_keychain, mac_securityd, mackeeper_cache, macwifi, olecf, openxml, plist, skype, utmpx, webhist
macosx_slow | macosx, syslog
webhist | binary_cookies, chrome_cache, chrome_cookies, chrome_extension_activity, chrome_history, chrome_preferences, firefox_cache, firefox_cookies, firefox_downloads, firefox_history, java_idx, msie_webcache, msiecf, opera_global, opera_typed_history, safari_history
win7 | recycle_bin, custom_destinations, esedb_file_history, olecf_automatic_destinations, win_gen, winevtx
win7_slow | hachoir, win7
win_gen | bencode, esedb, filestat, google_drive, java_idx, lnk, mcafee_protection, olecf, openxml, pe, prefetch, skydrive_log_error, skydrive_log, skype, symantec_scanlog, webhist, winfirewall, winjob, winreg
winxp | recycle_bin_info2, win_gen, winevt
winxp_slow | hachoir, winxp


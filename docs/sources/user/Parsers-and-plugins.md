### Parsers

Name | Description
--- | ---
android_app_usage | Parser for Android usage history (usage-history.xml) files.
asl_log | Parser for Apple System Log (ASL) files.
bencode | Parser for Bencoded files.
binary_cookies | Parser for Safari Binary Cookie files.
bodyfile | Parser for SleuthKit version 3 bodyfile.
bsm_log | Parser for Basic Security Module (BSM) event auditing files.
chrome_cache | Parser for Google Chrome or Chromium Cache files.
chrome_preferences | Parser for Google Chrome Preferences files.
cups_ipp | Parser for CUPS IPP files.
custom_destinations | Parser for Custom destinations jump list (.customDestinations-ms) files.
czip | Parser for Compound ZIP files.
esedb | Parser for Extensible Storage Engine (ESE) Database File (EDB) format.
filestat | Parser for file system stat information.
firefox_cache | Parser for Mozilla Firefox Cache version 1 file (version 31 or earlier).
firefox_cache2 | Parser for Mozilla Firefox Cache version 2 file (version 32 or later).
fish_history | Parser for Fish history files.
fseventsd | Parser for MacOS File System Events Disk Log Stream (fseventsd) files.
java_idx | Parser for Java WebStart Cache IDX files.
jsonl | Parser for JSON-L log files.
lnk | Parser for Windows Shortcut (LNK) files.
locate_database | Parser for Locate database file (updatedb).
mac_keychain | Parser for MacOS keychain database files.
mcafee_protection | Parser for McAfee Anti-Virus access protection log files.
mft | Parser for NTFS $MFT metadata files.
msiecf | Parser for Microsoft Internet Explorer (MSIE) 4 - 9 cache (index.dat) files.
networkminer_fileinfo | Parser for NetworkMiner .fileinfos files.
olecf | Parser for OLE Compound File (OLECF) format.
onedrive_log | Parser for OneDrive Log files.
opera_global | Parser for Opera global history (global_history.dat) files.
opera_typed_history | Parser for Opera typed history (typed_history.xml) files.
pe | Parser for Portable Executable (PE) files.
plist | Parser for Property list (plist) files.
pls_recall | Parser for PL SQL cache file (PL-SQL developer recall file) format.
prefetch | Parser for Windows Prefetch File (PF).
recycle_bin | Parser for Windows $Recycle.Bin $I files.
recycle_bin_info2 | Parser for Windows Recycler INFO2 files.
rplog | Parser for Windows Restore Point log (rp.log) files.
simatic_s7 | Parser for SIMATIC S7 Log files.
spotlight_storedb | Parser for Apple Spotlight store database (store.db) files.
sqlite | Parser for SQLite database files.
symantec_scanlog | Parser for Symantec AV Corporate Edition and Endpoint Protection log files.
systemd_journal | Parser for Systemd journal files.
text | Parser for text-based log files.
trendmicro_url | Parser for Trend Micro Office Web Reputation log files.
trendmicro_vd | Parser for Trend Micro Office Scan Virus Detection log files.
unified_logging | Parser for Apple Unified Logging (AUL) 64-bit tracev3 files.
usnjrnl | Parser for NTFS USN change journal ($UsnJrnl:$J) file system metadata files.
utmp | Parser for Linux libc6 utmp files.
utmpx | Parser for Mac OS X 10.5 utmpx files.
wincc_sys | Parser for WinCC Sys Log files.
windefender_history | Parser for Windows Defender scan DetectionHistory files.
winevt | Parser for Windows EventLog (EVT) files.
winevtx | Parser for Windows XML EventLog (EVTX) files.
winjob | Parser for Windows Scheduled Task job (or at-job) files.
winpca_db0 | Parser for Windows PCA DB0 log files.
winpca_dic | Parser for Windows PCA DIC log files.
winreg | Parser for Windows NT Registry (REGF) files.

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
user_access_logging | Parser for Windows User Access Logging ESE database files.

### Parser plugins: jsonl

Name | Description
--- | ---
aws_cloudtrail_log | Parser for AWS CloudTrail Log.
azure_activity_log | Parser for Azure Activity Log.
azure_application_gateway_access_log | Parser for Azure Application Gateway access log.
docker_container_config | Parser for Docker container configuration files.
docker_container_log | Parser for Docker container log files.
docker_layer_config | Parser for Docker layer configuration files.
gcp_log | Parser for Google Cloud (GCP) log.
ios_application_privacy | Parser for iOS Application Privacy report.
microsoft_audit_log | Parser for Microsoft (Office) 365 audit log.

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
ios_carplay | Parser for Apple iOS Car Play application plist files.
ios_identityservices | Parser for Idstatuscache plist files.
ipod_device | Parser for iPod, iPad and iPhone plist files.
launchd_plist | Parser for Launchd plist files.
macos_bluetooth | Parser for MacOS Bluetooth plist files.
macos_software_update | Parser for MacOS software update plist files.
macosx_install_history | Parser for MacOS installation history plist files.
macuser | Parser for MacOS user plist files.
plist_default | Parser for plist files.
safari_downloads | Parser for Safari Downloads plist files.
safari_history | Parser for Safari history plist files.
spotlight | Parser for Spotlight searched terms plist files.
spotlight_volume | Parser for Spotlight volume configuration plist files.
time_machine | Parser for MacOS TimeMachine plist files.

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
dropbox | Parser for Dropbox sync history database (sync_history.db) files.
firefox_10_cookies | Parser for Mozilla Firefox cookies SQLite database file version 10.
firefox_2_cookies | Parser for Mozilla Firefox cookies SQLite database file version 2.
firefox_downloads | Parser for Mozilla Firefox downloads SQLite database (downloads.sqlite) files.
firefox_history | Parser for Mozilla Firefox history SQLite database (places.sqlite) files.
google_drive | Parser for Google Drive snapshot SQLite database (snapshot.db) files.
hangouts_messages | Parser for Google Hangouts conversations SQLite database (babel.db) files.
imessage | Parser for MacOS and iOS iMessage database (chat.db, sms.db) files.
ios_datausage | Parser for iOS data usage SQLite databse (DataUsage.sqlite) file..
ios_netusage | Parser for iOS network usage SQLite database (netusage.sqlite) files.
ios_powerlog | Parser for iOS powerlog SQLite database (CurrentPowerlog.PLSQL) files.
ios_screentime | Parser for iOS Screen Time SQLite database (RMAdminStore-Local.sqlite).
kik_ios | Parser for iOS Kik messenger SQLite database (kik.sqlite) files.
kodi | Parser for Kodi videos SQLite database (MyVideos.db) files.
ls_quarantine | Parser for MacOS launch services quarantine events database SQLite database files.
mac_document_versions | Parser for MacOS document revisions SQLite database files.
mac_knowledgec | Parser for MacOS Duet/KnowledgeC SQLites database files.
mac_notes | Parser for MacOS Notes SQLite database (NotesV7.storedata) files.
mac_notificationcenter | Parser for MacOS Notification Center SQLite database files.
mackeeper_cache | Parser for MacOS MacKeeper cache SQLite database files.
macostcc | Parser for MacOS Transparency, Consent, Control (TCC) SQLite database (TCC.db) files.
safari_historydb | Parser for Safari history SQLite database (History.db) files.
skype | Parser for Skype SQLite database (main.db) files.
tango_android_profile | Parser for Tango on Android profile SQLite database files.
tango_android_tc | Parser for Tango on Android TC SQLite database files.
twitter_android | Parser for Twitter on Android SQLite database files.
twitter_ios | Parser for Twitter on iOS 8 and later SQLite database (twitter.db) files.
windows_eventtranscript | Parser for Windows diagnosis EventTranscript SQLite database (EventTranscript.db) files.
windows_timeline | Parser for Windows 10 Timeline SQLite database (ActivitiesCache.db) files.
zeitgeist | Parser for Zeitgeist activity SQLite database files.

### Parser plugins: text

Name | Description
--- | ---
android_logcat | Parser for Android logcat files.
apache_access | Parser for Apache access log (access.log) files.
apt_history | Parser for Advanced Packaging Tool (APT) History log files.
aws_elb_access | Parser for AWS ELB Access log files.
bash_history | Parser for Bash history files.
confluence_access | Parser for Confluence access log (access.log) files.
dpkg | Parser for Debian package manager log (dpkg.log) files.
gdrive_synclog | Parser for Google Drive Sync log files.
googlelog | Parser for Google-formatted log files.
ios_lockdownd | Parser for iOS lockdown daemon log.
ios_logd | Parser for iOS sysdiagnose logd files.
ios_sysdiag_log | Parser for iOS sysdiag log.
mac_appfirewall_log | Parser for MacOS Application firewall log (appfirewall.log) files.
mac_securityd | Parser for MacOS security daemon (securityd) log files.
mac_wifi | Parser for MacOS Wi-Fi log (wifi.log) files.
popularity_contest | Parser for Popularity Contest log files.
postgresql | Parser for PostgreSQL application log files.
powershell_transcript | Parser for PowerShell transcript event.
santa | Parser for Santa log (santa.log) files.
sccm | Parser for System Center Configuration Manager (SCCM) client log files.
selinux | Parser for SELinux audit log (audit.log) files.
setupapi | Parser for Windows SetupAPI log files.
skydrive_log_v1 | Parser for OneDrive (or SkyDrive) version 1 log files.
skydrive_log_v2 | Parser for OneDrive (or SkyDrive) version 2 log files.
snort_fastlog | Parser for Snort3/Suricata fast-log alert log (fast.log) files.
sophos_av | Parser for Sophos anti-virus log file (SAV.txt) files.
syslog | Parser for System log (syslog) files.
syslog_traditional | Parser for Traditional system log (syslog) files.
viminfo | Parser for Viminfo files.
vsftpd | Parser for vsftpd log files.
winfirewall | Parser for Windows Firewall log files.
winiis | Parser for Microsoft IIS log files.
xchatlog | Parser for XChat log files.
xchatscrollback | Parser for XChat scrollback log files.
zsh_extended_history | Parser for ZSH extended history files.

### Parser plugins: winreg

Name | Description
--- | ---
amcache | Parser for AMCache (AMCache.hve).
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
ios | jsonl/ios_application_privacy, plist/ios_identityservices, sqlite/imessage, sqlite/ios_netusage, sqlite/ios_powerlog, sqlite/ios_screentime, sqlite/kik_ios, sqlite/twitter_ios, text/ios_lockdownd, text/ios_logd, text/ios_sysdiag_log
linux | bencode, czip/oxml, jsonl/docker_container_config, jsonl/docker_container_log, jsonl/docker_layer_config, filestat, olecf, pls_recall, sqlite/google_drive, sqlite/skype, sqlite/zeitgeist, systemd_journal, text/apt_history, text/bash_history, text/dpkg, text/gdrive_synclog, text/googlelog, text/popularity_contest, text/selinux, text/syslog, text/syslog_traditional, text/vsftpd, text/xchatlog, text/xchatscrollback, text/zsh_extended_history, utmp, webhist
macos | asl_log, bencode, bsm_log, cups_ipp, czip/oxml, filestat, fseventsd, mac_keychain, olecf, plist, spotlight_storedb, sqlite/appusage, sqlite/google_drive, sqlite/imessage, sqlite/ls_quarantine, sqlite/mac_document_versions, sqlite/mac_notes, sqlite/mackeeper_cache, sqlite/mac_knowledgec, sqlite/skype, text/bash_history, text/gdrive_synclog, text/mac_appfirewall_log, text/mac_securityd, text/mac_wifi, text/syslog, text/syslog_traditional, text/zsh_extended_history, utmpx, webhist
mactime | bodyfile
webhist | binary_cookies, chrome_cache, chrome_preferences, esedb/msie_webcache, firefox_cache, java_idx, msiecf, opera_global, opera_typed_history, plist/safari_history, sqlite/chrome_8_history, sqlite/chrome_17_cookies, sqlite/chrome_27_history, sqlite/chrome_66_cookies, sqlite/chrome_autofill, sqlite/chrome_extension_activity, sqlite/firefox_2_cookies, sqlite/firefox_10_cookies, sqlite/firefox_downloads, sqlite/firefox_history, sqlite/safari_historydb
win7 | custom_destinations, esedb/file_history, esedb/user_access_logging, olecf/olecf_automatic_destinations, recycle_bin, text/powershell_transcript, winevtx, win_gen, winpca_db0, winpca_dic
win7_slow | esedb, mft, win7
win_gen | bencode, czip/oxml, filestat, lnk, mcafee_protection, olecf, pe, prefetch, sqlite/google_drive, sqlite/skype, symantec_scanlog, text/gdrive_synclog, text/sccm, text/setupapi, text/skydrive_log_v1, text/skydrive_log_v2, text/winfirewall, usnjrnl, webhist, winjob, winreg
winxp | recycle_bin_info2, rplog, win_gen, winevt
winxp_slow | esedb, mft, winxp


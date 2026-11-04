# Tagging Rules

Plaso provides various configuration files for the [tagging analysis plugin](Analysis-plugin-tagging.md).

## Linux tagging rules

The Linux tagging rules are stored in the file: [tag_linux.txt](https://github.com/log2timeline/plaso/blob/main/plaso/data/tag_linux.txt)

The sections below provide more context regarding specific tagging rules.

### application_execution

This rule tags application execution events on Linux, which are defined as:

* a command from bash history
* a Docker file system layer event
* a command from fish history
* a SELinux log line where the audit type is "EXECVE" or "USER_CMD"
* a command from zsh history
* a syslog line that indicates a cron task was run, for example:
```
Mar 11 00:00:00 ubuntu2015 CRON[3]: (root) CMD (touch /tmp/afile.txt)
```

* a syslog line from sudo that contains "COMMAND="
* a syslog line from CROND that contains "CMD"

### login

This rule tags log-in events on Linux, which are defined as:

* a utmp event with login type 7 (a user process)
* a SELinux log line where the audit type is "LOGIN"
* a SELinux log line where the audit type is "USER_LOGIN" and the operation result is success ("res=success"), for example:
```
type=USER_LOGIN msg=audit(1789331920.280:298): pid=1611 uid=0 auid=0 ses=7 subj=system_u:system_r:sshd_session_t:s0-s0:c0.c1023 msg='op=login id=0 exe="/usr/libexec/openssh/sshd-session" hostname=? addr=192.168.1.13 terminal=ssh res=success'
```

* a syslog line from login that contains "logged in", "ROOT LOGIN" or "session opened"
* a syslog line from sshd or sshd-session that contains "session opened" or "Starting session", for example:
```
2026-09-13T20:58:32.613518+00:00 ubuntu-26-parsers sshd-session[18413]: pam_unix(sshd:session): session opened for user ubuntu(uid=1000) by ubuntu(uid=0)
```

* a syslog line from sshd or sshd-session that indicates a successful authentication, for example:
```
2026-09-13T20:58:32.606882+00:00 ubuntu-26-parsers sshd-session[18413]: Accepted password for ubuntu from 192.168.1.13 port 61364 ssh2
```

* a syslog line from dovecot that contains "imap-login: Login:"
* a syslog line from postfix/submission/smtpd that contains "sasl_"
* a vsftpd log line that contains "OK LOGIN", for example:
```
Sun Sep 13 21:38:56 2026 [pid 42321] [john.doe] OK LOGIN: Client "::ffff:127.0.0.1"
```

### login_failed

This rule tags failed log-in events on Linux, which are defined as:

* a SELinux log line where the audit type is "ANOM_LOGIN_FAILURES"
* a SELinux log line where the audit type is "USER_LOGIN" and the operation result is failed ("res=failed")
* a SELinux log line where the audit type is "USER_AUTH" and the operation result is failed ("res=failed"), for example:
```
type=USER_AUTH msg=audit(1789331921.882:317): pid=1681 uid=1001 auid=0 ses=7 subj=unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023 msg='op=PAM:authentication grantors=? acct="root" exe="/usr/bin/su" hostname=localhost.localdomain addr=? terminal=/dev/pts/0 res=failed'
```

* a syslog line that contains "pam_tally2"
* a syslog line from sshd, sshd-session, login, postfix/submission/smtpd or sudo that contains "uthentication fail", which matches both "authentication failure" and "Authentication failed"
* a syslog line from sshd or sshd-session that contains "Access denied for user" or "not allowed because"
* a syslog line from sshd or sshd-session that indicates a failed authentication, for example:
```
2026-09-13T21:02:45.907303+00:00 ubuntu-26-parsers sshd-session[21146]: Failed password for john.doe from 192.168.1.138 port 39144 ssh2
```

* a syslog line from sshd or sshd-session that records an authentication request for a user name that does not exist, for example:
```
2026-10-08T00:19:26.539626+00:00 ubuntu sshd-session[3824]: Invalid user john doe from 192.168.248.1 port 54928
```

* a syslog line from xscreensaver or login that contains "FAILED LOGIN"
* a syslog line from su that contains "DENIED"
* a syslog line from su that contains "FAILED SU", for example:
```
Sep 13 15:38:44 localhost su[1681]: FAILED SU (to root) john.doe on pts/0
```

* a syslog line from nologin
* a vsftpd log line that contains "FAIL LOGIN", for example:
```
Sun Sep 13 21:38:48 2026 [pid 42238] [john.doe] FAIL LOGIN: Client "::ffff:127.0.0.1"
```

### useradd

This rule tags user account creation events on Linux, which are defined as:

* a syslog line from useradd that contains "new user"
* a SELinux log line where the audit type is "ADD_USER"

### groupadd

This rule tags group creation events on Linux, which are defined as:

* a syslog line from useradd that contains "new group"
* a syslog line from groupadd
* a SELinux log line where the audit type is "ADD_GROUP"

### userdel

This rule tags user account removal events on Linux, which are defined as:

* a syslog line from userdel that contains "delete user"
* a SELinux log line where the audit type is "DEL_USER"

### groupdel

This rule tags group removal events on Linux, which are defined as:

* a syslog line from userdel that contains "removed group"
* a syslog line from groupdel
* a SELinux log line where the audit type is "DEL_GROUP"

### firewall_change

This rule tags netfilter (firewall) configuration change events on Linux, which are defined as:

* a SELinux log line where the audit type is "NETFILTER_CFG"

### logout

This rule tags log-out events on Linux, which are defined as:

* a utmp event of type DEAD_PROCESS (8) with a terminal and a process identifier, which also matches the gettys that init stops during a shutdown or reboot
* a syslog line from login that contains "session closed"
* a syslog line from sshd or sshd-session that contains "session closed" or "Close session"
* a syslog line from systemd-logind that contains "logged out"
* a syslog line from dovecot that contains "Logged out"
* a SELinux log line where the audit type is "USER_LOGOUT"
* a syslog line from sshd or sshd-session that records the end of a connection of an authenticated user, for example:
```
2026-10-08T00:19:28.778673+00:00 ubuntu sshd-session[3884]: Disconnected from user ubuntu fe80::621:e520:10d6:6621%ens36 port 54931
```

### session_start

This rule tags user session start events on Linux, which are defined as:

* a syslog line from systemd-logind that contains "New session", for example:
```
2026-09-13T20:58:32.623329+00:00 ubuntu-26-parsers systemd-logind[1697]: New session '3' of user 'ubuntu' with class 'user' and type 'tty'.
```

* a SELinux log line where the audit type is "USER_START"

### session_stop

This rule tags user session stop events on Linux, which are defined as:

* a syslog line from systemd-logind that contains "Removed session", for example:
```
2026-09-13T20:58:33.933089+00:00 ubuntu-26-parsers systemd-logind[1697]: Removed session 3.
```

* a SELinux log line where the audit type is "USER_END"

### boot

This rule tags system boot events on Linux, which are defined as:

* a utmp event with login type 2 (a boot time), a terminal of "system boot" and the user name "reboot"
* a SELinux log line where the audit type is "SYSTEM_BOOT"

### shutdown

This rule tags system shutdown events on Linux, which are defined as:

* a utmp event with login type 1 (a run level change), a terminal of "~~" or "system boot" and the user name "shutdown"
* a SELinux log line where the audit type is "SYSTEM_SHUTDOWN"
* a syslog line from systemd-logind that contains "System is powering down", "System is rebooting" or "System is halting", for example:
```
Sep 13 16:39:16 localhost systemd-logind[1117]: System is rebooting.
```

### runlevel

This rule tags system run level change events on Linux, which are defined as:

* a utmp event with login type 1 (a run level change) and the user name "runlevel"
* a SELinux log line where the audit type is "SYSTEM_RUNLEVEL"

### device_connection

This rule tags device connection events on Linux, which are defined as:

* a syslog line from kernel that contains "New USB device found"

### device_disconnection

This rule tags device disconnection events on Linux, which are defined as:

* a syslog line from kernel that contains "USB disconnect"

### application_install

This rule tags application installation events on Linux, which are defined as:

* a dpkg log line that contains "status installed"
* an APT history log entry where the command is "Install", for example:
```
Commandline: apt-get install -y -q vsftpd
Requested-By: ubuntu (1000)
Install: ssl-cert:amd64 (1.1.3ubuntu2, automatic), vsftpd:amd64 (3.0.5-0.4)
```

### service_start

This rule tags service start events on Linux, which are defined as:

* a SELinux log line where the audit type is "SERVICE_START"

### service_stop

This rule tags service stop events on Linux, which are defined as:

* a SELinux log line where the audit type is "SERVICE_STOP"

### promiscuous

This rule tags network interface promiscuous mode change events on Linux, which are defined as:

* a SELinux log line where the audit type is "ANOM_PROMISCUOUS"
* a syslog line from kernel that contains "promiscuous mode"

### crash

This rule tags crash events on Linux, which are defined as:

* a SELinux log line where the audit type is "ANOM_ABEND"
* a syslog line from kernel that contains "segfault"

## MacOS tagging rules

The MacOS tagging rules are stored in the file: [tag_macos.txt](https://github.com/log2timeline/plaso/blob/main/plaso/data/tag_macos.txt)

The sections below provide more context regarding specific tagging rules.

### application_execution

This rule tags application execution events on MacOS, which are defined as:

* a MacOS application usage database entry
* a syslog line that contains "COMMAND=/bin/launchctl"

### application_install

This rule tags application installation events on MacOS, which are defined as:

* a plist key event of the "plist_install_history" plugin

### autorun

This rule tags auto run events on MacOS, which are defined as:

* a file system creation time event of a file with "LaunchAgents" as a path segment and a filename that contains ".plist"

### file_download

This rule tags file download events on MacOS, which are defined as:

* a Chrome history file downloaded event
* a MacOS launch services quarantine event
* an event with the timestamp description "Downloaded Time"

### device_connection

This rule tags device connection events on MacOS, which are defined as:

* an iPod device entry
* a plist key event of the "plist_airport" plugin

### document_print

This rule tags document print events on MacOS, which are defined as:

* an OLE compound file summary information last printed time event

## Windows tagging rules

The Windows tagging rules are stored in the file: [tag_windows.txt](https://github.com/log2timeline/plaso/blob/main/plaso/data/tag_windows.txt)

The sections below provide more context regarding specific tagging rules.

### application_execution

This rule tags application execution events on Windows, which are defined as:

* a file system event of a file with "Windows/Tasks/At" as path segments
* a Windows EventLog (EVT) record of source Security with event identifier 592
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Security-Auditing with event identifier 4688
* a Windows XML EventLog (EVTX) record with the strings "user mode service" and "demand start"
* a Windows Shortcut (LNK) file with a filename that contains "Recent" and of which the local, network or relative path contains ".exe"
* a Windows Prefetch execution event
* a Windows Application Compatibility Cache Registry entry
* a Windows MRUList or MRUListEx Registry entry that contains ".exe"
* a Windows UserAssist Registry value of which the name contains ".exe"
* a Windows Scheduled Task job

### application_install

This rule tags application installation events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Application-Experience with event identifier 903 or 904

### application_update

This rule tags application update events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Application-Experience with event identifier 905

### application_removal

This rule tags application removal events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Application-Experience with event identifier 907 or 908

### document_open

This rule tags document open events on Windows, which are defined as:

* a Windows BagMRU (or ShellBags) Registry entry
* a Windows MRUList or MRUListEx Registry entry that does not contain ".exe" and has a timestamp later than the POSIX epoch
* a Microsoft Office MRU Registry entry

### login_failed

This rule tags failed log-in events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Security-Auditing with event identifier 4625

### login_attempt

This rule tags log-in attempt events on Windows, which are defined as:

* a Windows EventLog (EVT) record of source Security with event identifier 540
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Security-Auditing with event identifier 4624
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-TerminalServices-LocalSessionManager with event identifier 21 or 1101
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-TerminalServices-RemoteConnectionManager with event identifier 1147 or 1149
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-User Profiles Service with event identifier 2
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Winlogon with event identifier 7001

### logoff

This rule tags log-off events on Windows, which are defined as:

* a Windows EventLog (EVT) record of source Security with event identifier 538
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Security-Auditing with event identifier 4634
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-TerminalServices-LocalSessionManager with event identifier 23 or 1103
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-User Profiles Service with event identifier 4
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Winlogon with event identifier 7002

### session_disconnection

This rule tags Terminal Services session disconnection events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-TerminalServices-LocalSessionManager with event identifier 24

### session_reconnection

This rule tags Terminal Services session reconnection events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-TerminalServices-LocalSessionManager with event identifier 25 or 1105

### shell_start

This rule tags Terminal Services shell start events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-TerminalServices-LocalSessionManager with event identifier 22 or 1102

### task_schedule

This rule tags scheduled task creation events on Windows, which are defined as:

* a Windows EventLog (EVT) record of source Security with event identifier 602
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Security-Auditing with event identifier 4698

### job_success

This rule tags Task Scheduler successfully completed job events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-TaskScheduler with event identifier 102

### action_success

This rule tags Task Scheduler successfully completed action events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-TaskScheduler with event identifier 201

### name_resolution_timeout

This rule tags DNS name resolution timeout events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-DNS-Client with event identifier 1014

### time_change

This rule tags system time change events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Kernel-General with event identifier 1

### shutdown

This rule tags system shutdown events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Kernel-General with event identifier 13

### system_start

This rule tags system start events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Kernel-General with event identifier 12

### system_sleep

This rule tags system sleep events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Kernel-Power with event identifier 42

### autorun

This rule tags auto run events on Windows, which are defined as:

* a Windows Boot Execute Registry value that contains ".exe" or ".dll"
* a Windows boot verification Registry value of which the image path contains ".exe" or ".dll"
* a Windows Run or RunOnce Registry entry that contains ".exe" or ".dll"

### file_download

This rule tags file download events on Windows, which are defined as:

* a Chrome history file downloaded event
* an event with the timestamp description "Downloaded Time"

### document_print

This rule tags document print events on Windows, which are defined as:

* an OLE compound file summary information last printed time event

### firewall_change

This rule tags Windows Firewall With Advanced Security change events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Windows Firewall With Advanced Security with event identifier 2003, 2004, 2005 or 2006

### system_wake

This rule tags system wake events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Power-Troubleshooter, or provider identifier {cdc05e28-c449-49c6-b9d2-88cf761644df}, with event identifier 1

### registry_modified

This rule tags Windows Registry modification events, which are defined as:

* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Security-Auditing with event identifier 4657, which indicates a registry value was modified

### service_new

This rule tags service creation events on Windows, which are defined as:

* a Windows XML EventLog (EVTX) record of source Service Control Manager with event identifier 7045, which indicates a new service was installed

### eventlog_cleared

This rule tags event log cleared events on Windows, which are defined as:

* a Windows EventLog (EVT) record of source Security with event identifier 517
* a Windows XML EventLog (EVTX) record of source Microsoft-Windows-Eventlog with event identifier 104 or 1102

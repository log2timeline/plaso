# Tagging Rules

Plaso provides various configuration files for the [tagging analysis plugin](Analysis-plugin-tagging.md).

## Linux tagging rules

The Linux tagging rules are stored in the file: [tag_linux.txt](https://github.com/log2timeline/plaso/blob/main/plaso/data/tag_linux.txt)

The sections below provide more context regarding specific tagging rules.

### application_execution

This rule tags application execution events on Linux, which are defined as:

* a command from bash history
* a Docker file system layer event
* a SELinux log line where the audit type is "EXECVE"
* a command from zsh history
* a syslog line that indicates a cron task was run, for example:
```
Mar 11 00:00:00 ubuntu2015 CRON[3]: (root) CMD (touch /tmp/afile.txt)
```

* a syslog line that contains "COMMAND="

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

### logout

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

### shutdown

This rule tags system shutdown events on Linux, which are defined as:

* a utmp event with login type 1 (a run level change), a terminal of "~~" or "system boot" and the user name "shutdown"
* a SELinux log line where the audit type is "SYSTEM_SHUTDOWN"
* a syslog line from systemd-logind that contains "System is powering down", "System is rebooting" or "System is halting", for example:
```
Sep 13 16:39:16 localhost systemd-logind[1117]: System is rebooting.
```

### runlevel

### device_connection

### device_disconnection

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

### service_stop

### promiscuous

### crash

## MacOS tagging rules

The MacOS tagging rules are stored in the file: [tag_macos.txt](https://github.com/log2timeline/plaso/blob/main/plaso/data/tag_macos.txt)

The sections below provide more context regarding specific tagging rules.

### application_execution

### application_install

### autorun

### file_download

### device_connection

### document_print

## Windows tagging rules

The Windows tagging rules are stored in the file: [tag_windows.txt](https://github.com/log2timeline/plaso/blob/main/plaso/data/tag_windows.txt)

The sections below provide more context regarding specific tagging rules.

### application_execution

### application_install

### application_update

### application_removal

### document_open

### login_failed

### login_attempt

### logoff

### session_disconnection

### session_reconnection

### shell_start

### task_schedule

### job_success

### action_success

### name_resolution_timeout

### time_change

### shutdown

### system_start

### system_sleep

### autorun

### file_download

### document_print

### firewall_change


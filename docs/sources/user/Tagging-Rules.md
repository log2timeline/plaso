# Tagging Rules

Plaso provides various configuration files for the [tagging analysis plugin](Analysis-plugin-tagging.md).

## Linux tagging rules

The Linux tagging rules are stored in the file: [tag_linux.txt](https://github.com/log2timeline/plaso/blob/main/data/tag_linux.txt)

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

### login_failed

### logout

### session_start

### session_stop

### boot

### shutdown

### runlevel

### device_connection

### device_disconnection

### application_install

### service_start

### service_stop

### promiscuous

### crash

## MacOS tagging rules

The MacOS tagging rules are stored in the file: [tag_macos.txt](https://github.com/log2timeline/plaso/blob/main/data/tag_macos.txt)

The sections below provide more context regarding specific tagging rules.

### application_execution

### application_install

### autorun

### file_download

### device_connection

### document_print

## Windows tagging rules

The Windows tagging rules are stored in the file: [tag_windows.txt](https://github.com/log2timeline/plaso/blob/main/data/tag_windows.txt)

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

